"""Bloquea una publicación publicitada como nominalmente completa sin datos reales."""
import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent.parent
m=json.loads((root/'datos/paquetes.json').read_text())
p=[x for x in m['paquetes'] if x['legislatura']=='XV']
if sum(x['registros'] for x in p)<2175:raise SystemExit('Faltan votaciones nominales XV en los paquetes anuales')
if len(p)<3:raise SystemExit('Se esperan paquetes de distintos años de la XV')
ids=set()
for e in p:
 f=root/e['ruta']
 if not f.exists():raise SystemExit('Falta archivo '+e['ruta'])
 raw=f.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=e['sha256']:raise SystemExit('Hash erróneo '+e['ruta'])
 d=json.loads(raw)
 if len(d['votaciones'])!=e['registros']:raise SystemExit('Recuento erróneo '+e['ruta'])
 for v in d['votaciones']:
  k=('XV',v['id']);
  if k in ids:raise SystemExit('Votación duplicada '+str(k))
  ids.add(k)
r=json.loads((root/'datos/auditoria_XV.json').read_text())
if r['num_votaciones']!=len(ids) or r.get('errores'):raise SystemExit('Auditoría discordante con paquetes')
print('OK:',len(ids),'votaciones XV en',len(p),'paquetes; SHA-256 correctos')
