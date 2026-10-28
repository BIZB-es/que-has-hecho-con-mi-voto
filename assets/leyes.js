(function(){'use strict';
const report=window.QHV_INDICADORES;
const svg=document.getElementById('seriesChart');
const $=id=>document.getElementById(id);
const fnum=(v,dec=0)=>new Intl.NumberFormat('es-ES',{maximumFractionDigits:dec,minimumFractionDigits:dec}).format(v);
const fmt=(v,metric)=>metric.id==='emancipacion'?fnum(v,1)+' %':fnum(v)+' viviendas';
const labelChange=(v,metric)=>metric.id==='emancipacion'?(v>=0?'+':'')+fnum(v,1)+' puntos porcentuales':(v>=0?'+':'')+fnum(v)+' viviendas';
const ns='http://www.w3.org/2000/svg';
let current='protegidas';let fromYear=0;
function el(tag,attrs={},parent=svg,content){const n=document.createElementNS(ns,tag);for(let [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(content!==undefined)n.textContent=content;parent.append(n);return n;}
function metric(){return report.indicadores.find(x=>x.id===current)}
function chart(data,m){svg.replaceChildren();const W=900,H=360,L=78,R=30,T=35,B=62,iw=W-L-R,ih=H-T-B;
 const yr=data.map(x=>x[0]),vs=data.map(x=>x[1]);let ymin=Math.min(...vs),ymax=Math.max(...vs);
 let delta=(ymax-ymin)||Math.max(1,ymax*.1);ymin=ymin-delta*.25;ymax=ymax+delta*.3;
 if(m.id==='protegidas')ymin=Math.max(0,Math.floor(ymin/1000)*1000);
 const x=i=>L+(data.length===1?iw/2:i*iw/(data.length-1));const y=v=>T+(ymax-v)*ih/(ymax-ymin);
 el('rect',{x:L,y:T,width:iw,height:ih,fill:'#ffffff'});
 for(let i=0;i<=4;i++){const v=ymin+(ymax-ymin)*i/4,yy=y(v);el('line',{x1:L,y1:yy,x2:W-R,y2:yy,stroke:'#e3e7e8','stroke-width':1});el('text',{x:L-12,y:yy+4,'text-anchor':'end',fill:'#697681','font-size':12},svg,m.id==='emancipacion'?fnum(v,1)+'%':fnum(Math.round(v)));}
 const cutIdx=yr.indexOf(2023);if(cutIdx>=0){const xx=x(cutIdx);el('line',{x1:xx,y1:T-6,x2:xx,y2:H-B+4,stroke:'#a56746','stroke-width':2,'stroke-dasharray':'5 5'});el('text',{x:xx+7,y:T+15,fill:'#91583d','font-weight':650,'font-size':12},svg,'Ley 2023');}
 data.forEach((p,i)=>{let xx=x(i);el('line',{x1:xx,y1:H-B,x2:xx,y2:H-B+5,stroke:'#b5bfc5'});el('text',{x:xx,y:H-B+23,'text-anchor':'middle',fill:'#344c5c','font-size':13},svg,p[0]);});
 let path='';data.forEach((p,i)=>path+=(i?'L':'M')+x(i).toFixed(2)+','+y(p[1]).toFixed(2)+' ');
 el('path',{d:path,fill:'none',stroke:'#0b6975','stroke-width':4,'stroke-linecap':'round','stroke-linejoin':'round'});
 data.forEach((p,i)=>{let circle=el('circle',{cx:x(i),cy:y(p[1]),r:6,fill:'#0b6975',stroke:'white','stroke-width':2});el('title',{},circle,p[0]+': '+fmt(p[1],m));});
 svg.setAttribute('aria-label',m.nombre+': '+data.map(p=>p[0]+', '+fmt(p[1],m)).join('; '));
}
function render(){let m=metric();if(!m)return;const series=m.serie.filter(p=>p[0]>=fromYear);if(series.length<2){fromYear=m.serie[0][0];return render()}
 document.querySelectorAll('[data-metric]').forEach(button=>{const active=button.dataset.metric===current;button.classList.toggle('selected',active);button.setAttribute('aria-pressed',active?'true':'false')});
 $('chartTitle').textContent=m.nombre;$('metricFrequency').textContent=m.frecuencia.toUpperCase();$('chartSubtitle').textContent=m.ambito+' | '+m.unidad;
 for(let indicator of report.indicadores){let last=indicator.serie.at(-1)[1];$('metricNum-'+indicator.id).textContent=fmt(last,indicator)}
 $('metricExplainer').textContent=m.explicacion;$('metricCaveat').textContent=m.advertencia;
 let first=series[0],last=series.at(-1),change=last[1]-first[1];
 $('plainReading').textContent='Entre '+first[0]+' y '+last[0]+', '+m.nombre.toLowerCase()+' pasó de '+fmt(first[1],m)+' a '+fmt(last[1],m)+' ('+labelChange(change,m)+'). Es una comparaci\u00f3n descriptiva, no una prueba del impacto de la ley.';
 $('metricTable').replaceChildren();series.forEach((p,i)=>{let tr=document.createElement('tr');let val=i===0?'\u2014':labelChange(p[1]-series[i-1][1],m);for(let t of [String(p[0]),fmt(p[1],m),val]){let td=document.createElement('td');td.textContent=t;tr.append(td)}$('metricTable').append(tr)});
 $('metricSources').replaceChildren();for(let s of m.fuentes){let li=document.createElement('li'),a=document.createElement('a');a.textContent=s.nombre;a.href=s.url;a.target='_blank';a.rel='noopener noreferrer';li.append(a);let typ=document.createElement('small');typ.textContent=' ('+s.tipo.replaceAll('_',' ')+')';li.append(typ);$('metricSources').append(li)}
 $('metricReviewed').textContent='Revisión documental: '+m.fecha_revision+'. '+m.estado_contraste+' Atribución causal: '+m.grado_atribucion+'.';
 $('nextEvidence').textContent=m.proximo_paso+' No existe un an\u00e1lisis causal publicado en esta ficha.';
 chart(series,m);
}
function resetStart(){const m=metric();const s=$('rangeStart');s.replaceChildren();m.serie.slice(0,-1).forEach(pair=>{let opt=document.createElement('option');opt.value=pair[0];opt.textContent=String(pair[0]);s.append(opt)});fromYear=m.serie[0][0];s.value=String(fromYear)}
if(!report||!report.indicadores){$('chartSubtitle').textContent='No se ha podido cargar la fuente local de indicadores.';return}
for(let b of document.querySelectorAll('[data-metric]'))b.addEventListener('click',()=>{current=b.dataset.metric;resetStart();render()});
$('rangeStart').addEventListener('change',e=>{fromYear=Number(e.target.value);render()});resetStart();render();
})();
