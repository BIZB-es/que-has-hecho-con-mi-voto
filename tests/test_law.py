"""The housing case displays documented numerical series on desktop and mobile."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import re
root=Path(__file__).resolve().parent.parent
html=(root/'ley-vivienda.html').read_text(encoding='utf8')
html=re.sub(r'<script[^>]*src="[^"]+"[^>]*></script>','',html)
html=re.sub(r'<link[^>]*stylesheet[^>]*>','',html)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium',args=['--no-sandbox','--no-proxy-server'])
 for name,w,h in [('vivienda_desktop',1440,900),('vivienda_mobile',390,844)]:
  page=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
  errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html,wait_until='domcontentloaded')
  for c in ['styles.css','leyes.css']:page.add_style_tag(path=str(root/'assets'/c))
  for f in ['indicadores.js','leyes.js']:page.add_script_tag(path=str(root/'assets'/f))
  page.wait_for_timeout(200)
  assert not errors,errors
  assert '12.858' in page.locator('#metricNum-protegidas').inner_text()
  assert '2025' in page.locator('#plainReading').inner_text()
  assert page.locator('#metricTable tr').count()==8
  assert page.locator('svg#seriesChart circle').count()==8
  page.locator('#metric-emancipacion').click()
  assert '14,5' in page.locator('#metricNum-emancipacion').inner_text()
  assert page.locator('#metricTable tr').count()==7
  assert 'segundo semestre' in page.locator('#metricFrequency').inner_text().lower()
  page.locator('#rangeStart').select_option('2022')
  assert page.locator('svg#seriesChart circle').count()==4
  page.locator('#metric-protegidas').click()
  assert page.locator('#metricTable tr').count()==8
  assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+2'), 'Horizontal scrolling'
  page.screenshot(path=str(root/f'preview_{name}.png'),full_page=True)
  print('PASS',name, 'series verified; browser errors',errors)
  page.close()
 browser.close()
