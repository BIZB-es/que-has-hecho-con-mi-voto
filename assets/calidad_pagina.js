(function(){'use strict';
const data=window.QHV_PRECARGA_XV?.votaciones||[],qual=window.QHV_CALIDAD_XV?.por_voto||{};
const $=x=>document.getElementById(x);
const clean=x=>String(x??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>new Intl.NumberFormat('de-DE').format(n||0);
const pageSize=15;let page=1,matching=[];
const sessionUrl=v=>v.id.startsWith('s203-ll')?v.url_votacion:'https://www.congreso.es/es/opendata/votaciones?targetLegislatura=XV&targetDate='+encodeURIComponent(v.fecha.slice(8,10)+'/'+v.fecha.slice(5,7)+'/'+v.fecha.slice(0,4));
function stateOf(v){return v.id.startsWith('s203-ll')?'por_llamamiento':qual[v.id]?.[0]||'sin_nominal'}
function label(s){return {coincide:'El nominal cuadra',incompleto:'Individual incompleto',sin_nominal:'Sin nominal',por_llamamiento:'Por llamamiento',contradictorio:'Datos contradictorios'}[s]||s}
function filter(){const q=clean($('qaBuscar').value),a=$('qaAno').value,s=$('qaEstado').value;
 matching=data.filter(v=>(!a||v.fecha.startsWith(a))&&(s==='todos'||stateOf(v)===s)&&(!q||clean(v.id+' '+v.fecha+' '+v.titulo).includes(q))).sort((a,b)=>b.fecha.localeCompare(a.fecha)||b.id.localeCompare(a.id));page=1;render()}
function render(){const max=Math.ceil(matching.length/pageSize)||1;page=Math.max(1,Math.min(max,page));$('qaCount').textContent=fmt(matching.length)+' registros encontrados';$('qaPage').textContent='Página '+fmt(page)+' de '+fmt(max);$('qaPrev').disabled=page===1;$('qaNext').disabled=page===max;
$('qaResults').innerHTML=matching.slice((page-1)*pageSize,page*pageSize).map(v=>{const s=stateOf(v),q=qual[v.id],missing=q?.[1];const cls=s==='coincide'?'ok':s==='incompleto'?'issue':'none';let msg=s==='por_llamamiento'?'Sin filas nominales del CSV · Referencia: sesión y BOE':s==='sin_nominal'?'Sin desglose individual':s==='coincide'?fmt(q?.[6])+' nominales; suman los totales':fmt(q?.[6])+' nominales · diferencia de '+fmt(missing)+' registros';
return `<article class="qa-item"><div><small>${esc(v.fecha)} · ${esc(v.id)}</small><br><strong>${esc(v.titulo)}</strong><p>${esc(msg)}</p><div class="qa-links"><a href="${esc(v.url_votacion||sessionUrl(v))}" target="_blank" rel="noopener noreferrer">Fuente oficial</a><a href="${esc(sessionUrl(v))}" target="_blank" rel="noopener noreferrer">Sesión parlamentaria</a>${v.url_expediente?`<a href="${esc(v.url_expediente)}" target="_blank" rel="noopener noreferrer">Expediente ${esc(v.expediente||'')}</a>`:''}</div></div><div class="qa-side"><span class="qa-label ${cls}">${esc(label(s))}</span><br>${fmt(v.si)} sí · ${fmt(v.no)} no</div></article>`}).join('')||'<p>No hay votaciones que coincidan con los filtros.</p>';
}
$('qaBuscar').addEventListener('input',filter);$('qaAno').addEventListener('change',filter);$('qaEstado').addEventListener('change',filter);$('qaPrev').addEventListener('click',()=>{page--;render()});$('qaNext').addEventListener('click',()=>{page++;render()});filter();
})();
