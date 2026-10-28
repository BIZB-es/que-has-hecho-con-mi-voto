#!/usr/bin/env python3
"""Importa los tres CSV de Congreso Abierto para XV, preservando su procedencia.

Entradas: CSV de votaciones, votos-grupo, votos-diputados (formato original con ;).
Salidas: fichas anuales JSON, precarga JS sin servidor, detalle nominal por sesión,
auditoría reproducible y manifiesto de cobertura. Nunca atribuye partidos.
Solo permite el intervalo registrado, no afirma cobertura de otras votaciones.
"""
import argparse,collections,csv,datetime as dt,hashlib,json,re,unicodedata
from pathlib import Path
from functools import lru_cache
ROOT=Path(__file__).resolve().parent.parent
SRC_URL='https://congresoabierto.org/datos/'
OFFICIAL='https://www.congreso.es/es/opendata/votaciones'
ALLOWED={'Sí':0,'No':1,'Abstención':2,'No vota':3}
TOPICS={'instituciones':'constitución--instituciones-y-monarquía',
        'territorio':'organización-territorial-y-autonomías',
        'justicia':'justicia-y-derechos-fundamentales',
        'trabajo':'trabajo--empleo-y-relaciones-laborales',
        'economia':'economía--empresas-y-competencia',
        'vivienda':'vivienda-y-urbanismo','sanidad':'sanidad-y-salud-pública',
        'educacion':'educación-no-universitaria',
        'igualdad':'igualdad--feminismo-y-violencia-de-género',
        'transporte':'transporte--tráfico-y-movilidad',
        'campo-medioambiente':'medio-ambiente-y-cambio-climático',
        'migracion':'migración--extranjería-y-asilo',
        'exterior':'relaciones-internacionales-y-cooperación',
        'defensa':'defensa-y-fuerzas-armadas'}

def read_csv(p):
 with p.open('r',encoding='utf-8-sig',newline='') as f:
  rdr=csv.DictReader(f,delimiter=';')
  if not rdr.fieldnames:raise ValueError(f'{p}: archivo vacío')
  for row in rdr:
   if None in row:raise ValueError(f'{p}: fila mal formada')
   yield row

def hash_bytes(data):return hashlib.sha256(data).hexdigest()
def write_json(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 data=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode('utf-8')
 p.write_bytes(data)
 return hash_bytes(data)
def write_script(p,assignment,obj):
 raw=(f'window.{assignment}='+json.dumps(obj,ensure_ascii=False,separators=(',',':'))+';\n').encode('utf-8')
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 return hash_bytes(raw)

def fold(s):return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if not unicodedata.combining(c))
@lru_cache(maxsize=None)
def pattern_for(word):
 p=fold(word)
 return None if len(p)<3 else re.compile(r'(?<![\w])'+re.escape(p)+r'(?![\w])')

def words_match(folded_text,word):
 pattern=pattern_for(word)
 return pattern is not None and pattern.search(folded_text) is not None

def areas(row,tax):
 tags=[x.strip() for x in row['Temas'].split('|')]
 manual=[TOPICS[t] for t in tags if t in TOPICS]
 # Reconocemos una fuente de categorías gruesas y no fingimos revisión editorial.
 # Para 'otros' solo intentamos clasificar por términos explícitos del título.
 proposed=[]
 if 'otros' in tags or not manual:
  title_folded=fold(row['Título'])
  for item in tax:
   if item['id']=='sin-clasificar':continue
   if any(words_match(title_folded,term) for term in item['palabras']):proposed.append(item['id'])
 result=list(dict.fromkeys(manual+proposed))
 return result[:7] or ['sin-clasificar']

def run(vpath,gpath,dpath):
 for p in (vpath,gpath,dpath):
  if not p.is_file():raise ValueError(f'No existe el CSV: {p}')
  if p.stat().st_size>150*1024*1024:raise ValueError(f'CSV excesivamente grande: {p}')
 tax=json.loads((ROOT/'datos/taxonomia.json').read_text(encoding='utf8'))['areas'];taxids={x['id'] for x in tax}
 if not set(TOPICS.values()).issubset(taxids):raise ValueError('Taxonomía incompatible')
 vote_rows=list(read_csv(vpath));groups_rows=list(read_csv(gpath))
 if not vote_rows or not groups_rows:raise ValueError('Faltan votaciones o grupos')
 votes={};dates={};years=collections.defaultdict(list); source_topics=collections.Counter()
 problems=[]
 for row in vote_rows:
  vid=row.get('Código','').strip();day=row.get('Fecha','').strip();title=row.get('Título','').strip()
  if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,90}',vid):problems.append('Código inesperado '+repr(vid));continue
  if vid in votes:problems.append('Votación duplicada '+vid);continue
  try:date=dt.date.fromisoformat(day)
  except ValueError:problems.append('Fecha inválida '+vid);continue
  if not (dt.date(2023,8,17)<=date<=dt.date(2026,10,6)):problems.append('Fecha fuera de XV: '+vid);continue
  if not title:problems.append('Sin título '+vid);continue
  try:nums=[int(row[k]) for k in ('Sí','No','Abstención')]
  except Exception:problems.append('Votos inválidos '+vid);continue
  if min(nums)<0 or sum(nums)>350:problems.append('Recuento no válido '+vid);continue
  for tag in row['Temas'].split('|'):source_topics[tag.strip()]+=1
  source_areas=areas(row,tax)
  votes[vid]={'id':vid,'legislatura':'XV','fecha':day,'titulo':title,'temas':row['Temas'],
      'areas':source_areas,'area_origen':'etiquetas de Congreso Abierto, con clasificación por título cuando figura «otros»; provisional',
      'tipo':'Votación del Pleno','resultado':row['Resultado'],'si':nums[0],'no':nums[1],'abstencion':nums[2],
      'no_vota':None,'url_votacion':'','fuente':'Congreso Abierto (CSV; datos elaborados desde el Congreso)',
      'calidad':('Identificador descriptivo del proveedor, no patrón sesión-voto; cotejo oficial específico pendiente. ' if not re.fullmatch(r's\d+-v\d+',vid) else '') + 'Registro del catálogo nominal del proveedor; no necesariamente la aprobación final de una ley.'}
  dates[vid]=day;years[day[:4]].append(vid)
 if problems:raise ValueError('Errores en votaciones: '+'; '.join(problems[:8]))
 groups={};totals=collections.defaultdict(lambda:[0,0,0,0]);groupnames=set()
 for r in groups_rows:
  vid=r['Votación'];name=r['Grupo'];key=(vid,name)
  if vid not in votes:problems.append('Grupo sin votación '+vid);continue
  if key in groups:problems.append('Grupo duplicado '+str(key));continue
  if r['Fecha']!=dates[vid]:problems.append('Fecha de grupo discordante '+str(key));continue
  try:n=[int(r[k]) for k in ('Sí','No','Abstención','No vota')]
  except Exception:problems.append('Valores no numéricos en '+str(key));continue
  if min(n)<0 or sum(n)>350:problems.append('Suma de grupo imposible '+str(key));continue
  position=r['Voto mayoritario']
  if not position:position='Sin voto consignado'
  groups[key]={'legislatura':'XV','votacion_id':vid,'grupo':name,'si':n[0],'no':n[1],
               'abstencion':n[2],'no_vota':n[3],'voto_mayoritario':position}
  groupnames.add(name);t=totals[vid]
  for i in range(4):t[i]+=n[i]
 if problems:raise ValueError('Errores grupos: '+'; '.join(problems[:8]))
 mismatches=[]
 for vid,t in totals.items():
  n=[votes[vid][k] for k in ('si','no','abstencion')]
  if t[:3]!=n:mismatches.append({'votacion':vid,'datos':[n,t[:3]]})
  votes[vid]['no_vota']=t[3]
 if mismatches:raise ValueError('Los totales de grupos no concilian: '+repr(mismatches[:4]))
 # Indexar nombres sin atribuir partidos; cada fila conserva grupo y voto en esa fecha.
 indexed_names={}; names=[];group_codes={};source_groups=[];nominal=collections.defaultdict(dict)
 nominal_count=0;dids=collections.Counter(); nominal_tallies=collections.defaultdict(lambda:[0,0,0,0]);nominal_groups=collections.defaultdict(lambda:[0,0,0,0]);keys_seen=set()
 dupe_nom=[];bad_nom=[]; empty=[]
 for r in read_csv(dpath):
  vid=r['Votación']; name=r['Diputado']; group=r['Grupo'];voto=r['Voto'];day=r['Fecha']
  if vid not in votes or day!=dates[vid] or not name or not group or voto not in ALLOWED:
   bad_nom.append((vid,name,group,voto));continue
  dedup=(vid,name)
  if dedup in keys_seen:dupe_nom.append(dedup);continue
  keys_seen.add(dedup)
  if name not in indexed_names:indexed_names[name]=len(names);names.append(name)
  if group not in group_codes:group_codes[group]=len(source_groups);source_groups.append(group)
  sess=vid.split('-v',1)[0] if re.fullmatch(r's\d+-v\d+',vid) else 'especiales'
  nominal[sess].setdefault(vid,[]).append([indexed_names[name],group_codes[group],ALLOWED[voto]])
  nominal_count+=1;dids[vid]+=1;nominal_tallies[vid][ALLOWED[voto]]+=1;nominal_groups[(vid,group)][ALLOWED[voto]]+=1
 if bad_nom or dupe_nom:raise ValueError(f'Anomalías nominales: inválidas={len(bad_nom)}, repetidas={len(dupe_nom)}')
 nominal_missing=sorted(set(votes)-set(dids))
 group_missing=sorted(set(votes)-set(totals))
 different_nominal_total=[];different_nominal_group=[]
 for vid,t in nominal_tallies.items():
  actual=[votes[vid][k] for k in ('si','no','abstencion')]
  if t[:3]!=actual:different_nominal_total.append({'id':vid,'general':actual,'nominal':t[:3]})
 for key,t in nominal_groups.items():
  row=groups.get(key)
  if row and t!=[row[k] for k in ('si','no','abstencion','no_vota')]:
   different_nominal_group.append({'id':key[0],'grupo':key[1],
         'grupo_csv':[row[k] for k in ('si','no','abstencion','no_vota')], 'nominal_csv':t})
 # CSV separados por año, acumulado completo listo para cargar en file://
 vd=ROOT/'datos';hist=vd/'historico';nd=vd/'nominales';hist.mkdir(parents=True,exist_ok=True);nd.mkdir(parents=True,exist_ok=True)
 packages=[]
 for y,ids in sorted(years.items()):
  objects=[votes[id] for id in sorted(ids,key=lambda id:(dates[id],id))]
  gs=[row for (vid,_),row in groups.items() if vid in set(ids)]
  gs.sort(key=lambda g:(g['votacion_id'],g['grupo']))
  pack={'legislatura':'XV','anio':y,'votaciones':objects,'grupos':gs,'partidos':[],
        'procedencia':'Congreso Abierto; CSV remitidos por el usuario; fuente original: datos del Congreso',
        'nota':'Corte de catálogo nominal del proveedor, no inventario universal. Los grupos no siempre equivalen a partidos.'}
  filename=f'XV-{y}.json';digest=write_json(hist/filename,pack)
  packages.append({'legislatura':'XV','anio':y,'ruta':'datos/historico/'+filename,
    'desde':min(dates[i] for i in ids),'hasta':max(dates[i] for i in ids),
    'registros':len(ids),'cobertura':'parcial','fuente':'Congreso Abierto, CSV descargados del catálogo',
    'sha256':digest,'ref_verificacion':''})
 manifest={'version':'0.6','paquetes':packages,
          'nota':'Catálogo XV completo SEGÚN LOS CSV aportados. No constituye inventario universal oficial del Congreso.'}
 (vd/'paquetes.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
 preload={'legislatura':'XV','votaciones':[votes[id] for y in sorted(years) for id in sorted(years[y],key=lambda id:(dates[id],id))],
     'grupos':[groups[k] for k in sorted(groups)],'partidos':[],
     'fuente':'Congreso Abierto / CSV remitidos, cotejados con los recuentos por grupo'}
 write_script(ROOT/'assets/precarga_XV.js','QHV_PRECARGA_XV',preload)
 nom_manifest={'version':'0.6','filas':nominal_count,'votaciones_con_nombres':len(dids),
    'personas_identificadas_por_nombre':len(names),'sesiones':[],'excluidos':nominal_missing,
    'nota':'Conserva cada registro individual tal como consta en el CSV. No rellena ausentes, no atribuye partidos.'}
 sessions=sorted(nominal,key=lambda x:(1,0) if x=='especiales' else (0,int(x[1:])))
 for s in sessions:
  rows=nominal[s]; sorted_data={vid:rows[vid] for vid in sorted(rows)}
  nom_path=nd/(s+'.js');digest=write_script(nom_path,'QHV_NOMINALES_SESIONES["'+s+'"]',sorted_data)
  nom_manifest['sesiones'].append({'sesion':s,'archivo':'datos/nominales/'+s+'.js',
      'votaciones':len(rows),'filas':sum(map(len,rows.values())),'sha256':digest})
 write_script(ROOT/'assets/nominal_catalog.js','QHV_NOMINALES_CATALOGO',
              {'nombres':names,'grupos':source_groups,'sentidos':list(ALLOWED),'sesiones':sessions,
               'total_filas':nominal_count,'votaciones_con_nominales':len(dids)})
 (nd/'indice.json').write_text(json.dumps(nom_manifest,ensure_ascii=False,indent=2),encoding='utf8')
 # Declaración a la que se podrá volver, nunca alterar cifras no verificadas.
 input_meta={key:{'nombre':p.name,'bytes':p.stat().st_size,'sha256':hash_bytes(p.read_bytes())} for key,p in [('votaciones',vpath),('grupos',gpath),('diputados',dpath)]}
 report={'version':'0.6','fecha_auditoria':dt.date.today().isoformat(),
 'ambito':'XV · catálogo de votaciones nominales de Congreso Abierto · periodo de los CSV recibidos',
 'url_catalogo':SRC_URL,'url_datos_primarios':OFFICIAL,
 'archivos_originales':input_meta,
 'resultado':{'votaciones':len(votes),'registros_grupo':len(groups),'registros_diputado':nominal_count,
    'fechas':[min(dates.values()),max(dates.values())],
    'votaciones_por_anio':{y:len(ids) for y,ids in sorted(years.items())},
    'votaciones_con_grupos':len(totals),'votaciones_con_nominales':len(dids),
    'grupos_distintos':sorted(groupnames),'diputados_nombres_distintos':len(names),
    'ficheros_nominales_por_sesion':len(sessions),'materias_fuente':dict(source_topics)},
 'identificadores_fuera_del_patron_sesion':[x for x in votes if not re.fullmatch(r's\d+-v\d+',x)],
 'controles':{'ids_votacion_unicos':True,'filas_grupo_unicas_por_id_y_nombre':True,
    'filas_nominales_unicas_por_id_y_nombre':True,
    'fechas_compatibles_en_tres_csv':True,'votos_por_grupo_concilian_con_totales':True,
    'discrepancias_grupos_vs_totales':len(mismatches),
    'discrepancias_nominal_vs_totales':len(different_nominal_total),
    'discrepancias_nominal_vs_grupo':len(different_nominal_group),
    'votaciones_sin_grupo':group_missing,
    'votaciones_sin_nominal':nominal_missing},
 'muestras_discrepancias':{'nominal_vs_totales':different_nominal_total[:25],
       'nominal_vs_grupo':different_nominal_group[:25]},
 'estado':'ÍNTEGRO respecto a los tres CSV aportados; cobertura oficial universal NO verificada',
 'limitaciones':[
  'El proveedor registra votaciones nominales del Pleno; no incluye necesariamente llamamientos, votaciones secretas o comisiones.',
  'Dos suplicatorios no tienen desgloses nominales ni por grupo; se conservan únicamente sus totales generales.',
  'Los datos de diputados no siempre reproducen los recuentos agregados: publicar ambos sin imputar votos ausentes.',
  'Existen identificadores legibles no homologados al patrón sesión-votación; se preservan y se marcan para cotejo documental.',
  'El CSV no contiene identificadores persistentes de diputado, candidatura, ni afiliación política; se muestra nombre y grupo, no partido inferido.',
  'No se dispone de URL oficial específica para cada fila en estos CSV; se enlaza el catálogo de procedencia y la fuente primaria general.',
  'Las categorías temáticas derivan de etiquetas amplias y de coincidencias automáticas, por lo que son provisionales.'
 ]}
 (vd/'auditoria_XV.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 status={'producto':'Qué has hecho con mi voto','version':'0.6','fecha_revision':dt.date.today().isoformat(),
    'estado':'Datos XV importados y precargados: cobertura del catálogo CSV sí; universo oficial de votaciones NO reconciliado',
    'registros_XV_precargados':len(votes),'desgloses_de_grupo_precargados':len(groups),
    'votos_nominales_precargados_bajo_demanda':nominal_count,
    'votaciones_con_desglose_grupo':len(totals),'votaciones_con_diputados':len(dids),
    'grupos_distintos':len(groupnames),'partidos_identificados':0,
    'fecha_primera':min(dates.values()),'fecha_ultima':max(dates.values()),
    'auditoria_nominal_completa':'datos/auditoria_XV.json',
    'auditoria_extracto':'datos/auditoria_extracto.json',
    'cobertura':'Completo respecto a CSV recibidos, NO respecto a inventario universal oficial',
    'fuentes':{'descarga':SRC_URL,'institucional':OFFICIAL},
    'legislaturas_en_selector':16,'legislaturas_con_datos_precargados':['XV'],
    'modo_de_ingesta':'Precarga de CSV reales para sitio sin servidor, paquetes anuales y detalle por sesión; no datos sintéticos',
    'limitacion_partidos':'Sin fichero histórico de candidaturas; los CSV solo dan grupos parlamentarios'}
 (vd/'estado_publicacion.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf8')
 print('IMPORTADO:',len(votes),'votaciones;',len(groups),'grupos;',nominal_count,'nominales;  detalles:',len(sessions),'sesiones')
 print('POR AÑO:',dict(sorted((y,len(v)) for y,v in years.items())))
 print('SIN GRUPOS/NOMINALES:',group_missing,nominal_missing)
 print('DIFERENCIAS: nominal/general',len(different_nominal_total),'nominal/grupo',len(different_nominal_group))
 print('AUDITORÍA:',vd/'auditoria_XV.json')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--votaciones',type=Path,required=True)
 p.add_argument('--grupos',type=Path,required=True)
 p.add_argument('--diputados',type=Path,required=True)
 a=p.parse_args();run(a.votaciones,a.grupos,a.diputados)
