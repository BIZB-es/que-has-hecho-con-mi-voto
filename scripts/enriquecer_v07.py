#!/usr/bin/env python3
"""Enriquece la v0.6 a partir de 3 CSV recibidos; no deduce partidos ni expedientes.

La vinculacion automatica incluye 21 votaciones de una unica sesion cotejada
contra la pagina oficial de datos abiertos (30/09/2026). El resto de expedientes
solo se enlaza si aparece en el CSV original, sin fabricar correspondencias.
"""
import argparse, csv, hashlib, json, re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
OFFICIAL_ROOT = 'https://www.congreso.es/es/busqueda-de-diputados?codParlamentario={id}&idLegislatura=XV&mostrarFicha=true'
EXPEDIENT_URL = ('https://www.congreso.es/es/busqueda-de-iniciativas?p_p_id=iniciativas&p_p_lifecycle=0'
    '&p_p_state=normal&p_p_mode=view&_iniciativas_mode=mostrarDetalle'
    '&_iniciativas_legislatura=XV&_iniciativas_id={exp}')
OFFICIAL_SESSION = 'https://www.congreso.es/es/opendata/votaciones'

# La asignacion de la sesion 202 se contrasto con el listado oficial de
# 30/09/2026, por numero de votacion, titulo y totales; ver auditoria_v07.json.
SESSION_202 = {
    1:'162/000814',2:'162/000769',3:'173/000194',4:'173/000194',5:'173/000194',
    6:'173/000195',7:'173/000196',8:'173/000196',9:'173/000196',
    10:'121/000106',11:'110/000081',12:'110/000082',13:'110/000083',
    14:'110/000084',15:'110/000085',16:'110/000086',17:'152/000008',
    18:'154/000006',19:'121/000092',20:'042/000044',21:'240/000002'
}

# Formacion como se muestra en la ficha del Congreso (no equivale necesariamente a partido).
# Una ficha fechada no constituye por si sola un historial de afiliacion politica.
FICHAS_CONSULTADAS={
 '262': {'formacion_ficha':'PODEMOS', 'nota':'Formación mostrada en la ficha oficial; NO se ha verificado un historial de afiliación.',
    'grupos_verificados':[{'grupo':'SUMAR','desde':'2023-08-28','hasta_exclusiva':'2023-12-05'},
                          {'grupo':'Mixto','desde':'2023-12-06','hasta_exclusiva':None}],
    'fecha_cambio_pendiente':'2023-12-05'},
 '164': {'formacion_ficha':'SUMAR','nota':'La ficha muestra SUMAR como formación electoral; su trayectoria menciona Compromís. No atribuir como afiliación a un partido específico.',
    'grupos_verificados':[{'grupo':'SUMAR','desde':'2023-08-28','hasta_exclusiva':'2025-07-03'},
                          {'grupo':'Mixto','desde':'2025-07-04','hasta_exclusiva':None}],
    'fecha_cambio_pendiente':'2025-07-03'},
 '38': {'formacion_ficha':'CCa', 'nota':'Formación mostrada en ficha oficial. No se dispone aquí de historial fechado del grupo.', 'grupos_verificados':[]},
 '238': {'formacion_ficha':'BNG', 'nota':'Formación mostrada en ficha oficial. No se dispone aquí de historial fechado del grupo.', 'grupos_verificados':[]},
}

def read_csv(path, sep=','):
 with open(path, encoding='utf-8-sig', newline='') as f:
  return list(csv.DictReader(f, delimiter=sep))

def norm(s):
 s=s.upper().replace('ª','A').replace('º','O')
 s=''.join(ch for ch in unicodedata.normalize('NFKD', s) if not unicodedata.combining(ch))
 return re.sub(r'[^A-Z0-9]', '', s)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dump(path, val):
 Path(path).parent.mkdir(parents=True,exist_ok=True)
 Path(path).write_text(json.dumps(val,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--votaciones',type=Path,required=True)
 ap.add_argument('--votos',type=Path,required=True)
 ap.add_argument('--censo',type=Path,required=True)
 args=ap.parse_args()
 v=read_csv(args.votaciones);d=read_csv(args.votos);c=read_csv(args.censo,';')
 assert len(v)==2175 and len({x['id'] for x in v})==2175, 'Identificadores o total inesperados'
 assert len(d)==726564,'Total de votos nominales inesperado'
 assert len(c)==6325, 'Censo no coincide con el archivo recibido'
 ix={z['id']:z for z in v}
 persons={z['diputado_id']:z['diputado'] for z in d}
 if len(persons)!=350:raise ValueError(f'{len(persons)} personas únicas en votos, esperado 350')
 reverse=defaultdict(set)
 for z in d:reverse[z['diputado_id']].add((z['diputado'],z['circunscripcion'],z['grupo']))
 assert all(len({name for name,_,_ in vv})==1 for vv in reverse.values())
 census_xv=[z for z in c if z['LEGISLATURA']=='Leg. XV']
 # Los campos FECHAINICIOLEGISLATURA / FECHAFINLEGISLATURA se refieren a la
 # legislatura, NO necesariamente a la toma de posesión de cada diputado.
 byname=defaultdict(list)
 for z in census_xv:byname[norm(z['NOMBRE']+' '+z['APELLIDOS'])].append(z)
 match={}
 for pid,name in persons.items():
  rr=byname.get(norm(name),[])
  if len(rr)!=1:raise ValueError(f'Identidad no univoca: {pid} {name} ({len(rr)} coincidencias)')
  match[pid]=rr[0]
 assert len(match)==350
 names_to_id={name:pid for pid,name in persons.items()}
 byname_catalog={}
 for pid,name in sorted(persons.items(),key=lambda r:int(r[0])):
  row={'codigo':pid,'nombre':name,'nombre_censo':match[pid]['NOMBRE']+' '+match[pid]['APELLIDOS'],
       'url_ficha':OFFICIAL_ROOT.format(id=pid), 'censo':'Coincidencia exacta normalizada en legislatura XV',
       'partido':'', 'partido_estado':'Sin constancia en los archivos recibidos',
       'grupo_nominal':'Etiqueta de los votos del proveedor, no verificada historicamente'}
  row.update(FICHAS_CONSULTADAS.get(pid,{}))
  byname_catalog[name]=row
 census_rows=[]
 for z in sorted(census_xv,key=lambda x:norm(x['APELLIDOS']+' '+x['NOMBRE'])):
  fullname=z['NOMBRE']+' '+z['APELLIDOS'];pid=names_to_id.get(fullname)
  if not pid:
   matches=[i for i,n in persons.items() if norm(n)==norm(fullname)]
   pid=matches[0] if len(matches)==1 else None
  census_rows.append({'nombre':fullname,'codigo':pid,'url_ficha':OFFICIAL_ROOT.format(id=pid) if pid else '',
    'voto_en_csv':bool(pid),'legislatura':'XV',
    'formacion_ficha':FICHAS_CONSULTADAS.get(pid or '',{}).get('formacion_ficha','')})
 assert len(census_rows)==412 and sum(bool(x['codigo']) for x in census_rows)==350

 # Enlaces al expediente: 7 ya incluidos, 21 vinculados por listado de sesión.
 direct={}
 for x in v:
  eid='';method='sin_vinculo'
  if x['url_expediente']:
   raw=parse_qs(urlparse(x['url_expediente']).query).get('_iniciativas_id',[''])[0]
   if not re.fullmatch(r'\d{2,3}/\d{4,6}',raw):raise ValueError(f'Expediente mal formado: {x["id"]}')
   eid=raw;method='URL expediente aportada en CSV'
  elif x['sesion']=='202' and x['id'].startswith('s202-v'):
   num=int(x['numero']);eid=SESSION_202.get(num,'');method='Listado oficial de la sesion 202 cotejado por numero, titulo y totales'
  direct[x['id']]=(eid,x['url_expediente'] or (EXPEDIENT_URL.format(exp=eid) if eid else ''),method)
 assert sum(bool(z[0]) for z in direct.values())==28
 assert len({z['url_votacion'] for z in v})==2175

 # Preservamos el objeto original v0.6, sus categorias y los 19.561 agregados.
 preload=ROOT/'assets/precarga_XV.js'
 pre=preload.read_text(encoding='utf-8');existing=json.loads(pre.split('=',1)[1].strip().rstrip(';'))
 if {z['id'] for z in existing['votaciones']}!=set(ix):raise ValueError('La precarga actual no contiene exactamente los IDs recibidos')
 for o in existing['votaciones']:
  src=ix[o['id']]
  for key in ('titulo','fecha','si','no','abstencion','resultado'):
   if str(o[key])!=str(src[key]):raise ValueError(f'Desacuerdo en {key} para {o["id"]}')
  o['no_vota']=int(src['no_vota'])
  o['url_votacion']=src['url_votacion']
  eid,elink,origin=direct[o['id']]
  o['expediente']=eid;o['url_expediente']=elink
  o['expediente_fuente']=origin;o['metadatos_enlaces']='Votacion: URL oficial del CSV; expediente: '+origin
 existing['fuente']+=' · enlaces oficiales añadidos desde nueva exportación CSV'
 preload.write_text('window.QHV_PRECARGA_XV='+json.dumps(existing,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
 for year in ('2023','2024','2025','2026'):
  loc=ROOT/f'datos/historico/XV-{year}.json'
  obj=json.loads(loc.read_text(encoding='utf-8'))
  for vote in obj['votaciones']:
   src=ix[vote['id']];eid,elink,method=direct[vote['id']]
   vote['no_vota']=int(src['no_vota']);vote['url_votacion']=src['url_votacion'];vote['url_expediente']=elink
   vote['expediente']=eid;vote['expediente_fuente']=method
  dump(loc,obj)

 # Actualizar hashes y metadatos en el manifiesto anual.
 pfile=ROOT/'datos/paquetes.json';p=json.loads(pfile.read_text(encoding='utf-8'))
 for entry in p['paquetes']:
  fname=ROOT/entry['ruta'];entry['sha256']=sha(fname)
 dump(pfile,p)

 identity={'legislatura':'XV','fecha_revision':'2026-10-26',
  'alcance':{'censo_oficial':len(census_rows),'diputados_identificados':len(byname_catalog),
    'expedientes_enlazados':28,'partidos_verificados_sistematicamente':False,
    'formaciones_con_ficha_individual_cotejada':len(FICHAS_CONSULTADAS)},
  'advertencia':'El archivo general del censo NO contiene partido, candidatura ni periodos de grupo. Las etiquetas de grupo del CSV de votos son una fotografia del proveedor, no un historial. No extrapolar partido desde grupo.',
  'por_nombre':byname_catalog,'censo':census_rows}
 dump(ROOT/'datos/identidades_XV.json',identity)
 (ROOT/'assets/identidades_XV.js').write_text('window.QHV_IDENTIDADES_XV='+json.dumps(identity,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')

 with (ROOT/'datos/vinculos_XV.csv').open('w',encoding='utf-8-sig',newline='') as fo:
  w=csv.writer(fo,delimiter=';');w.writerow(['votacion_id','fecha','titulo','url_votacion','expediente_id','url_expediente','metodo_vinculacion'])
  for x in v:
   eid,url,met=direct[x['id']];w.writerow([x['id'],x['fecha'],x['titulo'],x['url_votacion'],eid,url,met])
 with (ROOT/'datos/censo_XV.csv').open('w',encoding='utf-8-sig',newline='') as fo:
  w=csv.writer(fo,delimiter=';');w.writerow(['nombre','codigo_parlamentario','tiene_voto_en_csv','url_ficha','formacion_ficha_verificada'])
  for x in census_rows:w.writerow([x['nombre'],x['codigo'] or '',x['voto_en_csv'],x['url_ficha'],x['formacion_ficha']])

 audit={'version':'0.7','fecha':'2026-10-26','origen':{str(k):{'archivo':q.name,'sha256':sha(q)} for k,q in [('votaciones',args.votaciones),('votos_individuales',args.votos),('censo',args.censo)]},
  'votaciones_total':2175,'urls_oficiales_votacion':2175,
  'expedientes_directos':28,'expedientes_del_csv':7,'expedientes_de_sesion_cotejada':21,'expedientes_pendientes':2147,
  'fuente_21':OFFICIAL_SESSION+' (sesion 202, 30-09-2026; cotejo manual con totales y titulos)',
  'ids_votacion_no_estandar':[x['id'] for x in v if not re.fullmatch(r's\d+-v\d+',x['id'])],
  'censo_XV_filas':412,'registros_nominales':len(d),'diputados_codigos_unicos':350,'cruces_nombre_univocos':350,
  'personas_censo_sin_codigo_en_csv_votos':62,'perfiles_ficha_cotejados':sorted(FICHAS_CONSULTADAS),
  'grupo_con_historial_automatico':False,'partidos_completos':False,
  'limites':['Los 350 codigos proceden del CSV de votos y se cruzaron por nombre normalizado con el censo.',
             'Los 62 restantes no tienen un ID en los datos aportados; no inferir que no votaron en ninguna circunstancia.',
             'FECHAINICIOLEGISLATURA no es fecha de alta individual en el escaño.',
             'La columna grupo del CSV individual no documenta los cambios historicos de grupo.',
             'URL oficial de voto no implica disponer del numero de expediente.',
             'Las URL de expediente reconstruidas siguen el formato conocido, pero no se han comprobado por HTTP en este entorno.',
             'No hay perfil de afiliacion a partido completo y no se calculan totales por partido.']}
 dump(ROOT/'datos/auditoria_v07.json',audit)
 print(json.dumps({'votaciones':2175,'votos':len(d),'censo':412,'match':len(match),'url_votacion':2175,'url_expediente':28,'faltan_expedientes':2147},ensure_ascii=False))

if __name__=='__main__':main()
