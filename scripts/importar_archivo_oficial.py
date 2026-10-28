#!/usr/bin/env python3
"""Imports official Congress ZIP session archives; optional catalogue discovery.

No claim that selected dates cover all available roll-call votes unless the
list of sitting dates is independently reconciled. Date discovery uses the
public HTML selector when it exposes dates; some Congress releases rely on
client-side JavaScript and may require --fechas.

Examples:
 python scripts/importar_archivo_oficial.py --legislatura XIII --zip-dir descargas/XIII --salida borrador/XIII
 python scripts/importar_archivo_oficial.py --legislatura X --descargar --desde 2012-01-01 --hasta 2015-10-27 --salida borrador/X
 python scripts/construir_paquetes.py --legislatura XIII --votaciones borrador/XIII/votaciones.csv --grupos borrador/XIII/votos-grupo.csv
"""
from __future__ import annotations
import argparse,csv,datetime,hashlib,io,json,re,time,urllib.parse,urllib.request,zipfile
from collections import defaultdict
from pathlib import Path
from html.parser import HTMLParser

BASE='https://www.congreso.es/es/opendata/votaciones'
HTTP={'User-Agent':'Observatorio-QHV/0.3 (investigacion civica; sin recopilacion de datos privados)'}
LEGS=['X','XI','XII','XIII','XIV','XV']
def clean(k):return re.sub(r'[^a-z0-9]','',str(k).lower())
def find(d,*keys):
    if not isinstance(d,dict):return None
    m={clean(k):v for k,v in d.items()}
    for key in keys:
        if clean(key) in m:return m[clean(key)]
    return None

def locate(obj,*k):
    seen=[]
    def walk(x,depth):
        if depth>4:return
        if isinstance(x,dict):
            val=find(x,*k)
            if val is not None and not isinstance(val,(list,dict)):seen.append(val)
            for v in x.values():
                if isinstance(v,dict):walk(v,depth+1)
    walk(obj,0)
    return seen[0] if seen else None

def datefmt(x):
    s=str(x or '').strip()
    a=re.search(r'(\d{2})[/.-](\d{2})[/.-](\d{4})',s)
    if a:return a[3]+'-'+a[2]+'-'+a[1]
    b=re.search(r'(20\d{2})-(\d{2})-(\d{2})',s)
    return b.group() if b else ''

def integer(x):
    try:return int(str(x).replace('.','').replace(',','.'))
    except:return None

def official_json(data,leg,link,context=None):
    """Read fields when present; refuses to invent votes or descriptions.

    Context provides a separately extracted title/subject from the day page.
    """
    if not isinstance(data,dict):return None,[],['JSON not an object']
    info=data.get('informacion') or data.get('Informacion') or data.get('Información') or {}
    datestr=datefmt(locate(info,'fecha','fechaVotacion') or locate(data,'fechaVotacion','fecha'))
    number=integer(locate(info,'numeroVotacion','votacion','numero') or locate(data,'numeroVotacion'))
    session=integer(locate(info,'sesion','numeroSesion') or locate(data,'numeroSesion'))
    path=re.search(r'Sesion(\d+)/(\d{8})/Votacion(\d+)',link,re.I)
    if path:
        session=session if session is not None else int(path[1])
        number=number if number is not None else int(path[3])
        if not datestr:datestr=path[2][:4]+'-'+path[2][4:6]+'-'+path[2][6:8]
    if not datestr:return None,[],['No session date; record held back']
    if session is None or number is None:return None,[],['No session/number; record held back']
    title=(context or {}).get('titulo') or locate(info,'titulo','asunto','descripcionVotacion','textoVotacion') or locate(data,'titulo','asunto','descripcionVotacion')
    if not title:title='Título oficial pendiente de asociar con la votación'
    typ=(context or {}).get('tipo') or locate(info,'tipoVotacion','tipo') or 'Trámite (sin clasificar)'
    si=integer(locate(data.get('totales') or {},'aFavor','favor','si','votosAFavor'))
    no=integer(locate(data.get('totales') or {},'enContra','contra','no','votosEnContra'))
    abst=integer(locate(data.get('totales') or {},'abstenciones','abstencion'))
    nov=integer(locate(data.get('totales') or {},'noVotan','noVota','ausentes'))
    # Loose fallback for JSON with totals at top level.
    if si is None:si=integer(find(data,'aFavor','votosAFavor','si'))
    if no is None:no=integer(find(data,'enContra','votosEnContra','no'))
    uid=f's{session:03d}-v{number:03d}'
    vote={'id':uid,'legislatura':leg,'fecha':datestr,'sesion':session,'numero':number,'tipo':typ,'titulo':title,
          'resultado':'No confirmado','si':si,'no':no,'abstencion':abst,'no_vota':nov,
          'url_votacion':link if link.startswith('http') else '',
          'calidad':('Título pendiente de contextualización' if str(title).startswith('Título oficial pendiente') else 'Registro oficial; estado parlamentario por confirmar')}
    rows=find(data,'votaciones','diputados','votos')
    if isinstance(rows,dict):rows=list(rows.values())
    if not isinstance(rows,list):
        # Search common nested structure without identifying the totals as votes.
        rows=[]
        for k,v in data.items():
            if isinstance(v,dict):
                x=find(v,'votaciones','diputados','votos')
                if isinstance(x,list):rows=x;break
    individual=[]
    for r in rows:
        if not isinstance(r,dict):continue
        who=find(r,'diputado','nombre','nombreDiputado')
        v=find(r,'voto','sentido','valor')
        if isinstance(who,dict):who=find(who,'nombre','nombreCompleto')
        if not who or not v:continue
        individual.append({'votacion_id':uid,'fecha':datestr,'legislatura':leg,'diputado':str(who),
                           'diputado_id':str(find(r,'diputadoId','codigoDiputado','idDiputado') or ''),
                           'grupo':str(find(r,'grupo','grupoParlamentario') or ''),'voto':str(v),'circunscripcion':''})
    issues=[]
    if not individual:issues.append('No individual votes in JSON; no group/candidacy disaggregation')
    if all(vote[k] is None for k in ('si','no','abstencion')):issues.append('No clear official totals')
    return vote,individual,issues

class PageLinks(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.dates=set();self.anchor=None;self.in_select=False
 def handle_starttag(self,tag,attrs):
    a=dict(attrs)
    if tag=='a' and a.get('href'):self.links.append(a['href'])
    if tag=='option':
      self.anchor=a.get('value','');m=re.search(r'\d{2}/\d{2}/20\d{2}',self.anchor)
      if m:self.dates.add(datefmt(m.group()))
 def handle_data(self,text):
    if self.anchor is not None:
      m=re.search(r'\d{2}/\d{2}/20\d{2}',text)
      if m:self.dates.add(datefmt(m.group()))
 def handle_endtag(self,tag):
    if tag=='option':self.anchor=None

def fetch(url,timeout=25):
 req=urllib.request.Request(url,headers=HTTP)
 with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()

def discover_dates(leg):
 url=BASE+'?'+urllib.parse.urlencode({'targetLegislatura':leg})
 text=fetch(url).decode('utf-8','replace');p=PageLinks();p.feed(text)
 return sorted(p.dates)

def download_zips(leg,dates,cachedir,seconds=0.4):
 cachedir.mkdir(parents=True,exist_ok=True);found=[];errors=[]
 for n,date in enumerate(dates,1):
    us=date[8:10]+'/'+date[5:7]+'/'+date[:4]
    url=BASE+'?'+urllib.parse.urlencode({'targetLegislatura':leg,'targetDate':us})
    try:
      page=fetch(url).decode('utf-8','replace');p=PageLinks();p.feed(page)
      links=[urllib.parse.urljoin(url,u) for u in p.links if re.search(r'\.zip(?:[?&#]|$)',u,re.I)]
      for idx,link in enumerate(dict.fromkeys(links),1):
        path=cachedir/f'{leg}-{date}-{idx:02d}.zip'
        if not path.exists():path.write_bytes(fetch(link));time.sleep(seconds)
        if not zipfile.is_zipfile(path):errors.append(f'{date}: invalid ZIP {path.name}');continue
        found.append(path)
      if not links:errors.append(f'{date}: no ZIP link in official HTML')
    except Exception as e:errors.append(f'{date}: {e}')
    print(f'[{n}/{len(dates)}] {leg} {date}: {len(found)} ZIPs saved',flush=True)
 return found,errors

def writecsv(path,rows,fields):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def main():
 p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
 p.add_argument('--legislatura',required=True,choices=LEGS);p.add_argument('--zip-dir',type=Path)
 p.add_argument('--descargar',action='store_true');p.add_argument('--fechas',type=Path,help='Text file: one sitting date per line, YYYY-MM-DD')
 p.add_argument('--desde',default='');p.add_argument('--hasta',default='');p.add_argument('--salida',required=True,type=Path)
 opt=p.parse_args()
 if not opt.descargar and not opt.zip_dir:p.error('Provide --descargar or --zip-dir')
 archive=opt.zip_dir or opt.salida/'zips';files=list(archive.glob('**/*.zip')) if archive.exists() else []
 problems=[];dates=[]
 if opt.descargar:
    if opt.fechas:dates=[x.strip() for x in opt.fechas.read_text().splitlines() if x.strip() and not x.startswith('#')]
    else:
      try:dates=discover_dates(opt.legislatura)
      except Exception as e:raise SystemExit('Could not discover dates; provide --fechas: '+str(e))
    dates=[d for d in dates if (not opt.desde or d>=opt.desde) and (not opt.hasta or d<=opt.hasta)]
    if not dates:raise SystemExit('No known dates for requested selection; no records will be invented')
    files,errors=download_zips(opt.legislatura,dates,archive);problems.extend(errors)
 if not files:raise SystemExit('No ZIPs to import')
 votes={};nominal=[];hashes=[]
 for path in sorted(files):
    raw=path.read_bytes();hashes.append({'archivo':str(path),'sha256':hashlib.sha256(raw).hexdigest()})
    try:
      z=zipfile.ZipFile(io.BytesIO(raw))
      for name in z.namelist():
        if not name.lower().endswith('.json'):continue
        try:doc=json.loads(z.read(name))
        except Exception as e:problems.append(f'{path.name}/{name}: invalid JSON {e}');continue
        # URL inferred from official ZIP? Local ZIP does not guarantee permanent JSON URL.
        link=name
        row,deputies,issues=official_json(doc,opt.legislatura,link)
        if row:
          if opt.desde and row['fecha']<opt.desde or opt.hasta and row['fecha']>opt.hasta:continue
          if row['id'] in votes and votes[row['id']]!=row:problems.append(f'Duplicate conflicting vote ID: {row["id"]}')
          votes[row['id']]=row;nominal.extend(deputies)
        problems.extend(f'{path.name}/{name}: {x}' for x in issues)
    except Exception as e:problems.append(f'{path}: {e}')
 out=opt.salida;out.mkdir(parents=True,exist_ok=True)
 writecsv(out/'votaciones.csv',sorted(votes.values(),key=lambda x:(x['fecha'],x['id'])),['id','legislatura','fecha','sesion','numero','tipo','titulo','resultado','si','no','abstencion','no_vota','url_votacion','calidad'])
 writecsv(out/'votos-diputado.csv',nominal,['legislatura','votacion_id','fecha','diputado_id','diputado','grupo','circunscripcion','voto'])
 (out/'auditoria.json').write_text(json.dumps({'legislatura':opt.legislatura,'descargas':hashes,'fechas_solicitadas':dates,'zips_procesados':len(files),
 'votaciones':len(votes),'votos_nominales':len(nominal),'advertencias':problems,
 'veredicto_cobertura':'NO COMPLETA: hay que reconciliar el calendario, fechas con llamamientos, archivos fallidos y vincular los títulos con el listado oficial antes de publicar'},ensure_ascii=False,indent=2),encoding='utf8')
 print('Votaciones:',len(votes),'Votos nominales:',len(nominal),'Advertencias:',len(problems))
 print('Auditoría:',out/'auditoria.json')
if __name__=='__main__':main()
