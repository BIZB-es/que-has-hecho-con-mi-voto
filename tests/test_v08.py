"""Prueba visual y funcional de v0.8. Sin fuentes remotas ni datos ficticios."""
from pathlib import Path
import re
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent
URL='https://qhv-local.invalid/'

def load_page(page,filename):
 content=(ROOT/filename).read_text(encoding='utf8')
 scripts=re.findall(r'<script[^>]*src="([^"]+)"[^>]*></script>',content)
 content=re.sub(r'<script[^>]*src="[^"]+"[^>]*></script>','',content)
 content=re.sub(r'<link[^>]*stylesheet[^>]*>','',content)
 content=content.replace('<head>','<head><base href="'+URL+'">',1)
 page.set_content(content,wait_until='domcontentloaded')
 page.add_style_tag(path=str(ROOT/'assets/styles.css'))
 for src in scripts:page.add_script_tag(path=str(ROOT/src))

def local_route(route):
 rel=route.request.url.split('qhv-local.invalid/',1)[-1].split('?',1)[0]
 f=ROOT/rel
 if f.is_file() and str(f.resolve()).startswith(str(ROOT.resolve())):
  route.fulfill(body=f.read_bytes(),content_type='application/javascript' if f.suffix=='.js' else 'application/json' if f.suffix=='.json' else 'text/html')
 else:route.fulfill(status=404,body='no file')


def test():
 with sync_playwright() as p:
  br=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--allow-file-access-from-files','--no-proxy-server'])
  tab=br.new_page(viewport={'width':1440,'height':900});errors=[];tab.on('pageerror',lambda e:errors.append(str(e)))
  tab.route('https://qhv-local.invalid/**',local_route)
  load_page(tab,'index.html')
  tab.wait_for_function('window.QHV_TEST && QHV_TEST.getState().votes === 2177',timeout=25000)
  assert tab.locator('#mVotes').inner_text()=='2.177'
  assert tab.locator('#datasetStatus').inner_text().find('2.078')>=0
  assert tab.locator('nav a[href="calidad.html"]').count()==1
  # Sesión del 2 de octubre: sin reconstrucción nominal
  tab.evaluate("QHV_TEST.showVote('XV:s203-ll002')")
  txt=tab.locator('#dialogBody').inner_text()
  assert '184' in txt and '166' in txt
  assert 'Votación por llamamiento' in txt
  assert tab.locator('#cargarDiputados').count()==0
  assert tab.locator('#dialogBody a[href*="130/000056"]').count()==1
  tab.locator('#closeDialog').click()
  # Incompleta: 1 voto individual menos en una votación de septiembre 2026
  tab.evaluate("QHV_TEST.showVote('XV:s196-v021')")
  txt=tab.locator('#dialogBody').inner_text()
  assert 'Votos individuales incompletos' in txt and 'Diferencia: 1 registros' in txt
  tab.locator('#cargarDiputados').click()
  tab.wait_for_function("document.querySelector('#nominalCount') && document.querySelector('#nominalCount').textContent.includes('349')",timeout=18000)
  tab.locator('#closeDialog').click()
  # Coincidencia exacta en una de las 95
  tab.evaluate("QHV_TEST.showVote('XV:s202-v020')")
  assert 'coincide con los totales' in tab.locator('#dialogBody').inner_text()
  tab.locator('#closeDialog').click()
  # Enlace contextual a sesión oficial para expediente pendiente
  tab.evaluate("QHV_TEST.showVote('XV:s2-v001')")
  assert tab.locator('#dialogBody a[href*="targetDate=19%2F09%2F2023"]').count()==1
  tab.locator('#closeDialog').click()
  tab.screenshot(path=str(ROOT/'preview_v08_escritorio.png'),full_page=False)
  assert not errors,errors
  # Página de calidad y filtros
  load_page(tab,'calidad.html')
  tab.wait_for_function("document.querySelector('#qaCount') && document.querySelector('#qaCount').textContent.includes('2.177')",timeout=15000)
  for state,count in [('coincide','95'),('incompleto','2.078'),('sin_nominal','2'),('por_llamamiento','2')]:
   tab.locator('#qaEstado').select_option(state)
   assert count in tab.locator('#qaCount').inner_text(),(state,tab.locator('#qaCount').inner_text())
  tab.locator('#qaEstado').select_option('todos')
  tab.locator('#qaBuscar').fill('s202-v020')
  assert '1 registros' in tab.locator('#qaCount').inner_text()
  tab.screenshot(path=str(ROOT/'preview_v08_calidad.png'),full_page=False)
  assert not errors,errors
  mob=br.new_page(viewport={'width':390,'height':844});err=[];mob.on('pageerror',lambda e:err.append(str(e)))
  mob.route('https://qhv-local.invalid/**',local_route)
  load_page(mob,'index.html')
  mob.wait_for_function('window.QHV_TEST && QHV_TEST.getState().votes === 2177',timeout=20000)
  mob.screenshot(path=str(ROOT/'preview_v08_movil.png'),full_page=False)
  mob.evaluate("QHV_TEST.showVote('XV:s203-ll001')")
  assert 'por llamamiento' in mob.locator('#dialogBody').inner_text().lower()
  load_page(mob,'calidad.html')
  mob.screenshot(path=str(ROOT/'preview_v08_calidad_movil.png'),full_page=False)
  assert not err,err
  br.close()
 print('OK browser v08: 2177, llamamientos, avisos de nominales, fuente de sesion, filtros de calidad y móvil.')
if __name__=='__main__':test()
