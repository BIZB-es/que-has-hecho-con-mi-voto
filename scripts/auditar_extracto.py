#!/usr/bin/env python3
"""Audit the bundled hand-checked EXCERPT, not the full official legislature."""
import json,datetime,sys,collections
from pathlib import Path
root=Path(__file__).resolve().parent.parent
path=root/'datos/muestra.json';seed=json.loads(path.read_text(encoding='utf8'))
v=seed.get('votaciones',[]);g=seed.get('grupos',[]);ids=set();errors=[];issues=[]
for row in v:
 k=row.get('id','');date=row.get('fecha','')
 if not k or k in ids:errors.append('ID vacio o duplicado '+k)
 ids.add(k)
 try:
  d=datetime.date.fromisoformat(date)
  if not datetime.date(2023,8,17)<=d<=datetime.date(2026,10,6):errors.append('Fecha fuera de XV '+k)
 except Exception:errors.append('Fecha invalida '+k)
 numbers=[row.get(i) for i in ('si','no','abstencion')]
 if any(not isinstance(n,int) or n<0 for n in numbers):errors.append('Totales no numericos '+k)
 elif sum(numbers)>350:errors.append('Totales >350 '+k)
 if not row.get('url_votacion','').startswith('https://www.congreso.es/'):errors.append('Sin enlace Congreso '+k)
 if row.get('resultado') not in ('Aprobada','Rechazada','Derogada'):
  issues.append('Resultado no usual: '+k)
keyset=set();group_by=collections.Counter()
for row in g:
 k=row.get('votacion_id','');party=row.get('grupo','')
 if k not in ids:errors.append('Posicion sin votacion '+k)
 if (k,party) in keyset:errors.append('Posicion duplicada '+k+' '+party)
 keyset.add((k,party));group_by[k]+=1
 if sum(row.get(x,0) for x in ('si','no','abstencion','no_vota'))>350:errors.append('Grupo > 350 '+k)
try:
 info=json.loads((root/'datos/indicadores_vivienda.json').read_text())
 for m in info['indicadores']:
  years=[p[0] for p in m['serie']]
  if len(years)!=len(set(years)) or years!=sorted(years):errors.append('Serie no ordenada '+m['id'])
except Exception as e:errors.append('Indicadores no disponibles '+str(e))
report={'version':'0.4','fecha_revision':'2026-10-26','estado':'EXTRACTO NO EXHAUSTIVO - pendiente de ingestiones masivas',
 'ambito':'XV 2023-2026, exclusivamente registros ilustrativos transcritos del Congreso y dos llamamientos',
 'votaciones_muestra':len(v),'desgloses_grupo_muestra':len(g),'votaciones_con_desglose_grupo':len(group_by),
 'num_partidos_con_desglose':0,'num_paquetes_historicos_precargados':len(json.loads((root/'datos/paquetes.json').read_text())['paquetes']),
 'series_indicadores':len(info['indicadores']),'errores_integridad':errors,'advertencias':issues+[
 'La muestra NO constituye todos los registros XV. Titulos de extractos 2026 resumidos editorialmente.',
 'Las ocho posiciones por grupo corresponden a una sola votacion. No representan las posiciones en las 46 votaciones.',
 'No hay identidad temporal de diputados/candidaturas integrada: no se infieren votos de partidos.',
 'El total publico 2175 corresponde al CSV de votos nominales de Congreso Abierto, no al inventario universal.',
 'Existe un inventario alternativo con 2187 registros; falta reconciliar diferencias y no nominales.',
 'Las series de vivienda son descriptivas y necesitan cotejo automatico del archivo primario antes de la publicacion definitiva.',
 'El ano 2023 del indicador anual incluye meses antes y despues de la entrada en vigor en mayo.'] ,
 'fuentes':['https://www.congreso.es/es/opendata/votaciones','https://congresoabierto.org/datos/',
 'https://www.boe.es/buscar/act.php?id=BOE-A-2023-12203',
 'https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP005_01.csv',
 'https://www.cje.org/observatorio-de-emancipacion/'],
 'control_minimo_produccion':'Verificacion de todas las sesiones oficiales, identificadores nominales, recusaciones/llamamientos, expediente juridico, metadatos de representantes y version de series.'}
(root/'datos/auditoria_extracto.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Audit excerpt:',len(v),'votes;',len(g),'group rows; errors',len(errors))
if errors:raise SystemExit('\n'.join(errors))
