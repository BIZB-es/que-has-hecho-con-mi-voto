(function(){'use strict';
 const data=window.QHV_IDENTIDADES_XV?.censo||[],$=x=>document.getElementById(x);let page=1,filtered=[];
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const norm=x=>String(x||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 function draw(){let q=norm($('censoQuery').value),f=$('censoState').value;
  filtered=data.filter(x=>(f==='all'||(f==='with'&&x.voto_en_csv)||(f==='without'&&!x.voto_en_csv))&&norm(x.nombre+' '+(x.codigo||'')).includes(q));
  let totalPages=Math.max(1,Math.ceil(filtered.length/24));page=Math.min(page,totalPages);
  $('censoCount').textContent=`${filtered.length.toLocaleString('es-ES')} personas en esta consulta`;
  let slice=filtered.slice((page-1)*24,page*24);
  $('censoResults').innerHTML=slice.map(x=>`<article class="census-card"><h3>${esc(x.nombre)}</h3><p>${x.codigo?'Código parlamentario '+esc(x.codigo)+' · XV':'Código no disponible en el CSV nominal recibido'}</p>${x.formacion_ficha?`<p>Formación en ficha oficial: <b>${esc(x.formacion_ficha)}</b></p>`:''}${x.url_ficha?`<a class="card-link" href="${esc(x.url_ficha)}" target="_blank" rel="noopener noreferrer">Ver ficha oficial del Congreso ↗</a>`:'<p>Consultar nombre en el buscador oficial de diputados</p>'}</article>`).join('')||'<p class="census-empty">No se han encontrado coincidencias. Borra el filtro e inténtalo de nuevo.</p>';
  $('censoPage').textContent=`Página ${page} de ${totalPages}`;$('censoPrev').disabled=page===1;$('censoNext').disabled=page>=totalPages;
 }
 $('censoQuery').addEventListener('input',()=>{page=1;draw()});$('censoState').addEventListener('change',()=>{page=1;draw()});
 $('censoPrev').addEventListener('click',()=>{page--;draw();$('censoCount').scrollIntoView({block:'nearest'})});$('censoNext').addEventListener('click',()=>{page++;draw();$('censoCount').scrollIntoView({block:'nearest'})});draw();
 window.QHV_CENSO_TEST={getState:()=>({count:filtered.length,page,items:data.length})};
})();
