from pathlib import Path
from textwrap import dedent
root=Path(__file__).resolve().parent.parent
js=root/'assets/app.js';s=js.read_text(encoding='utf-8')
def rep(old,new):
 global s
 n=s.count(old)
 if n!=1:raise ValueError(f'Replacement count {n}: {old[:85]}')
 s=s.replace(old,new)
rep('''let linkFile=v.url_expediente?`<a href="${C.esc(safeLink(v.url_expediente))}" target="_blank" rel="noopener">Expediente parlamentario ↗</a>`:'';''',
'''let linkFile=v.url_expediente?`<a href="${C.esc(safeLink(v.url_expediente))}" target="_blank" rel="noopener noreferrer">Expediente ${C.esc(v.expediente||'')} ↗</a>`:`<span class="missing-source">Expediente aún sin asociación verificada. <a href="https://www.congreso.es/es/busqueda-de-iniciativas" target="_blank" rel="noopener noreferrer">Buscador oficial de iniciativas ↗</a></span>`;''')
rep('''<p class="alert-line">${C.esc(C.effect(v))}</p><h3>Materias</h3>''',
'''<p class="alert-line">${C.esc(C.effect(v))}</p><div class="exp-file"><strong>Expediente:</strong> ${v.expediente?`<span class="file-ref">${C.esc(v.expediente)}</span><small>Asociación documental: ${C.esc(v.expediente_fuente||'enlace de la exportación')}</small>`:'<span class="muted">No identificado en los CSV</span><small>No confundas el enlace al registro de voto con el expediente de tramitación.</small>'}</div><h3>Materias</h3>''')
rep('''const rows=raw.map(x=>({name:names[x[0]]||'Sin nombre',group:g[x[1]]||'',vote:s[x[2]]||''})).sort((a,b)=>a.name.localeCompare(b.name,'es'));''',
'''const profiles=window.QHV_IDENTIDADES_XV?.por_nombre||{};
  const rows=raw.map(x=>{const name=names[x[0]]||'Sin nombre',p=profiles[name]||null,grupoCsv=g[x[1]]||'';
   const marco=p?.grupos_verificados?.find(t=>v.fecha>=t.desde && (!t.hasta_exclusiva||v.fecha<t.hasta_exclusiva));
   const cambio=p?.fecha_cambio_pendiente===v.fecha;
   return {name,id:p?.codigo||'',url:p?.url_ficha||'',group:marco?marco.grupo:grupoCsv,groupCsv:grupoCsv,
     grupoFuente:marco?'Grupo histórico contrastado':cambio?'Fecha de cambio: revisar':'Grupo consignado en CSV (sin control histórico)',
     formacion:p?.formacion_ficha||'',vote:s[x[2]]||''};
  }).sort((a,b)=>a.name.localeCompare(b.name,'es'));''')
rep('''<input type="search" id="nominalSearch" placeholder="Nombre o grupo parlamentario" autocomplete="off"><p class="fine-print" id="nominalCount"></p><div id="nominalList" class="table-scroll"></div><p class="fine-print">Transcripción del CSV nominal del proveedor. Puede haber diferencias con los totales generales: <a href="datos/auditoria_XV.json" target="_blank" rel="noopener">ver auditoría</a>. No se atribuyen ausencias ni partidos por deducción.</p>''',
'''<input type="search" id="nominalSearch" placeholder="Nombre, código, grupo o formación" autocomplete="off"><p class="fine-print" id="nominalCount"></p><div id="nominalList" class="table-scroll"></div><p class="fine-print">Los códigos identifican a la persona en el Congreso. La formación electoral no siempre equivale a su partido. Las etiquetas de grupo del CSV individual no incorporan un historial de cambios; únicamente se rectifican en casos cotejados con la ficha oficial. <a href="datos/auditoria_v07.json" target="_blank" rel="noopener">Ver auditoría</a>.</p>''')
rep('''C.clean(x.name+' '+x.group+' '+x.vote).includes(q)''',
'''C.clean(x.name+' '+x.id+' '+x.group+' '+x.groupCsv+' '+x.formacion+' '+x.vote).includes(q)''')
rep('''<table class="detail-table nominal-table"><thead><tr><th>Diputado</th><th>Grupo</th><th>Voto consignado</th></tr></thead><tbody>${filtered.map(x=>`<tr><td>${C.esc(x.name)}</td><td>${C.esc(x.group)}</td><td><b>${C.esc(x.vote)}</b></td></tr>`).join('')}</tbody></table>''',
'''<table class="detail-table nominal-table"><thead><tr><th>Diputado y ficha</th><th>Grupo</th><th>Formación en ficha oficial</th><th>Voto consignado</th></tr></thead><tbody>${filtered.map(x=>`<tr><td>${x.url?`<a href="${C.esc(safeLink(x.url))}" target="_blank" rel="noopener noreferrer">${C.esc(x.name)} ↗</a>`:C.esc(x.name)}${x.id?`<small>Código ${C.esc(x.id)} · XV</small>`:''}</td><td>${C.esc(x.group)}<small>${C.esc(x.grupoFuente)}</small>${x.groupCsv&&x.groupCsv!==x.group?`<small>El CSV indicaba: ${C.esc(x.groupCsv)}</small>`:''}</td><td>${x.formacion?C.esc(x.formacion):'<span class="muted">Sin contrastar</span>'}</td><td><b>${C.esc(x.vote)}</b></td></tr>`).join('')}</tbody></table>''')
rep('''// Los CSV no proporcionan identificador persistente de partido: el grupo solo es una etiqueta parlamentaria.''',
'''// La exportacion nueva SI proporciona ID parlamentario, pero NO partido ni historial completo de grupo.
// La correccion de grupo solo se muestra para las fechas respaldadas por ficha oficial.''')
rep('''El Grupo Mixto puede contener varias formaciones. Estos totales son los publicados por el proveedor, no calculados a partir de las fichas individuales.''',
'''El Grupo Mixto puede contener varias formaciones. Estos totales son los publicados por el proveedor, no calculados a partir de las fichas individuales. A diferencia de la etiqueta individual del CSV, el agregado por grupos refleja el resultado registrado para cada votación.''')
js.write_text(s,encoding='utf-8')

# Menus, resumen y carga de nuevo diccionario de identidad
idx=root/'index.html';h=idx.read_text(encoding='utf-8')
h=h.replace('<a href="argumentos.html">Argumentos</a>','<a href="diputados.html">Diputados</a><a href="argumentos.html">Argumentos</a>')
h=h.replace('Los tres archivos aportados se han integrado y auditado.',
'''Los CSV de votos y el censo están relacionados. Los 350 diputados del fichero nominal tienen código parlamentario y enlace a su ficha oficial. Solo 28 expedientes están vinculados directamente; los otros 2.147 están pendientes de recuperar desde las sesiones oficiales.''')
h=h.replace('No se atribuyen partidos a partir del grupo.',
'''No se atribuyen partidos a partir del grupo. <a href="diputados.html">Consultar el censo histórico de 412 personas</a> y <a href="datos/auditoria_v07.json">auditoría v0.7</a>.''')
h=h.replace('Estos tres archivos', 'Estos archivos')
h=h.replace('versión 0.6', 'versión 0.7')
h=h.replace('<script src="assets/nominal_catalog.js"></script><script src="assets/precarga_XV.js"></script>',
'''<script src="assets/nominal_catalog.js"></script><script src="assets/identidades_XV.js"></script><script src="assets/precarga_XV.js"></script>''')
h=h.replace('Estos tres CSV', 'Los CSV')
h=h.replace('Los tres archivos aportados se han integrado', 'Los archivos aportados se han integrado')
h=h.replace('Se muestran todos los grupos presentes en los datos importados. Para ver partidos o candidaturas por separado, necesitamos también votos nominales y su atribución identificable a la fecha correspondiente.',
'''Se muestran todos los grupos presentes en los datos. Los códigos oficiales identifican a los 350 diputados del CSV, pero partido, coalición y grupo son conceptos diferentes. Los cambios de grupo solo se rectifican cuando la ficha histórica lo acredita. <a href="diputados.html">Ver el censo</a>.''')
idx.write_text(h,encoding='utf-8')
for title in ['argumentos.html','ley-vivienda.html','votaciones.html']:
 p=root/title; html=p.read_text(encoding='utf-8')
 if 'href="diputados.html"' not in html:
  html=html.replace('<a href="argumentos.html"', '<a href="diputados.html">Diputados</a><a href="argumentos.html"',1)
 p.write_text(html,encoding='utf-8')

# Estilo para fichas oficiales y la nueva pagina de censo.
css=root/'assets/styles.css';st=css.read_text(encoding='utf-8')+'''
/* Identificadores y trazabilidad de expedientes, version 0.7 */
.exp-file{padding:12px 14px;background:#edf4f5;border:1px solid #d3e3e7;border-radius:9px;margin:16px 0}
.exp-file small{display:block;color:var(--muted);font-size:12px;margin-top:4px}
.file-ref{font-weight:750;margin-left:7px}
.missing-source{font-size:13px;color:var(--muted)}
.nominal-table td small{display:block;font-size:11px;color:#58707c;margin-top:4px}
.nominal-table th{vertical-align:top}
.muted{color:#6e818c}
.census-hero{background:#102d41;color:white;padding:35px 0}
.census-hero h1{font-size:clamp(25px,4vw,42px);line-height:1.1;letter-spacing:-.045em;margin:9px 0}
.census-hero p{color:#d0e1e4;max-width:720px}
.census-controls{background:#fff;border:1px solid var(--line);border-radius:13px;padding:18px;margin:24px 0;display:flex;gap:14px;flex-wrap:wrap}
.census-controls label{display:flex;flex-direction:column;gap:4px;font-size:13px;font-weight:700;flex:1 1 220px}
.census-controls input,.census-controls select{padding:10px;border:1px solid #b6c9cf;border-radius:8px;min-height:44px;max-width:100%}
.census-entries{display:grid;grid-template-columns:repeat(auto-fill,minmax(245px,1fr));gap:12px}
.census-card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px;min-height:126px}
.census-card h3{font-size:16px;margin-bottom:8px}
.census-card p{font-size:12px;color:var(--muted);margin:5px 0}
.census-card .card-link{display:inline-block;margin-top:6px;font-size:12px;font-weight:650}
.census-empty{padding:28px;background:white;border:1px solid var(--line);border-radius:9px}
.census-stats{display:flex;gap:15px;flex-wrap:wrap;margin:18px 0}
.census-stats>div{background:white;border:1px solid var(--line);padding:12px 17px;border-radius:9px;min-width:145px}
.census-stats b{display:block;font-size:24px;color:var(--deep)}.census-stats span{font-size:12px;color:var(--muted)}
.census-footer{padding:24px 0;color:var(--muted);font-size:12px}
'''
css.write_text(st,encoding='utf-8')
print('Updated JS / HTML / styles')
