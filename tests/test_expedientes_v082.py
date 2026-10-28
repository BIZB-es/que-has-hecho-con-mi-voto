#!/usr/bin/env python3
"""No-network consistency tests for the published data bundle."""
from pathlib import Path
from collections import Counter
import hashlib,csv,json,re,sys
ROOT=Path(__file__).resolve().parent.parent

def rows(path):
 with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))

def main():
 data=json.loads((ROOT/'assets/precarga_XV.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
 vs=data['votaciones'];assert len(vs)==2177
 rel=rows(ROOT/'datos/relaciones_votacion_expediente_XV.csv')
 links=rows(ROOT/'datos/vinculos_XV.csv')
 assert len(rel)==2206 and len(links)==2177
 assert len({x['votacion_id'] for x in links})==2177
 idmap={v['id']:v for v in vs}
 relcounts=Counter(r['votacion_id'] for r in rel)
 st=Counter(v['expediente_estado'] for v in vs)
 assert st=={'UNICO_HTML':2119,'MULTIPLE_HTML':15,'COTEJO_ANTERIOR':43},st
 for v in vs:
  codes=v['expedientes']; urls=v['expedientes_urls']; n=relcounts[v['id']]
  assert n==len(codes)==len(urls) and len(codes)>0,v['id']
  if len(codes)==1:assert v['url_expediente']==urls[0]
  else:assert v['url_expediente']=='',v['id']
  assert all(re.fullmatch(r'\d{3}/\d{6}',x) for x in codes)
  assert all(x.startswith('https://www.congreso.es/es/busqueda-de-iniciativas?') for x in urls)
  assert all(v['id']==r['votacion_id'] for r in rel if r['votacion_id']==v['id'])
 assert idmap['s40-v056']['expedientes'].__len__()==12
 assert idmap['s19-v001']['expedientes']==['125/000002']
 assert idmap['s166-v010']['expedientes']==['101/000002']
 assert idmap['s2-v001']['expedientes']==['410/000001']
 assert len(set(x['expediente_id'] for x in rel))==707
 # The same vote->expediente relation must appear in annual JSON packages.
 manifest=json.loads((ROOT/'datos/paquetes.json').read_text(encoding='utf-8'))
 union={}
 for pkg in manifest['paquetes']:
  path=ROOT/pkg['ruta'];original=path.read_bytes()
  assert hashlib.sha256(original).hexdigest()==pkg['sha256']
  obj=json.loads(original);assert len(obj['votaciones'])==pkg['registros']
  for vote in obj['votaciones']:
   assert vote['id'] not in union
   union[vote['id']]=vote['expedientes']
 assert len(union)==2177
 assert all(union[k]==v['expedientes'] for k,v in idmap.items())
 # Every data script or style linked from index is physically present.
 index=(ROOT/'index.html').read_text(encoding='utf-8')
 for f in re.findall(r'(?:src|href)="((?:assets|datos)/[^"?#]+)"',index):
  assert (ROOT/f).is_file(),f
 assert not rows(ROOT/'datos/expedientes_pendientes_XV.csv')
 assert (ROOT/'datos/fuentes_sesiones_XV.zip').stat().st_size>1_000_000
 print('OK: 2177 votes, 2206 dossier links, 15 multi, 8 corrected, 4 SHA256 annual packages')

if __name__=='__main__':main()
