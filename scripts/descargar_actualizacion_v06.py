#!/usr/bin/env python3
"""Descarga tres CSV verificados (manual) y regenera la publicación v0.6."""
import argparse,subprocess,sys,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
MAX_BYTES=90*1024*1024
ALLOWED={'congresoabierto.org','www.congresoabierto.org'}
p=argparse.ArgumentParser(description=__doc__)
for k in ('votaciones','grupos','diputados'):p.add_argument('--url-'+k,required=True)
a=p.parse_args()
folder=ROOT/'importaciones';folder.mkdir(exist_ok=True)
paths={}
for k in ('votaciones','grupos','diputados'):
 url=getattr(a,'url_'+k);u=urllib.parse.urlparse(url)
 if u.scheme!='https' or u.hostname not in ALLOWED:
  raise SystemExit('Solo se admiten descargas HTTPS desde Congreso Abierto: '+k)
 req=urllib.request.Request(url,headers={'User-Agent':'QHV/0.6; public open data importer','Accept':'text/csv,text/plain,*/*'})
 with urllib.request.urlopen(req,timeout=80) as response:
  data=response.read(MAX_BYTES+1)
 if len(data)>MAX_BYTES or data[:256].lstrip().lower().startswith((b'<!doctype',b'<html')):
  raise SystemExit('No es un fichero CSV válido o es demasiado grande: '+k)
 out=folder/(k+'.csv');out.write_bytes(data);paths[k]=out
command=[sys.executable,str(ROOT/'scripts/integrar_csv_congreso_abierto.py')]
for k in ('votaciones','grupos','diputados'):command+=['--'+k,str(paths[k])]
subprocess.run(command,check=True)
subprocess.run([sys.executable,str(ROOT/'scripts/verificar_importacion_v06.py')],check=True)
print('Actualización terminada: comparar auditoría antes de publicar')
