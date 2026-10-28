#!/usr/bin/env python3
r"""Archiva HTML originales de sesiones XV sin interpretar expedientes.

Permite una auditoria posterior independiente de las asociaciones propuestas.
Es respetuoso con la fuente: sin concurrencia, ~1.3 s entre peticiones,
reintentos limitados, reutiliza descargas previas y permite reanudar.

Windows PowerShell (desde la carpeta del proyecto):
  py scripts\guardar_sesiones_fuente_v081.py --limite 3
  py scripts\guardar_sesiones_fuente_v081.py
Resultado: fuentes_sesiones_XV.zip, con HTML y manifest CSV.
"""
import argparse,csv,hashlib,time,urllib.request,urllib.error,zipfile,sys,ssl
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DAT=ROOT/'datos/expedientes_propuestos_anotados_XV.csv'
AGENT='Mozilla/5.0 (compatible; ProyectoObservatorio/0.8; verificacion documental de datos publicos)'

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--limite',type=int,default=0,help='Numero maximo de fechas nuevas a descargar (0 = todas)')
 p.add_argument('--desde',default='');p.add_argument('--hasta',default='')
 p.add_argument('--destino',default='fuentes_sesiones_XV')
 a=p.parse_args();dest=ROOT/a.destino;dest.mkdir(exist_ok=True,parents=True)
 with DAT.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f,delimiter=';'))
 dates=sorted(set(r['fecha'] for r in rows if r['fecha'] and (not a.desde or r['fecha']>=a.desde) and (not a.hasta or r['fecha']<=a.hasta)))
 count=0;failures=[]
 for date in dates:
  target=dest/(date+'.html');url='https://www.congreso.es/es/opendata/votaciones?targetLegislatura=XV&targetDate='+date[8:10]+'%2F'+date[5:7]+'%2F'+date[:4]
  if target.exists() and target.stat().st_size>1500:continue
  if a.limite and count>=a.limite:break
  count+=1
  try:
   req=urllib.request.Request(url,headers={'User-Agent':AGENT,'Accept':'text/html,application/xhtml+xml','Accept-Language':'es-ES,es;q=0.9'})
   with urllib.request.urlopen(req,timeout=25,context=ssl.create_default_context()) as response:
    if response.status!=200:raise RuntimeError('HTTP '+str(response.status))
    content=response.read(8_000_000)
   txt=content.decode('utf-8',errors='replace').lower()
   if len(content)<1500 or 'votacion' not in txt and 'votaci' not in txt or date[8:10] not in txt:
    raise RuntimeError('No parece una página de votaciones de la fecha solicitada (se conserva solo si es válida)')
   target.write_bytes(content)
   print('OK',date,len(content),'bytes')
  except KeyboardInterrupt:
   print('Interrumpido por usuario: se conservará lo ya descargado.');break
  except Exception as err:
   failures.append((date,str(err)))
   print('ERROR',date,str(err)[:140])
  time.sleep(1.3)
 manifest=[]
 for date in dates:
  fn=dest/(date+'.html')
  if fn.exists() and fn.stat().st_size>1500:
   content=fn.read_bytes()
   manifest.append({'fecha':date,'archivo':fn.name,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
 met=dest/'manifest.csv'
 with met.open('w',encoding='utf-8-sig',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=['fecha','archivo','bytes','sha256'],delimiter=';');wr.writeheader();wr.writerows(manifest)
 zipped=ROOT/'fuentes_sesiones_XV.zip'
 with zipfile.ZipFile(zipped,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
  z.write(met,arcname='manifest.csv')
  for r in manifest:z.write(dest/r['archivo'],arcname=r['archivo'])
 print('Guardadas',len(manifest),'de',len(dates),'sesiones. Archivo ZIP:',zipped)
 if failures:print('Errores:','; '.join(dt+': '+msg[:60] for dt,msg in failures))
 if len(manifest)<len(dates):print('La descarga no está completa: se puede reanudar con el mismo comando.')

if __name__=='__main__':main()
