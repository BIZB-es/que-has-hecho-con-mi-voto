#!/usr/bin/env python3
"""Valida el inventario de publicación 0.8, sin necesidad de tener CSV originales."""
import csv, hashlib, json, re
from pathlib import Path
P=Path(__file__).resolve().parent.parent
j=lambda f:json.loads((P/f).read_text(encoding='utf-8-sig'))
p=j('datos/calidad_XV.json');q=j('datos/paquetes.json');x=j('datos/estado_publicacion.json');ll=j('datos/llamamientos_2026.json')
assert len(ll['registros'])==2 and all(v['fecha']=='2026-10-02' for v in ll['registros'])
assert p['recuentos_csv']['votaciones']==2175
assert p['calidad']['filas_que_cuadran_grupos']==2173
assert p['calidad']['votaciones_con_nominal_incompleto']==2078
assert p['calidad']['votaciones_con_nominal_exacto']==95
assert p['calidad']['votaciones_sin_nominal']==2
assert x['registros_XV_precargados']==2177
assert sum(i['registros'] for i in q['paquetes'])==2177
n=0;exp=0;ids=set();extra=0
for a in q['paquetes']:
 b=(P/a['ruta']).read_bytes();assert hashlib.sha256(b).hexdigest()==a['sha256']
 rows=json.loads(b)['votaciones'];assert len(rows)==a['registros']
 for v in rows:
  assert v['id'] not in ids;ids.add(v['id'])
  assert v['fecha'][:4]==a['anio']
  assert all(isinstance(v[k],int) for k in ['si','no','abstencion','no_vota'])
  exp+=bool(v.get('expediente') and v.get('url_expediente'))
  extra+=v['id'].startswith('s203-ll')
 n+=len(rows)
assert n==2177 and extra==2 and exp==30
with open(P/'datos/incidencias_nominales_XV.csv',encoding='utf-8-sig',newline='') as f:
 rows=list(csv.DictReader(f,delimiter=';'));assert len(rows)==2080
with open(P/'datos/vinculos_XV.csv',encoding='utf-8-sig',newline='') as f:
 links=list(csv.DictReader(f,delimiter=';'));assert len(links)==2177
print('OK v0.8: 2.177 registros, 30 expedientes, 2.080 incidencias nominales documentadas, 4 paquetes integros.')
