#!/usr/bin/env python3
"""Verifica que los paquetes de publicación concuerden con la auditoría XV."""
import collections,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
B=lambda p:(ROOT/p).read_bytes()
J=lambda p:json.loads(B(p))
report=J('datos/auditoria_XV.json');manifest=J('datos/paquetes.json');idx=J('datos/nominales/indice.json')
assert report['version']=='0.6' and idx['version']=='0.6'
want=report['resultado']
assert len(manifest['paquetes'])==4 and all(p['legislatura']=='XV' for p in manifest['paquetes'])
count_votes=count_groups=0;all_ids=set();all_groups=set();bad=[]
for p in manifest['paquetes']:
 path=p['ruta'];assert hashlib.sha256(B(path)).hexdigest()==p['sha256'],path
 data=J(path);assert data['legislatura']=='XV' and data['anio']==p['anio']
 assert len(data['votaciones'])==p['registros'] and data['partidos']==[]
 votes={v['id']:v for v in data['votaciones']};assert len(votes)==len(data['votaciones'])
 for vid,v in votes.items():
  assert vid not in all_ids
  assert v['fecha'][:4]==p['anio'] and v['id']==vid
  all_ids.add(vid)
 tally=collections.defaultdict(lambda:[0,0,0,0])
 for g in data['grupos']:
  vid=g['votacion_id'];assert vid in votes
  k=(vid,g['grupo']);assert k not in all_groups;all_groups.add(k)
  for i,key in enumerate(('si','no','abstencion','no_vota')):tally[vid][i]+=g[key]
 for vid,t in tally.items():
  v=votes[vid]
  assert t==[v[k] for k in ('si','no','abstencion','no_vota')],vid
 count_votes+=len(votes);count_groups+=len(data['grupos'])
 assert p['cobertura']=='parcial'
assert count_votes==want['votaciones']+2 and count_groups==want['registros_grupo']
assert len(all_groups)==count_groups
num_session=num_deputies=0
for s in idx['sesiones']:
 assert hashlib.sha256(B(s['archivo'])).hexdigest()==s['sha256'],s['archivo']
 content=B(s['archivo']).decode('utf8')
 prefix='window.QHV_NOMINALES_SESIONES["'+s['sesion']+'"]='
 assert content.startswith(prefix) and content.endswith(';\n')
 entries=json.loads(content[len(prefix):-2])
 assert len(entries)==s['votaciones']
 for vid,details in entries.items():
  assert vid in all_ids and len(details)<=350
  assert all(len(row)==3 for row in details)
 num_session+=len(entries);num_deputies+=sum(map(len,entries.values()))
assert num_session==want['votaciones_con_nominales']
assert num_deputies==want['registros_diputado']==idx['filas']
assert len(idx['excluidos'])==want['votaciones']-want['votaciones_con_nominales']
assert 'window.QHV_PRECARGA_XV=' in B('assets/precarga_XV.js').decode('utf8')[:60]
print('OK: 2.175 registros CSV + 2 por llamamiento; 19.561 filas de grupo; 726.564 nominales, 4 años,')
print('   ',len(idx['sesiones']),'archivos por sesión; huellas, totales y claves comprobados.')
