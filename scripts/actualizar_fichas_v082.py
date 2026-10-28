#!/usr/bin/env python3
"""Update offline UI to render all official expediente links, including joint votes."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
app=ROOT/'assets/app.js';text=app.read_text(encoding='utf-8')
core=ROOT/'assets/core.js';basic=core.read_text(encoding='utf-8')
old="    expediente:String(v.expediente||''),expediente_fuente:String(v.expediente_fuente||''),si,no,abstencion,no_vota,resultado:String(v.resultado||v.estado||'No confirmado'),"
new="    expediente:String(v.expediente||''),expedientes:Array.isArray(v.expedientes)?v.expedientes.map(String):(v.expediente?[String(v.expediente)]:[]),expedientes_urls:Array.isArray(v.expedientes_urls)?v.expedientes_urls.map(String):[],expediente_fuente:String(v.expediente_fuente||''),expediente_estado:String(v.expediente_estado||''),expediente_fuente_html:String(v.expediente_fuente_html||''),url_sesion_evidencia:String(v.url_sesion_evidencia||''),si,no,abstencion,no_vota,resultado:String(v.resultado||v.estado||'No confirmado'),"
assert old in basic
core.write_text(basic.replace(old,new),encoding='utf-8')

start=text.index('const candidate=window.QHV_PROPUESTAS_EXP_XV?.[v.id];')
stop=text.index('const quality=window.QHV_CALIDAD_XV?',start)
sub='''const codes=Array.isArray(v.expedientes)?v.expedientes:[];
const sourceSession=v.url_sesion_evidencia||'https://www.congreso.es/es/opendata/votaciones?targetLegislatura=XV&targetDate='+encodeURIComponent(v.fecha.slice(8,10)+'/'+v.fecha.slice(5,7)+'/'+v.fecha.slice(0,4));
const recordLink=(id,index)=>v.expedientes_urls?.[index]||'https://www.congreso.es/es/busqueda-de-iniciativas?p_p_id=iniciativas&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_iniciativas_mode=mostrarDetalle&_iniciativas_legislatura=XV&_iniciativas_id='+encodeURIComponent(id);
const expList=codes.map((id,i)=>`<li><a href="${C.esc(safeLink(recordLink(id,i)))}" target="_blank" rel="noopener noreferrer">Expediente ${C.esc(id)} &#8599;</a></li>`).join('');
const joint=codes.length>1;
const expStatus=v.expediente_estado==='COTEJO_ANTERIOR'?'Cotejo documental de versiones anteriores':v.expediente_estado==='MULTIPLE_HTML'?'Varios expedientes en el mismo bloque oficial':v.expediente_estado==='UNICO_HTML'?'Cotejo con HTML de la sesi\u00f3n, JSON y recuentos':'Asociaci\u00f3n pendiente de revisar';
const expNotice=codes.length?`<div class="exp-evidence"><p><strong>${joint?'Esta votaci\u00f3n afecta a '+codes.length+' expedientes.':'Expediente asociado a esta votaci\u00f3n.'}</strong> ${C.esc(expStatus)}.</p><ul class="exp-records">${expList}</ul><p class="fine-print">Fuente: <a href="${C.esc(safeLink(sourceSession))}" target="_blank" rel="noopener noreferrer">listado de la sesi\u00f3n del Congreso &#8599;</a> · <a href="datos/auditoria_expedientes_v082.json" target="_blank" rel="noopener noreferrer">auditor\u00eda de la asociaci\u00f3n &#8599;</a>. Los HTML archivados tienen manifiesto SHA-256; no sustituyen la comprobaci\u00f3n de vigencia de los enlaces.</p></div>`:
`<span class="missing-source">No se ha identificado un expediente en los datos disponibles. <a href="${C.esc(safeLink(sourceSession))}" target="_blank" rel="noopener noreferrer">Consultar sesi\u00f3n &#8599;</a></span>`;
const linkFile=codes.length?`<a href="${C.esc(safeLink(sourceSession))}" target="_blank" rel="noopener noreferrer">Sesi\u00f3n y expedientes &#8599;</a>`:expNotice;
'''
text=text[:start]+sub+text[stop:]
# Replace the older file block that could present a single ambiguous candidate.
start=text.index('<div class="exp-file"><strong>Expediente:</strong>')
stop=text.index('<h3>Materias</h3>',start)
text=text[:start]+'<div class="exp-file">${expNotice}</div>'+text[stop:]
# Search/export all expediente IDs rather than only first.
text=text.replace("'url_votacion','url_expediente'];let data=filtered.map", "'url_votacion','expediente','expediente_estado','url_sesion_evidencia','url_expediente'];let data=filtered.map")
app.write_text(text,encoding='utf-8')

css=ROOT/'assets/styles.css'
css.write_text(css.read_text(encoding='utf-8')+'''\n/* V0.8.2: one voting decision may correspond to several parliamentary files. */\n.exp-evidence p{margin:5px 0 11px}\n.exp-records{margin:8px 0 13px;padding-left:19px;max-height:235px;overflow-y:auto;line-height:1.65}\n.exp-records li{margin-bottom:5px;overflow-wrap:anywhere}\n.exp-records a{color:#075a74;text-decoration:underline}\n''',encoding='utf-8')

index=ROOT/'index.html';html=index.read_text(encoding='utf-8')
start=html.index('<div class="import-howto">')
stop=html.index('</div>',start)+len('</div>')
html=html[:start]+'''<div class="import-howto"><h3>La XV Legislatura ya est\u00e1 cargada: no tienes que importar nada</h3><p>Dispones de 2.177 votaciones del cat\u00e1logo recibido y sus registros de voto. Ahora se relacionan con 2.206 expedientes (relaciones votaci\u00f3n-expediente), porque <strong>15 votaciones afectan a varios expedientes</strong>. De las votaciones, 2.134 se han cotejado con 139 p\u00e1ginas HTML oficiales archivadas, y 43 conservan un cotejo anterior por fuentes oficiales. Las fichas permiten abrir los expedientes y consultar la sesi\u00f3n correspondiente. <a href="datos/auditoria_expedientes_v082.json">Ver auditor\u00eda de expedientes</a>.</p><p class="fine-print">Los votos individuales contienen lagunas en muchas votaciones. No confundas resultados totales, votos nominales individuales y afiliaci\u00f3n a partidos: los grupos parlamentarios no equivalen necesariamente a partidos. <a href="calidad.html">Auditor\u00eda nominal</a> · <a href="datos/relaciones_votacion_expediente_XV.csv" download>Descargar relaciones votaci\u00f3n-expediente</a> · <a href="diputados.html">Censo XV de diputados</a>. El alcance sigue limitado al inventario de votaciones de este proyecto; no incluye todas las legislaturas ni todas las votaciones en comisi\u00f3n.</p></div>'''+html[stop:]
html=html.replace('0.8.1','0.8.2')
index.write_text(html,encoding='utf-8')

quality=ROOT/'calidad.html';q=quality.read_text(encoding='utf-8')
needle='<section class="qa-card"><h2>Descargar la evidencia</h2>'
new_section='''<section class="qa-card"><h2>Relaci\u00f3n entre votaciones y expedientes</h2><p>En el inventario actual, <strong>2.134 votaciones</strong> tienen el enlace al expediente cotejado mediante el HTML de su sesi\u00f3n (URL JSON y recuentos coincidentes). <strong>43 m\u00e1s</strong> conservan un cotejo documental anterior, no incluido en el ZIP de HTML recibido. Hay <strong>15 votaciones</strong> con varios expedientes y 8 propuestas antiguas corregidas.</p><p>Esta cobertura se refiere a las <strong>2.177 votaciones cargadas</strong>, no al conjunto completo de todas las legislaturas ni a cada tr\u00e1mite en comisi\u00f3n. La vinculaci\u00f3n de expedientes no resuelve las discrepancias del voto individual.</p><div class="qa-links"><a href="datos/relaciones_votacion_expediente_XV.csv" download>Relaciones comprobadas (CSV)</a><a href="datos/auditoria_expedientes_v082.json" target="_blank" rel="noopener">Auditor\u00eda de expedientes (JSON)</a><a href="datos/fuentes_sesiones_XV.zip" download>P\u00e1ginas HTML fuente (ZIP + SHA-256)</a></div></section>\n'''
assert needle in q
q=q.replace(needle,new_section+needle).replace('VERSI\u00d3N 0.8','VERSI\u00d3N 0.8.2')
quality.write_text(q,encoding='utf-8')
print('Core, app, index, quality and styles updated')
