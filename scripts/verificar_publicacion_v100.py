#!/usr/bin/env python3
"""Controles reproducibles de coherencia para la candidata publica 1.00.

No certifica la validez externa de cada estadistica ni reemplaza la revision editorial.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parent.parent


def get(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        k='href' if tag in ('a','link') else 'src' if tag in ('script','img') else None
        if k and d.get(k):self.links.append(d[k])


metrics=get('datos/indicadores_espana_v1.json')
assert metrics['publication']=='No publicado'
assert len(metrics['metrics'])==9
assert sum(bool(m['variants']) for m in metrics['metrics'])==8
assert len({m['id'] for m in metrics['metrics']})==9
for m in metrics['metrics']:
    for k in m.get('sourceKeys',[]): assert k in metrics['sources']
    for v in m['variants']:
        assert v['labels'] and v['lines'] and v['unit'] and v['note']
        assert len(v['labels'])==len(set(v['labels']))
        for l in v['lines']:
            assert len(l['values'])==len(v['labels'])
            assert all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in l['values'])
        for k in v.get('sourceKeys',[]): assert k in metrics['sources']

manifest=get('datos/paquetes.json')
ids=set(); vote_count=0
for p in manifest['paquetes']:
    data=(ROOT/p['ruta']).read_bytes()
    assert hashlib.sha256(data).hexdigest()==p['sha256'],p['ruta']
    rows=json.loads(data)['votaciones']
    assert len(rows)==p['registros']
    for r in rows:
        k=r['id'];assert k not in ids;k and ids.add(k)
    vote_count+=len(rows)
assert vote_count==2177

with (ROOT/'datos/relaciones_votacion_expediente_XV.csv').open(encoding='utf-8-sig',newline='') as f:
    rows=list(csv.DictReader(f,delimiter=';'))
assert len(rows)==2206, len(rows)
assert len({r['votacion_id'] for r in rows})==2177
assert all(r['votacion_id'] in ids and r['expediente_id'] for r in rows)

all_html=list(ROOT.glob('*.html'))
assert len(all_html)>=7
broken=[]
for html in all_html:
    p=Links();p.feed(html.read_text(encoding='utf-8'))
    for url in p.links:
        if url.startswith(('http:','https:','mailto:','tel:','#','data:','javascript:')): continue
        target=unquote(urlsplit(url).path)
        if target and not (ROOT/target).exists():broken.append((html.name,url))
assert not broken,broken
assert 'assets/precarga_XV.js' not in (ROOT/'index.html').read_text(encoding='utf-8')
assert 'assets/precarga_XV.js' in (ROOT/'congreso.html').read_text(encoding='utf-8')
assert 'proyecto.html' in (ROOT/'index.html').read_text(encoding='utf-8')
print(f'OK v1.00 RC: {len(metrics["metrics"])} bloques (8 con serie), {vote_count} votaciones, {len(rows)} relaciones de expediente y {len(all_html)} paginas HTML; enlaces locales integros.')
