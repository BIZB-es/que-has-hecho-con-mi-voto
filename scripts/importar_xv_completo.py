#!/usr/bin/env python3
"""Importador reproducible XV: descubre descargas publicadas o usa CSV originales.

Dos mecanismos excluyentes:
  python scripts/importar_xv_completo.py --descubrir
  python scripts/importar_xv_completo.py --votaciones archivo.csv --grupos archivo.csv

El programa no atribuye votos ni inventa resultados. Publica paquetes anuales
solo tras la auditoria y nunca anuncia una cobertura oficial no conciliada.
"""
from __future__ import annotations
import argparse, csv, io, json, hashlib, os, re, subprocess, sys, tempfile, urllib.parse, urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANDING = 'https://congresoabierto.org/datos/'
REFERENCE = {'votaciones': 2175, 'grupos': 19561, 'nominales': 726564}
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; QHV-Congreso/0.5; public data ingestion)', 'Accept': 'text/html,text/csv,application/csv,text/plain,*/*'}
MAX_BYTES = 90 * 1024 * 1024

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._current = None
    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            self._current = {'href': dict(attrs).get('href',''), 'text': ''}
    def handle_data(self, data):
        if self._current is not None:
            self._current['text'] += data
    def handle_endtag(self, tag):
        if tag.lower() == 'a' and self._current is not None:
            self.links.append(self._current)
            self._current = None

def fetch(url, limit=MAX_BYTES):
    p = urllib.parse.urlparse(url)
    if p.scheme != 'https' or p.hostname not in ('congresoabierto.org', 'www.congresoabierto.org', 'raw.githubusercontent.com'):
        raise ValueError('Origen externo no autorizado: '+url)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=45) as r:
        data = r.read(limit+1)
        if len(data) > limit: raise ValueError('Descarga demasiado grande: '+url)
        return data

def sniff_header(payload):
    if payload[:500].lstrip().lower().startswith((b'<!doctype', b'<html', b'{"error"')):return []
    sample = payload[:8192].decode('utf-8-sig',errors='replace')
    line = sample.splitlines()[0] if sample.splitlines() else ''
    try:return [h.strip().lower() for h in next(csv.reader(io.StringIO(line), delimiter=(';' if line.count(';')>line.count(',') else ',')))]
    except Exception:return []

def kind_of(payload):
    h=set(sniff_header(payload))
    if {'id','fecha','titulo','si','no'}.issubset(h):return 'votaciones'
    if {'votacion_id','grupo','si','no'}.issubset(h):return 'grupos'
    if {'votacion_id','diputado_id','voto'}.issubset(h):return 'nominales'
    if {'id','partido','fecha_alta'}.issubset(h):return 'candidaturas'
    return ''

def extract_candidates(html, root=LANDING):
    links=Links();links.feed(html)
    candidates=[]
    for l in links.links:
        u=urllib.parse.urljoin(root,l['href'])
        if u.startswith(('https://congresoabierto.org/','https://www.congresoabierto.org/')):
            hint=(l['href']+' '+l['text']).lower()
            if ('csv' in hint or 'descarg' in hint or 'downloa' in hint) and ('vot' in hint or 'datos' in hint or 'export' in hint):
                candidates.append(u)
    candidates += [
        'https://congresoabierto.org/datos/csv/votaciones.csv',
        'https://congresoabierto.org/datos/csv/votos-grupo.csv',
        'https://congresoabierto.org/datos/csv/votos-diputado.csv',
        'https://congresoabierto.org/datos/votaciones.csv',
        'https://congresoabierto.org/datos/votos-grupo.csv',
        'https://congresoabierto.org/api/datos/votaciones.csv',
        'https://congresoabierto.org/api/datos/votos-grupo.csv',
    ]
    # The candidate URLs are hypotheses, never evidence: the schema is verified
    # after HTTP download. Failed URLs are not represented as valid.
    return list(dict.fromkeys(candidates))

def discover(target, html_override=None):
    print('Inspeccionando catálogo de descargas:',LANDING)
    html = html_override if html_override is not None else fetch(LANDING, 5*1024*1024).decode('utf-8','replace')
    candidates=extract_candidates(html)
    sources={}; failures=[]
    for u in candidates:
        if len(sources)>=2:break
        try:
            payload=fetch(u)
            k=kind_of(payload)
            if k not in ('votaciones','grupos') or k in sources:continue
            # A preview, selected filter or login page must never pass as a full export.
            f=target/(k+'.csv');f.parent.mkdir(exist_ok=True,parents=True);f.write_bytes(payload)
            sources[k]={'url':u,'path':str(f),'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()}
            print('Tabla identificada:',k,'en',u,'bytes',len(payload))
        except Exception as e:failures.append(f'{u}: {type(e).__name__}: {e}')
    return sources,failures

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--descubrir',action='store_true',help='Descubrir los CSV del catálogo de Congreso Abierto')
    a.add_argument('--votaciones',type=Path)
    a.add_argument('--grupos',type=Path)
    a.add_argument('--nominales',type=Path)
    a.add_argument('--candidaturas',type=Path)
    a.add_argument('--min-votaciones',type=int,default=REFERENCE['votaciones'])
    a.add_argument('--min-grupos',type=int,default=REFERENCE['grupos'])
    o=a.parse_args()
    if not o.descubrir and not (o.votaciones and o.grupos):a.error('Indica --descubrir o los dos CSV (--votaciones y --grupos)')
    if o.descubrir and (o.votaciones or o.grupos):a.error('No combines --descubrir y CSV locales')
    if bool(o.nominales)!=bool(o.candidaturas):a.error('Para atribuir candidaturas se precisan nominales y censo fechado')
    target=ROOT/'importaciones'
    if o.descubrir:
        try:sources,failures=discover(target)
        except Exception as e:raise SystemExit('ERROR: No se pudo consultar el catálogo de origen: '+str(e))
        if 'votaciones' not in sources or 'grupos' not in sources:
            print('Candidatas probadas sin CSV completo: ',*failures[-8:],sep='\n  ',file=sys.stderr)
            raise SystemExit('ERROR: No hay dos descargas CSV válidas identificadas. Abre '+LANDING+' y descarga las tablas Votaciones y Voto de cada grupo; pasa sus rutas con --votaciones y --grupos.')
        v=Path(sources['votaciones']['path']);g=Path(sources['grupos']['path'])
    else:
        v=o.votaciones;g=o.grupos
        for k,p in (('votaciones',v),('grupos',g)):
            if not p.exists():raise SystemExit('ERROR: Archivo no disponible: '+str(p))
            identified=kind_of(p.read_bytes()[:16384])
            if identified!=k:raise SystemExit(f'ERROR: {p} no es un CSV compatible de {k}; identificado: {identified}')
        sources={k:{'url':'archivo local aportado','path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in (('votaciones',v),('grupos',g))}
    cmd=[sys.executable,str(ROOT/'scripts/sincronizar_xv.py'),'--votaciones',str(v),'--grupos',str(g),'--min-votos',str(o.min_votaciones),'--min-grupos',str(o.min_grupos)]
    if o.nominales:cmd.extend(['--nominales',str(o.nominales),'--candidaturas',str(o.candidaturas)])
    proc=subprocess.run(cmd)
    if proc.returncode:raise SystemExit(proc.returncode)
    audit=ROOT/'datos/auditoria_XV.json';report=json.loads(audit.read_text())
    report['descargas']={k:{z:s[z] for z in ('url','bytes','sha256')} for k,s in sources.items()}
    # 100% of the THIRD-PARTY CSV tables, not 100% of every official recorded vote.
    report['cobertura_del_catalogo_congresoabierto']=('coincidente con referencia publicada' if report['num_votaciones']>=REFERENCE['votaciones'] and report['num_filas_grupo']>=REFERENCE['grupos'] else 'no alcanza referencia publicada')
    audit.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    state=ROOT/'datos/estado_publicacion.json';s=json.loads(state.read_text())
    s.update({'version':'0.5','estado':'Paquetes nominales XV incorporados; cotejo oficial de todos los procedimientos pendiente',
              'registros_XV_precargados':report['num_votaciones'],'desgloses_de_grupo_precargados':report['num_filas_grupo'],
              'auditoria_nominal_completa':'datos/auditoria_XV.json','modo_de_ingesta':'CSV completos con auditoria; paquetes anuales precargados y consultables por periodo',
              'aviso': 'La base nominal de Congreso Abierto no incluye necesariamente llamadas, votos secretos, comisiones ni todos los acuerdos.'})
    state.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf8')
    print('\nIMPORTACIÓN NOMINAL COMPLETADA: {} votaciones, {} filas de grupo.'.format(report['num_votaciones'],report['num_filas_grupo']))
    print('Paquetes anuales listos: datos/paquetes.json. Alcance oficial: parcial hasta conciliacion documental.')

if __name__=='__main__':main()
