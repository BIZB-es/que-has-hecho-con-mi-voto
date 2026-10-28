#!/usr/bin/env python3
"""Extrae CANDIDATOS de expediente de listados oficiales de sesiones XV.

Por defecto NO edita la web: genera CSV de candidaturas revisables.
Una asociación verificable necesita 1) URL JSON idéntica al CSV, 2) sumas
Sí/No/Abstención idénticas y 3) número de expediente explícito en sesión.

Modo normal (red requerida):
  python scripts/proponer_expedientes_v08.py --limite-sesiones 10
Modo sin red, con HTML descargados del Congreso (1 fichero por fecha):
  python scripts/proponer_expedientes_v08.py --html-dir /ruta/sesiones
La falta de red no modifica los datos publicados.
"""
import argparse, csv, hashlib, re, ssl, time, unicodedata, urllib.request
from collections import defaultdict, Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parent.parent
SOURCE='https://www.congreso.es/es/opendata/votaciones'
R_EXP=re.compile(r'\b(\d{3}/\d{6})\b')
R_VOTE=re.compile(r'Sesion0*(\d+)/\d{8}/Votacion0*(\d+)/[^"\s?#]+\.json',re.I)
R_TALLY={'si':re.compile(r'^s[ií]\s*[:.]\s*(\d+)',re.I),'no':re.compile(r'^no\s*[:.]\s*(\d+)',re.I),'abstencion':re.compile(r'^abstenciones?\s*[:.]\s*(\d+)',re.I)}

class Parser(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.events=[];self.script_depth=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'):self.script_depth+=1
  if tag=='a' and not self.script_depth:
   href=dict(attrs).get('href','')
   if R_VOTE.search(href):self.events.append(('json',urljoin(SOURCE,href)))
 def handle_endtag(self,tag):
  if tag in ('script','style') and self.script_depth:self.script_depth-=1
 def handle_data(self,datum):
  if not self.script_depth:
   txt=' '.join(datum.split())
   if txt:self.events.append(('txt',txt))

def parse_html(content):
 parser=Parser();parser.feed(content)
 current_exp='';tallies={};last=[];out=[]
 for kind,value in parser.events:
  if kind=='txt':
   last.append(value);last=last[-7:]
   look=' '.join(last)
   exp=R_EXP.search(look)
   if exp and re.search(r'(?:n[uú]m\.?\s*)?exp(?:ediente|te)\.?',look,re.I):
    current_exp=exp.group(1)
   for field,reg in R_TALLY.items():
    m=reg.match(value)
    if m:tallies[field]=int(m.group(1))
  else:
   m=R_VOTE.search(value)
   if not m:continue
   out.append({'sesion':str(int(m.group(1))),'numero':str(int(m.group(2))),'url_votacion':value,'expediente':current_exp,
    'si':tallies.get('si'), 'no':tallies.get('no'),'abstencion':tallies.get('abstencion')})
   tallies={}
 return out

def url_session(date):return SOURCE+'?targetLegislatura=XV&targetDate='+date[8:10]+'%2F'+date[5:7]+'%2F'+date[:4]

def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (public academic audit; contact via site)'})
 with urllib.request.urlopen(req,timeout=18,context=ssl.create_default_context()) as resp:
  data=resp.read(4_000_000)
 return data.decode('utf-8',errors='replace')

def main():
 pa=argparse.ArgumentParser();pa.add_argument('--html-dir',type=Path);pa.add_argument('--limite-sesiones',type=int,default=0);pa.add_argument('--desde');pa.add_argument('--hasta');pa.add_argument('--out',type=Path,default=ROOT/'datos/expedientes_propuestos_v08.csv')
 args=pa.parse_args()
 source={};sess=defaultdict(list)
 with open(ROOT/'datos/votaciones_referencia_XV.csv',encoding='utf-8-sig',newline='') as f:
  reference={v['id']:v for v in csv.DictReader(f,delimiter=';')}
 with open(ROOT/'datos/vinculos_XV.csv',encoding='utf-8-sig',newline='') as f:
  for x in csv.DictReader(f,delimiter=';'):
   if x['votacion_id'].startswith('s203-ll'):continue
   source[x['votacion_id']]=x
   m=re.match(r's(\d+)-v(\d+)',x['votacion_id'])
   if m:key=(str(int(m.group(1))),x['fecha'])
   else:
    # los 7 alias editoriales no siguen el formato; cotejar por URL oficial
    match=R_VOTE.search(x['url_votacion'])
    if not match:continue
    key=(str(int(match.group(1))),x['fecha'])
   sess[key].append(x)
 covered=0;wrote=[];queries=0
 for (session,fecha),rows in sorted(sess.items(),key=lambda x:x[0][1]):
  if args.desde and fecha<args.desde or args.hasta and fecha>args.hasta:continue
  if all(x['expediente_id'] for x in rows):continue
  if args.limite_sesiones and queries>=args.limite_sesiones:break
  if args.html_dir:
   file=args.html_dir/(fecha+'.html')
   if not file.exists():continue
   content=file.read_text(encoding='utf-8',errors='replace')
  else:
   try:content=fetch(url_session(fecha))
   except Exception as e:
    print('ERROR descarga',fecha,str(e)[:120]);continue
   time.sleep(.4)
  queries+=1
  official=parse_html(content);byurl={x['url_votacion'].lower():x for x in official}
  for row in rows:
   if row['expediente_id']:continue
   a=byurl.get(row['url_votacion'].lower());
   if not a:continue
   # Cotejar los recuentos con la exportación original, además de la URL JSON
   if not a['expediente']:continue
   original=reference.get(row['votacion_id'])
   if not original or any(a[k]!=int(original[k]) for k in ('si','no','abstencion')):continue
   wrote.append({'votacion_id':row['votacion_id'],'fecha':fecha,'url_sesion':url_session(fecha),'expediente_candidato':a['expediente'],'url_votacion':row['url_votacion'], 'metodo':'URL JSON idéntica + cifras Sí/No/Abstención idénticas + expediente visible en listado oficial; requiere revisión antes de publicar'})
   covered+=1
 print('Sesiones leídas',queries,'candidatos preliminares',covered)
 if wrote:
  with open(args.out,'w',encoding='utf-8-sig',newline='') as f:
   wr=csv.DictWriter(f,fieldnames=list(wrote[0]),delimiter=';');wr.writeheader();wr.writerows(wrote)
  print('Propuestas guardadas en',args.out)
 else:print('Ninguna asociación añadida. Archivo publicado permanece intacto.')

if __name__=='__main__':main()
