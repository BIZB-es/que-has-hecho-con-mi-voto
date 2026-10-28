#!/usr/bin/env python3
"""Mejoras de transparencia, enlaces y cobertura de la v0.8."""
from pathlib import Path
import re
R=Path(__file__).resolve().parent.parent
p=R/'assets/app.js'
s=p.read_text(encoding='utf-8')
# Dates and coverage
s=s.replace("dateFrom:'2023-09-19',dateTo:'2026-09-30'","dateFrom:'2023-09-19',dateTo:'2026-10-02'")
s=s.replace("status:'Íntegro respecto a los tres CSV recibidos (no equivale a todas las votaciones oficiales)'","status:'2.175 registros CSV y 2 por llamamiento (no incluye todos los votos de comisiones)'")
s=s.replace("<strong>${F(votes.size)} votaciones cargadas.</strong> ${window.QHV_PRECARGA_XV?'Catálogo nominal de la XV integrado desde los tres CSV. 2 votaciones sin desglose por grupo o diputado. <a href=\"datos/auditoria_XV.json\" target=\"_blank\" rel=\"noopener\">Auditoría completa</a>. No incluye necesariamente todas las votaciones oficiales.'","<strong>${F(votes.size)} votaciones documentadas.</strong> ${window.QHV_PRECARGA_XV?'2.175 registros del CSV y 2 por llamamiento (02/10/2026). Los votos individuales tienen lagunas en 2.078 votaciones. <a href=\"calidad.html\">Ver auditoría y cobertura</a>. No cubre necesariamente todas las votaciones oficiales.'")
# link to daily session for votes without expte
old="`<span class=\"missing-source\">Expediente aún sin asociación verificada. <a href=\"https://www.congreso.es/es/busqueda-de-iniciativas\" target=\"_blank\" rel=\"noopener noreferrer\">Buscador oficial de iniciativas ↗</a></span>`;"
new="`<span class=\"missing-source\">Expediente pendiente de vinculación. <a href=\"${C.esc('https://www.congreso.es/es/opendata/votaciones?targetLegislatura=XV&targetDate='+encodeURIComponent(v.fecha.slice(8,10)+'/'+v.fecha.slice(5,7)+'/'+v.fecha.slice(0,4)))}\" target=\"_blank\" rel=\"noopener noreferrer\">Ver sesión oficial del día ↗</a></span>`;"
assert old in s,'No se ha localizado bloque de expedientes sin vinculo';s=s.replace(old,new)
needle="let linkFile=v.url_expediente?"
assert needle in s
# add audit status in showVote after vote URL
needle="$('dialogBody').innerHTML=`<div class=\"kicker dark\">Legislatura"
assert needle in s
inject="""const quality=window.QHV_CALIDAD_XV?.por_voto?.[v.id],extra=v.id.startsWith('s203-ll');
let qualityNote='';
if(extra)qualityNote='<p class="data-quality note">Votación por llamamiento: resultado documentado mediante el BOE y la sesión oficial. <strong>No hay desglose nominal ni por grupos en los CSV recibidos</strong>. Los totales proceden de una crónica periodística citada en el informe de fuentes.</p>';
else if(quality){const [state,missing,ds,dn,da,dnv,available]=quality;
 if(state==='coincide')qualityNote='<p class="data-quality good">El número de votos individuales consignados coincide con los totales publicados para esta votación. No implica que las etiquetas históricas de grupo estén comprobadas.</p>';
 else if(state==='sin_nominal')qualityNote='<p class="data-quality note">No hay desglose individual en el CSV de origen para esta votación. Solo pueden consultarse los totales publicados.</p>';
 else if(state==='incompleto')qualityNote='<p class="data-quality note"><strong>Votos individuales incompletos:</strong> se conservan '+F(available)+' registros, mientras que el total publicado es '+F(available+missing)+'. Diferencia: '+F(missing)+' registros (sí: '+F(ds)+', no: '+F(dn)+', abstención: '+F(da)+', no vota: '+F(dnv)+'). <strong>No se imputa a ningún diputado un voto ausente.</strong></p>';
 else qualityNote='<p class="data-quality note">Existe una discrepancia en el registro individual. Consulta la auditoría antes de interpretar estos votos.</p>';
}
"""
s=s.replace(needle,inject+needle)
s=s.replace("</div></div><h3>¿Qué se estaba votando?</h3>","</div></div>${qualityNote}<h3>¿Qué se estaba votando?</h3>")
# extra 2-October as no-nominal
s=s.replace("['s89-v005','s202-v021'].includes(v.id)","(['s89-v005','s202-v021'].includes(v.id)||extra)")
s=s.replace("Este registro no tiene votos individuales en el CSV aportado. Solo consta el resultado agregado.","No hay votos individuales publicados en los archivos recibidos para esta votación. Consulta las fuentes para su naturaleza y resultado.")
# audit page link near sources
s=s.replace("<h3>Fuentes</h3><div class=\"detail-links\">","<h3>Fuentes</h3><div class=\"detail-links\"><a href=\"calidad.html\">Auditoría de cobertura ↗</a>")
# link official session for everything
s=s.replace(" <a href=\"https://www.congreso.es/es/opendata/votaciones\" target=\"_blank\" rel=\"noopener\">Archivo del Congreso ↗</a></div>"," <a href=\"https://www.congreso.es/es/opendata/votaciones\" target=\"_blank\" rel=\"noopener\">Archivo del Congreso ↗</a></div>")
p.write_text(s,encoding='utf-8')
# simple edits HTML
p=R/'index.html';s=p.read_text(encoding='utf-8')
s=s.replace('<a href="diputados.html">Diputados</a><a href="argumentos.html">', '<a href="diputados.html">Diputados</a><a href="calidad.html">Calidad de datos</a><a href="argumentos.html">')
s=s.replace('2.175 votaciones, 19.561 desgloses por grupo y 726.564 registros de diputados', '2.177 registros (2.175 del CSV y 2 por llamamiento), 19.561 desgloses por grupo y 726.564 filas nominales')
s=s.replace('Solo 28 expedientes están vinculados directamente; los otros 2.147 están pendientes', 'Hay 30 expedientes enlazados, incluidos dos por llamamiento; los otros 2.147 del CSV están pendientes')
s=s.replace('La XV Legislatura ya está incorporada.', 'La XV Legislatura está incorporada, incluidos los dos llamamientos de octubre de 2026.')
s=s.replace('sus 2.175 registros','sus 2.177 registros')
s=s.replace('Solo 28 expedientes', 'Solo 30 expedientes')
s=s.replace('las 2.175 registros','los 2.177 registros')
s=s.replace('Los códigos oficiales identifican a los 350 diputados', 'Los códigos oficiales identifican a los 350 diputados')
s=s.replace('y <a href="datos/auditoria_v07.json">auditoría de identificadores y expedientes</a>', 'y <a href="calidad.html">auditoría de integridad individual y por grupos</a>')
s=s.replace('Los 350 diputados del fichero nominal tienen código parlamentario y enlace a su ficha oficial.', 'Los 350 diputados del fichero nominal tienen código parlamentario y enlace a su ficha oficial. Los registros individuales contienen lagunas significativas y requieren una comprobación de cobertura. <a href="calidad.html">Consultar calidad de los datos</a>.')
s=s.replace('No se atribuyen partidos a partir del grupo.', 'No se atribuyen partidos a partir del grupo; los datos nominales incompletos no deben interpretarse como ausencias parlamentarias.')
s=s.replace('</section>\n  <section class="law-promo"', '</section>\n  <section class="law-promo"')
s=s.replace('<script src="assets/precarga_XV.js"></script><script src="assets/app.js"></script>', '<script src="assets/precarga_XV.js"></script><script src="assets/calidad_XV.js"></script><script src="assets/app.js"></script>')
p.write_text(s,encoding='utf-8')
# navigation across other pages
for filename in ('diputados.html','argumentos.html','ley-vivienda.html'):
 p=R/filename;t=p.read_text(encoding='utf-8')
 if '<a href="calidad.html">Calidad de datos</a>' not in t:
  t=t.replace('<a href="diputados.html">Diputados</a>', '<a href="diputados.html">Diputados</a><a href="calidad.html">Calidad de datos</a>')
  t=t.replace('<a href="diputados.html" class="on" aria-current="page">Diputados</a>', '<a href="diputados.html" class="on" aria-current="page">Diputados</a><a href="calidad.html">Calidad de datos</a>')
 t=t.replace('versión 0.7','versión 0.8').replace('Solo se han asociado directamente 28 expedientes.','Se han asociado 30 expedientes (28 de los CSV y 2 por llamamiento).')
 p.write_text(t,encoding='utf-8')
p=R/'assets/styles.css';t=p.read_text(encoding='utf-8')
t+='''\n/* v0.8: avisos de integridad visibles en ficha */\n.data-quality{line-height:1.55;padding:13px 15px;border:1px solid #d4e4e8;border-left:4px solid #39839a;border-radius:9px;background:#eff7f8;color:#1e4b58;margin:16px 0}\n.data-quality.good{background:#edf7ef;color:#245e43;border-color:#cae0d1;border-left-color:#278461}\n.data-quality.note{background:#fff8e9;color:#664b1e;border-color:#f0dfbc;border-left-color:#cb9141}\n@media(max-width:780px){.data-quality{font-size:13px}}\n'''
p.write_text(t,encoding='utf-8')
print('UI v08 updated')
