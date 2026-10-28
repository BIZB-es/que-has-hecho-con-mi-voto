#!/usr/bin/env python3
"""Audit voting-to-file links against saved Congress session HTML.

Exact vote JSON URL, individual yes/no/abstentions, and an expediente link
within the DOM accordion that owns that specific vote are REQUIRED.
Supports joint votes with multiple expediente links. Never inherits the last
expediente from a different vote or a sibling accordion.

Run from any directory:
  python scripts/cotejar_html_sesiones_v082.py --fuentes fuentes_sesiones_XV.zip \
      --propuestas expedientes_propuestos_v08.csv
"""
import argparse, csv, hashlib, io, json, re, sys, zipfile
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent.parent
REGEX_JSON=re.compile(r'/Votacion\d+/[^"<>]+\.json(?:$|\?)',re.I)
R_EXP=re.compile(r'\b(\d{3}/\d{6})\b')
EXPS='https://www.congreso.es/es/busqueda-de-iniciativas?p_p_id=iniciativas&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_iniciativas_mode=mostrarDetalle&_iniciativas_legislatura=XV&_iniciativas_id='

def read_csv(path):
 with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))

def write_csv(path,rows,fields):
 with open(path,'w',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=fields,delimiter=';',extrasaction='ignore');writer.writeheader();writer.writerows(rows)

def official_url(code):return EXPS+quote(code,safe='')

def session_url(day):return ('https://www.congreso.es/es/opendata/votaciones?targetLegislatura=XV&targetDate='+day[8:10]+'%2F'+day[5:7]+'%2F'+day[:4])

def parse_votations(html,day,sha):
 soup=BeautifulSoup(html,'lxml')
 result=[];seen=set()
 for a in soup.find_all('a',href=REGEX_JSON):
  vote_url=urljoin('https://www.congreso.es',a.get('href','')).split('?')[0].lower()
  if vote_url in seen:raise ValueError('Duplicate JSON link '+vote_url)
  seen.add(vote_url)
  # Avoid extracting a count from some other vote in the accordion.
  div=a.find_parent('div',class_='result_vot')
  if div is None:raise ValueError('No result-vot block for '+vote_url)
  tally={}
  for p in div.find_all('p',recursive=False):
   s=p.get_text(' ',strip=True)
   for key,pattern in [('si',r'^S[i\u00ed]\s*:\s*(\d+)'),('no',r'^No\s*:\s*(\d+)'),('abstencion',r'^Abstenciones?\s*:\s*(\d+)')]:
    m=re.search(pattern,s,re.I)
    if m:tally[key]=int(m.group(1))
  # Walk the voting accordion ancestry. The first ancestor with expediente
  # links attached to its own heading is the actual legislative item.
  codes=[];accord_id=''
  for node in a.parents:
   if node.name=='div' and 'accord' in node.get('class',[]):
    links=node.find_all('a',class_='n_exp',recursive=False)
    heading=node.find('div',id=re.compile(r'^heading'),recursive=False)
    if heading:links+=heading.find_all('a',class_='n_exp')
    for link in links:
     text=link.get_text(' ',strip=True);m=R_EXP.search(text)
     if not m:m=R_EXP.search(link.get('href',''))
     if m and m.group(1) not in codes:codes.append(m.group(1))
    if codes:accord_id=node.get('id','');break
   if node.name=='div' and 'cuerpo-votaciones' in node.get('class',[]):break
  result.append({'url':vote_url,'counts':tally,'expedientes':codes,'accordion':accord_id,'fecha':day,'archivo':day+'.html','sha256':sha})
 return result

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--fuentes',type=Path,required=True)
 p.add_argument('--propuestas',type=Path,required=True)
 p.add_argument('--salida',type=Path,default=ROOT)
 a=p.parse_args();out=a.salida
 datos=out/'datos';assets=out/'assets';datos.mkdir(parents=True,exist_ok=True)
 originals=read_csv(datos/'vinculos_XV.csv')
 refs={x['url_votacion'].strip().lower():x for x in read_csv(datos/'votaciones_referencia_XV.csv')}
 proposals={x['url_votacion'].strip().lower():x for x in read_csv(a.propuestas)}
 byurl={};manifest=[];seen_dates=set()
 with zipfile.ZipFile(a.fuentes) as z:
  manifest=list(csv.DictReader(io.TextIOWrapper(z.open('manifest.csv'),encoding='utf-8-sig'),delimiter=';'))
  if len(manifest)!=139:raise ValueError('Manifest size unexpectedly differs: '+str(len(manifest)))
  for item in manifest:
   day=item['fecha'];fn=item['archivo']
   if not re.fullmatch(r'\d{4}-\d{2}-\d{2}\.html',fn) or fn!=day+'.html':raise ValueError('Unsafe or incorrect archive entry '+fn)
   if day in seen_dates:raise ValueError('Repeated date in manifest '+day)
   seen_dates.add(day)
   data=z.read(fn)
   if len(data)!=int(item['bytes']) or hashlib.sha256(data).hexdigest().lower()!=item['sha256'].lower():raise ValueError('SHA256/bytes mismatch '+fn)
   for row in parse_votations(data.decode('utf-8',errors='replace'),day,item['sha256']):
    if row['url'] in byurl:raise ValueError('Duplicate vote across pages '+row['url'])
    original=refs.get(row['url'])
    if not original:raise ValueError('JSON link is not in original reference CSV '+row['url'])
    if row['fecha']!=original['fecha']:raise ValueError('Incorrect source date '+row['url'])
    if any(row['counts'].get(k)!=int(original[k]) for k in ('si','no','abstencion')):raise ValueError('Tally mismatch '+row['url'])
    if not row['expedientes']:raise ValueError('No direct expediente for vote '+row['url'])
    byurl[row['url']]=row
 ids={x['votacion_id'] for x in originals}
 assert len(originals)==len(ids)==2177
 existing={x['url_votacion'].strip().lower():x for x in originals if x['url_votacion']}
 assert len(refs)==2175
 if len(byurl)!=2134:raise ValueError('Expected 2134 source votes; got '+str(len(byurl)))
 outrows=[];relations=[];audit_cases=[];stats=Counter();found=set()
 for old in originals:
  url=old['url_votacion'].strip().lower(); id=old['votacion_id'];row=byurl.get(url)
  if row:
   codes=row['expedientes'];status='MULTIPLE_HTML' if len(codes)>1 else 'UNICO_HTML'
   prev=old['expediente_id'].strip()
   if prev and not set(prev.split(' | ')).issubset(set(codes)):raise ValueError('Preexisting reviewed link conflicts with HTML: '+id+' '+prev+' vs '+str(codes))
   proposal=proposals.get(url,{}).get('expediente_candidato','')
   if proposal and proposal not in codes:stats['propuestas_anteriores_corregidas']+=1;audit_cases.append({'votacion_id':id,'anterior':proposal,'correctos':codes,'motivo':'El enlace al expediente figura en el mismo bloque HTML del voto, no se hereda de otra votacion'})
   elif proposal and len(codes)>1:stats['propuestas_anteriores_incompletas']+=1
   provenance='HTML guardado de sesion del Congreso; URL JSON, recuentos y bloque de expediente cotejados; SHA-256 '+row['sha256']
   srcfile=row['archivo']; sha=row['sha256']; node=row['accordion']
   found.add(url)
  else:
   # These 43 are previously individually reviewed, not present in 139 pages.
   if not old['expediente_id']:raise ValueError('Unlinked vote outside source ZIP: '+id)
   codes=[old['expediente_id']];status='COTEJO_ANTERIOR';provenance=old['metodo_vinculacion']
   srcfile='';sha='';node=''
  stats[status]+=1
  new=dict(old)
  new['expediente_id']=' | '.join(codes)
  new['url_expediente']=official_url(codes[0]) if len(codes)==1 else ''
  new['metodo_vinculacion']=provenance
  new['estado_expediente']=status
  new['numero_expedientes']=len(codes)
  new['url_sesion']=session_url(old['fecha'])
  new['fuente_html']=srcfile
  new['sha256_html']=sha
  new['acordeon_html']=node
  outrows.append(new)
  for code in codes:
   relations.append({'votacion_id':id,'fecha':old['fecha'],'expediente_id':code,'url_expediente':official_url(code),'estado':status,
    'url_votacion':old['url_votacion'],'url_sesion':session_url(old['fecha']),'fuente_html':srcfile,'sha256_html':sha,'acordeon_html':node,'metodo':provenance})
 # Integrity: every originally received voting item now has a matched official link.
 assert len(outrows)==2177 and len(relations)>=2177
 assert len(set(x['votacion_id'] for x in outrows))==2177
 assert not (set(byurl)-set(existing))
 assert sum(1 for x in outrows if x['estado_expediente']=='MULTIPLE_HTML')==15
 assert stats['propuestas_anteriores_corregidas']==8
 assert len([x for x in outrows if x['estado_expediente']=='COTEJO_ANTERIOR'])==43
 link_fields=list(outrows[0])
 write_csv(datos/'vinculos_XV.csv',outrows,link_fields)
 write_csv(datos/'relaciones_votacion_expediente_XV.csv',relations,list(relations[0]))
 write_csv(datos/'expedientes_enlazados_XV.csv',[
  {'votacion_id':x['votacion_id'],'fecha':x['fecha'],'titulo':x['titulo'],'expediente':x['expediente_id'],
   'fuente':x['metodo_vinculacion'],'url_sesion':x['url_sesion'],'estado':x['estado_expediente']} for x in outrows],
  ['votacion_id','fecha','titulo','expediente','fuente','url_sesion','estado'])
 write_csv(datos/'expedientes_pendientes_XV.csv',[],['votacion_id','fecha','titulo','url_votacion','observaciones'])
 # Stop presenting the old candidates as unverified; preserve only a legacy audit copy.
 oldnotes=datos/'expedientes_propuestos_anotados_XV.csv'
 if oldnotes.exists():oldnotes.rename(datos/'historico'/'expedientes_propuestos_v081.csv')
 annotated=[]
 for url,p in proposals.items():
  main=existing[url];nr=next(r for r in outrows if r['votacion_id']==main['votacion_id'])
  real_codes=nr['expediente_id'].split(' | ')
  status=('CORREGIDO' if p['expediente_candidato'] not in real_codes else
          'INCOMPLETO_MULTI' if len(real_codes)>1 else 'VERIFICADO_HTML')
  annotated.append({'votacion_id':main['votacion_id'],'fecha':main['fecha'],'candidato_v081':p['expediente_candidato'],
                    'expedientes_v082':nr['expediente_id'],'estado':status,'url_sesion':nr['url_sesion'],'fuente_html':nr['fuente_html'],'sha256_html':nr['sha256_html']})
 write_csv(oldnotes,annotated,list(annotated[0]))
 (assets/'propuestas_XV.js').write_text('window.QHV_PROPUESTAS_EXP_XV={};\n',encoding='utf-8')
 # Update the precached JSON and annual offline packages, without touching votes or totals.
 prepath=assets/'precarga_XV.js'; prefix='window.QHV_PRECARGA_XV='
 js=prepath.read_text(encoding='utf-8'); assert js.startswith(prefix)
 preload=json.loads(js[len(prefix):].strip().rstrip(';'))
 byid={r['votacion_id']:r for r in outrows}
 def update_vote(v):
  row=byid.get(v['id']);
  if not row:raise ValueError('Missing vote from preloaded data: '+v['id'])
  codes=row['expediente_id'].split(' | ')
  v['expediente']=codes[0] if len(codes)==1 else ', '.join(codes)
  v['expedientes']=codes
  v['expedientes_urls']=[official_url(code) for code in codes]
  v['url_expediente']=official_url(codes[0]) if len(codes)==1 else ''
  v['expediente_fuente']=row['metodo_vinculacion']
  v['expediente_estado']=row['estado_expediente']
  v['expediente_fuente_html']=row['fuente_html']
  v['url_sesion_evidencia']=row['url_sesion']
  return v
 for x in preload['votaciones']:update_vote(x)
 assert len(preload['votaciones'])==2177
 prepath.write_text(prefix+json.dumps(preload,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
 pkpath=datos/'paquetes.json';pk=json.loads(pkpath.read_text(encoding='utf-8'))
 for d in pk['paquetes']:
  source=out/d['ruta'];payload=json.loads(source.read_text(encoding='utf-8'))
  for x in payload['votaciones']:update_vote(x)
  raw=json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
  source.write_text(raw,encoding='utf-8')
  d['sha256']=hashlib.sha256(raw.encode('utf-8')).hexdigest()
 pk['version']='0.8.2';pkpath.write_text(json.dumps(pk,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 summary={
  'version':'0.8.2','fecha_revision':'2026-10-28',
  'archivos_html_recibidos':len(manifest),'archivos_html_integridad_sha256':len(manifest),
  'votaciones_total':len(outrows),'votaciones_cotejadas_html':len(byurl),
  'votaciones_con_cotejo_previo_fuera_zip':stats['COTEJO_ANTERIOR'],
  'asociaciones_unicas_html':stats['UNICO_HTML'], 'votaciones_multi_expediente':stats['MULTIPLE_HTML'],
  'asociaciones_unicas_previas':stats['COTEJO_ANTERIOR'],
  'relaciones_votacion_expediente':len(relations),
  'expedientes_distintos':len(set(x['expediente_id'] for x in relations)),
  'votaciones_sin_expediente':sum(not bool(x['expediente_id']) for x in outrows),
  'candidatos_previos_cotejados':len(annotated),
  'candidatos_previos_corregidos':stats['propuestas_anteriores_corregidas'],
  'candidatos_previos_incompletos_por_voto_conjunto':stats['propuestas_anteriores_incompletas'],
  'correcciones':audit_cases,
  'votaciones_multi':[{'votacion_id':r['votacion_id'],'fecha':r['fecha'],'expedientes':r['expediente_id'].split(' | ')} for r in outrows if r['estado_expediente']=='MULTIPLE_HTML'],
  'notas':[
   'Los 2.134 registros cotejados se apoyan en HTML proporcionado por el usuario, cuyo manifiesto SHA-256 coincide con sus contenidos. No equivale a un cotejo en vivo del servidor.',
   'Los otros 43 registros ya estaban documentalmente vinculados en la version 0.8.1; sus HTML no estaban en el ZIP recibido. Se mantiene esa procedencia separada.',
   'La cobertura de expedientes es completa respecto al inventario de 2.177 votos de la web, NO respecto a todas las votaciones oficiales historicas ni a todas las comisiones.',
   'Los recuentos nominales individuales aun contienen diferencias respecto a los agregados; la vinculacion de expedientes no resuelve ese problema.',
   'La afiliacion historica de todos los partidos sigue pendiente.'
  ]
 }
 (datos/'auditoria_expedientes_v082.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 # Update version-level metadata; retain previous audit snapshots as historic material.
 status=datos/'estado_publicacion.json';state=json.loads(status.read_text(encoding='utf-8'))
 state.update({'version':'0.8.2','fecha_revision':'2026-10-28','expedientes_con_url':sum(len(x['expediente_id'].split(' | '))==1 for x in outrows),
 'expedientes_pendientes':0,'expedientes_multiples':15,'expedientes_con_cotejo_html':len(byurl),
 'relaciones_votacion_expediente':len(relations),'auditoria_expedientes':'datos/auditoria_expedientes_v082.json',
 'estado':'2.177 votaciones documentadas; expediente asociado por contexto HTML para 2.134, cotejo previo para 43. Otras limitaciones: nominales y partidos.'})
 status.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in summary.items() if k not in ('correcciones','votaciones_multi','notas')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
