"""Regression tests v0.8.1: tested verified & provisional links stay separate."""
from pathlib import Path
import csv,json,hashlib
from playwright.sync_api import sync_playwright
from test_v08 import load_page,local_route
R=Path(__file__).resolve().parent.parent
with (R/'datos/vinculos_XV.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f,delimiter=';'))
with (R/'datos/expedientes_propuestos_anotados_XV.csv').open(encoding='utf-8-sig',newline='') as f:proposals=list(csv.DictReader(f,delimiter=';'))
assert len(rows)==2177
assert sum(bool(r['expediente_id']) for r in rows)==50
assert len(proposals)==2127 and len({p['votacion_id'] for p in proposals})==2127
assert not {r['votacion_id'] for r in rows if r['expediente_id']} & {p['votacion_id'] for p in proposals}
assert sum(p['estado']=='VOTACION_POSIBLEMENTE_CONJUNTA' for p in proposals)==3
byid={v['votacion_id']:v for v in rows}
assert byid['s82-v003']['expediente_id']=='173/000065'
assert byid['s167-v001']['expediente_id']=='122/000257'
assert not byid['s40-v052']['expediente_id']
assert not byid['s2-v001']['expediente_id']
for x in json.loads((R/'datos/paquetes.json').read_text())['paquetes']:
 assert hashlib.sha256((R/x['ruta']).read_bytes()).hexdigest()==x['sha256']

with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--allow-file-access-from-files','--no-proxy-server'])
 for width,height in [(1400,900),(390,844)]:
  tab=b.new_page(viewport={'width':width,'height':height});errors=[];tab.on('pageerror',lambda e:errors.append(str(e)))
  tab.route('https://qhv-local.invalid/**',local_route)
  load_page(tab,'index.html')
  tab.wait_for_function('window.QHV_TEST && QHV_TEST.getState().votes===2177',timeout=25000)
  assert '2.127' in tab.locator('body').inner_text()
  tab.evaluate("QHV_TEST.showVote('XV:s82-v003')")
  txt=tab.locator('#dialogBody').inner_text();assert '173/000065' in txt and 'Asociación documental' in txt
  tab.locator('#closeDialog').click()
  tab.evaluate("QHV_TEST.showVote('XV:s2-v001')")
  txt=tab.locator('#dialogBody').inner_text();assert 'Candidato 410/000001' in txt and 'sin verificar' in txt.lower()
  assert tab.locator('#dialogBody a[href*="_iniciativas_id="]').count()==0
  tab.locator('#closeDialog').click()
  tab.evaluate("QHV_TEST.showVote('XV:s40-v052')")
  txt=tab.locator('#dialogBody').inner_text();assert 'Votación conjunta' in txt and 'no se puede asignar un expediente único' in txt
  assert tab.locator('#dialogBody a[href*="_iniciativas_id="]').count()==0
  tab.locator('#closeDialog').click()
  tab.evaluate("QHV_TEST.showVote('XV:s167-v001')")
  txt=tab.locator('#dialogBody').inner_text();assert '122/000257' in txt and 'Asociación documental' in txt
  tab.locator('#closeDialog').click()
  tab.screenshot(path=str(R/('preview_v081_escritorio.png' if width>500 else 'preview_v081_movil.png')),full_page=False)
  assert not errors,errors
  tab.close()
 b.close()
print('PASS v081: 50 enlaces cotejados; 2127 candidatos provisional; 3 conjuntos señalados; vista escritorio/móvil; integridad manifiesto')
