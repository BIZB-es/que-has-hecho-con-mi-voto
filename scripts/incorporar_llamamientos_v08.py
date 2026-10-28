#!/usr/bin/env python3
"""Agrega dos votaciones por llamamiento documentadas del 02/10/2026.
No inventa votos nominales, grupos o JSON electrónicos inexistentes.
"""
import csv, hashlib, json
from pathlib import Path
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parent.parent
SRC_AV='https://app.congreso.es/AudiovisualCongreso/audiovisualdetalledisponible?codOrgano=400&codSesion=203&fechaSesion=02%2F10%2F2026&i=779883&idLegislaturaElegida=15&mp4=mp4'
EXP_BASE='https://www.congreso.es/es/busqueda-de-iniciativas?p_p_id=iniciativas&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_iniciativas_mode=mostrarDetalle&_iniciativas_legislatura=XV&_iniciativas_id='
VOTES=[
 {'id':'s203-ll001','legislatura':'XV','fecha':'2026-10-02','sesion':'203','numero':'1','tipo':'Convalidación o derogación de real decreto-ley (votación por llamamiento)','titulo':'Convalidación del Real Decreto-ley 26/2026, de 29 de septiembre, por el que se adoptan medidas urgentes para la protección de la función social de la vivienda y la ampliación de la oferta de vivienda asequible.','temas':'vivienda','areas':['vivienda-y-urbanismo'],'area_origen':'revisión editorial según título oficial','resultado':'Derogado','si':172,'no':178,'abstencion':0,'no_vota':0,'expediente':'130/000055','url_expediente':EXP_BASE+'130/000055','url_votacion':SRC_AV,'expediente_fuente':'Orden del día audiovisual del Congreso, sesión 203 del 02/10/2026', 'fuente':'Congreso (sesión audiovisual y BOE); recuento: crónica de El Debate de 02/10/2026', 'calidad':'Votación por llamamiento fuera de los CSV nominales; no se dispone del desglose de votos por persona o grupo en los archivos recibidos.','resumen':'El Pleno rechazó convalidar el Real Decreto-ley 26/2026; la resolución de derogación se publicó en el BOE.','fuente_normativa':'https://www.boe.es/buscar/doc.php?id=BOE-A-2026-20526','fuente_recuento':'https://www.eldebate.com/espana/20261002/asi-han-votado-partidos-decretos-vivienda-quien-apoyado-quien-tumbado-cada-texto-cns_465496_amp.html','metadatos_enlaces':'Votación por llamamiento; votación con resultado confirmado por BOE y votación en audiovisual oficial; cifra por crónica periodística'},
 {'id':'s203-ll002','legislatura':'XV','fecha':'2026-10-02','sesion':'203','numero':'2','tipo':'Convalidación o derogación de real decreto-ley (votación por llamamiento)','titulo':'Convalidación del Real Decreto-ley 27/2026, de 29 de septiembre, por el que se adoptan medidas urgentes para reforzar la estabilidad de los contratos de arrendamiento de vivienda habitual.','temas':'vivienda','areas':['vivienda-y-urbanismo'],'area_origen':'revisión editorial según título oficial','resultado':'Derogado','si':166,'no':184,'abstencion':0,'no_vota':0,'expediente':'130/000056','url_expediente':EXP_BASE+'130/000056','url_votacion':SRC_AV,'expediente_fuente':'Orden del día audiovisual del Congreso, sesión 203 del 02/10/2026','fuente':'Congreso (sesión audiovisual y BOE); recuento: crónica de El Debate de 02/10/2026','calidad':'Votación por llamamiento fuera de los CSV nominales; no se dispone del desglose de votos por persona o grupo en los archivos recibidos.','resumen':'El Pleno rechazó convalidar el Real Decreto-ley 27/2026; la resolución de derogación se publicó en el BOE.','fuente_normativa':'https://www.boe.es/buscar/doc.php?id=BOE-A-2026-20527','fuente_recuento':'https://www.eldebate.com/espana/20261002/asi-han-votado-partidos-decretos-vivienda-quien-apoyado-quien-tumbado-cada-texto-cns_465496_amp.html','metadatos_enlaces':'Votación por llamamiento; votación con resultado confirmado por BOE y votación en audiovisual oficial; cifra por crónica periodística'}
]

def save_json(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def add_list(doc):
  ids={v['id'] for v in doc['votaciones']}
  for v in VOTES:
    if v['id'] not in ids:doc['votaciones'].append(v.copy())
  doc['votaciones'].sort(key=lambda x:(x['fecha'],x['id']))

p=ROOT/'assets/precarga_XV.js';content=p.read_text(encoding='utf8');prefix='window.QHV_PRECARGA_XV=';assert content.startswith(prefix)
doc=json.loads(content[len(prefix):].strip().rstrip(';'))
assert len(doc['votaciones']) in (2175,2177)
add_list(doc)
assert len(doc['votaciones'])==2177
p.write_text(prefix+json.dumps(doc,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
q=ROOT/'datos/historico/XV-2026.json';year=json.loads(q.read_text(encoding='utf8'));add_list(year);assert len(year['votaciones'])==542
q.write_text(json.dumps(year,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
manifest=ROOT/'datos/paquetes.json';m=json.loads(manifest.read_text())
for pkg in m['paquetes']:
    if pkg['anio']=='2026':
        pkg['registros']=542;pkg['hasta']='2026-10-02';pkg['sha256']=hashlib.sha256(q.read_bytes()).hexdigest();pkg['fuente']='Congreso Abierto (CSV 2026 hasta 30/09) + 2 por llamamiento (Congreso/BOE)'
m['version']='0.8';m['nota']='2.175 votos del CSV nominal XV + dos votaciones por llamamiento documentadas del 02/10/2026, sin nominales.'
save_json(manifest,m)
save_json(ROOT/'datos/llamamientos_2026.json',{'legislatura':'XV','sesion':203,'fecha':'2026-10-02','fuentes':[SRC_AV], 'registros':VOTES,'nota':'No hay CSV nominal adjunto; no deben inferirse grupos ni diputados.'})
vinc=ROOT/'datos/vinculos_XV.csv'
with open(vinc,encoding='utf-8-sig',newline='') as f:r=csv.DictReader(f,delimiter=';');rows=list(r);cols=r.fieldnames
for v in VOTES:
    if not any(x['votacion_id']==v['id'] for x in rows):rows.append({'votacion_id':v['id'],'fecha':v['fecha'],'titulo':v['titulo'],'url_votacion':v['url_votacion'],'expediente_id':v['expediente'],'url_expediente':v['url_expediente'],'metodo_vinculacion':v['expediente_fuente']})
with open(vinc,'w',encoding='utf-8-sig',newline='') as f:r=csv.DictWriter(f,fieldnames=cols,delimiter=';');r.writeheader();r.writerows(rows)
assert len(rows)==2177
state=ROOT/'datos/estado_publicacion.json';x=json.loads(state.read_text());x['version']='0.8';x['registros_XV_precargados']=2177;x['registro_fuente_csv']=2175;x['registros_por_llamamiento_fuera_csv']=2;x['fecha_ultima']='2026-10-02';x['datos_calidad']='datos/calidad_XV.json';x['enlaces_expedientes']=30;x['estado']='2.175 votaciones nominales del CSV y dos por llamamiento añadidas con fuente documental; detalles nominales incompletos y expedientes pendientes de conciliar.';save_json(state,x)
print('Añadidas 2 votaciones por llamamiento; total registros precargados:',len(doc['votaciones']))
