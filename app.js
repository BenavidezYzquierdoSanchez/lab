/* FraudCloud 2026 · Presentación interactiva autónoma (HTML/CSS/JS sin conexión a AWS).
 * No obtiene datos en vivo; trabaja con ocho CSV Athena exportados del proyecto y evidencias históricas.
 */
(()=>{
'use strict';
const $=s=>document.querySelector(s);
const $$=s=>Array.from(document.querySelectorAll(s));
const assetSrc=path=>window.FRAUD_EMBEDDED_IMAGES?.[path]||path;
const pages=['inicio','proyecto','arquitectura','proceso','repositorio','resultados','app','evidencias','costos','seguridad','cierre'];
let current='inicio', evidenceFilter='Todas', activeToast=null;
const meta={
 '02_fraude_por_monto':{title:'Fraude por rangos de monto transformado',x:'rango_monto',kind:'export',description:'Resultado CSV exportado de Athena. Monto winsorizado, sin importe original ni moneda verificada.',short:'Monto procesado'},
 '03_fraude_noche':{title:'Incidencia por horario',x:'es_noche',kind:'aws',description:'Consulta 03: AWS Athena con captura directa. Los grupos son indicadores binarios, no horas originales.',short:'Noche vs día'},
 '04_fraude_categoria_riesgo':{title:'Bandera de alto riesgo',x:'high_risk_cat',kind:'aws',description:'Consulta 04: AWS Athena con captura directa. high_risk_cat no identifica categorías comerciales concretas.',short:'Riesgo'},
 '05_fraude_edad':{title:'Tasa según grupo de edad',x:'edad_grupo',kind:'export',description:'Resultado exportado de Amazon Athena en aws.zip; sin captura individual de consola.',short:'Edad'},
 '06_fraude_mes':{title:'Comportamiento por mes',x:'mes',kind:'export',description:'Resultado CSV exportado de Athena. Los meses carecen de año verificado; no es una serie interanual.',short:'Meses'},
 '07_fraude_fin_semana':{title:'Fin de semana vs día laboral',x:'es_fin_de_semana',kind:'export',description:'Resultado Athena CSV. Comparación descriptiva por indicador de fin de semana.',short:'Fin de semana'},
 '08_fraude_por_distancia':{title:'Distancia cliente-comercio',x:'rango_distancia',kind:'export',description:'Resultado Athena CSV. Rangos de distancia: asociación, no causalidad.',short:'Distancia'}
};
const docSteps=[
 {name:'Preparación de herramientas',state:'Requisito local',detail:'Instalar Python 3.10+, AWS CLI v2, dependencias y abrir el proyecto desde VS Code. Conservar los archivos originales.',cmd:'python --version\naws --version\npython -m pip install -r requirements.txt'},
 {name:'Acceso seguro con AWS IAM Identity Center',state:'Acceso SSO verificado',detail:'Configurar el perfil fraudlab. El centro de identidad usa us-east-2; el pipeline se ejecutó en us-east-1. La región del portal SSO no cambia la región de los datos.',cmd:'aws configure sso --use-device-code\naws sso login --profile fraudlab\n$env:AWS_PROFILE = "fraudlab"\naws sts get-caller-identity'},
 {name:'Autenticación multifactor (MFA)',state:'Validado por usuario',detail:'El usuario ha aportado capturas adicionales que validan MFA en AWS IAM Identity Center. Este control protege el inicio de sesión. Es distinto del principio de mínimo privilegio: el conjunto AdministratorAccess sigue requiriendo revisión.',cmd:'AWS IAM Identity Center → Configuración → Autenticación multifactor (MFA) → Revisar la configuración y las comprobaciones de acceso'},
 {name:'Validación de plantilla y datos',state:'Validación local',detail:'Validar CloudFormation y revisar consistencia del CSV: 339 607 válidas, 0 inválidas; 1 782 con etiqueta de fraude.',cmd:'aws cloudformation validate-template --template-body file://infra/main.yaml --region us-east-1 --profile fraudlab\npython scripts/local_check.py --csv data/real/fraude_tarjeta_credito_process.csv'},
 {name:'Despliegue con AWS CloudFormation',state:'AWS verificado',detail:'La pila fraude-tarjetas-lab alcanzó CREATE_COMPLETE. Se crearon los recursos de almacenamiento, ETL, catálogo, Athena, IAM y presupuesto.',cmd:'python scripts/run_aws.py deploy --region us-east-1 --email TU_CORREO@DOMINIO.COM --budget 5',image:'01_cloudformation_create_complete.png'},
 {name:'Carga de CSV en S3 RAW',state:'AWS verificado',detail:'Se cargó el archivo real a raw/transactions/ dentro del bucket del laboratorio, conservando la fuente procesada sin sobrescribirla durante ETL.',cmd:'python scripts/run_aws.py upload --region us-east-1 --data data/real/fraude_tarjeta_credito_process.csv',image:'02_s3_csv_upload.png'},
 {name:'Transformación con Glue ETL y S3 Curated',state:'AWS verificado',detail:'AWS Glue 5.0 completó SUCCEEDED. Seleccionó atributos analíticos y produjo dos ficheros Parquet con compresión Snappy en curated/transactions/ingest_date=2026-11-04/.',cmd:'python scripts/run_aws.py etl --region us-east-1',image:'05_glue_etl_succeeded.png'},
 {name:'Crawler y Data Catalog',state:'AWS verificado',detail:'El crawler quedó en READY y registró la tabla fraud_transactions en la base fraude_tarjetas_db para consultar los Parquet.',cmd:'python scripts/run_aws.py catalog --region us-east-1',image:'06_glue_crawler_ready.png'},
 {name:'Consultas analíticas en Amazon Athena',state:'8 CSV Athena / 3 capturas',detail:'Los ocho scripts SQL se ejecutaron y sus resultados CSV se incorporaron al paquete aws.zip. Se conservan capturas directas en la consola para KPIs, horario nocturno y riesgo; las otras cinco consultas se sustentan en los CSV exportados.',cmd:'python scripts/run_aws.py queries --region us-east-1',image:'07_athena_resumen.png'},
 {name:'Visualización con Streamlit local',state:'Evidencia en localhost',detail:'El dashboard Streamlit mostró resultados exportados de Athena, no consulta a Athena en cada clic. La copia HTML guardada requiere servidor Python para su plena funcionalidad.',cmd:'python -m streamlit run dashboard/app.py',image:'10_dashboard_athena.png'},
 {name:'Presupuesto, costos y seguridad',state:'Evidencia disponible',detail:'Se revisaron AWS Budgets, facturación, Cost Explorer y Pricing Calculator. El presupuesto de US$ 5 es aviso, no bloqueo; la estimación de US$ 5,29 no es un cargo medido.',cmd:'aws cloudformation describe-stacks --stack-name fraude-tarjetas-lab --region us-east-1 --profile fraudlab',image:'11_budgets.png'},
 {name:'Cierre controlado (posterior a la sustentación)',state:'Paso futuro / no ejecutado',detail:'Solo cuando termine la exposición y se hayan respaldado resultados, vaciar/borrar únicamente los recursos del stack del laboratorio. Verificar dependencias y facturación por separado.',cmd:'python scripts/run_aws.py destroy --region us-east-1 --confirm-destroy'}
];
function esc(v){return String(v??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));}
function fmt(x,decimals=0){const n=Number(x);return Number.isFinite(n)?n.toLocaleString('es-PE',{minimumFractionDigits:decimals,maximumFractionDigits:decimals}):'—'}
function showToast(message){let t=$('#toast');t.textContent=message;t.classList.add('visible');if(activeToast)clearTimeout(activeToast);activeToast=setTimeout(()=>t.classList.remove('visible'),2800)}
function go(page,push=true){if(!pages.includes(page))return;current=page;$$('.page').forEach(x=>x.classList.toggle('active',x.id===page));$$('[data-go].nav-link').forEach(b=>{b.classList.toggle('active',b.dataset.go===page);if(b.dataset.go===page)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});$('#current-title').textContent=$('#'+page).dataset.title||page;let i=pages.indexOf(page);$('#nav-count').textContent=String(i+1).padStart(2,'0')+' / '+pages.length;$('#bottom-page').textContent=String(i+1).padStart(2,'0')+' / '+pages.length;$('#progress-bar').style.width=((i+1)/pages.length*100)+'%';$('#sidebar').classList.remove('open');if(push){try{history.replaceState(null,'','#'+page)}catch(e){}}window.scrollTo({top:0,behavior:'instant'});if(page==='resultados'||page==='app'){requestAnimationFrame(()=>{$$('.page.active .chart-render').forEach(node=>drawChart(node,node.dataset.chart,node.dataset.metric));});}}
function openImage(path,title){$('#modal-image').src=assetSrc(path);$('#modal-image').alt=title||'Evidencia de FraudCloud';$('#modal-caption').textContent=title||'Evidencia ampliada';$('#image-modal').hidden=false;document.body.style.overflow='hidden';}
function closeImage(){$('#image-modal').hidden=true;$('#modal-image').src='';document.body.style.overflow='';}
function stepRender(){const host=$('#steps-holder');host.innerHTML=docSteps.map((x,i)=>`<article class="step"><div class="step-marker">${String(i).padStart(2,'0')}</div><div class="step-body"><h3>${esc(x.name)}<span class="step-tag">${esc(x.state)}</span></h3><p>${esc(x.detail)}</p><div class="step-code"><code>${esc(x.cmd)}</code><button data-copy="${i}" aria-label="Copiar comandos paso ${i}">Copiar</button></div>${x.image?`<div class="step-bottom"><button class="step-evidence" data-image="assets/evidencias/${x.image}" data-imagetitle="${esc(x.name)}">▧ Ver evidencia real →</button></div>`:''}</div></article>`).join('')}
function groupLabel(key,value){let val=String(value);if(key==='03_fraude_noche')return val==='1'?'Nocturna (1)':'No nocturna (0)';if(key==='04_fraude_categoria_riesgo')return val==='1'?'Riesgo marcado (1)':'Sin marca (0)';if(key==='07_fraude_fin_semana')return val==='1'?'Fin de semana':'Día laboral';if(key==='06_fraude_mes')return ['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][Number(val)]||val;return val.replace(/^\d\d\s+-\s+/,'');}
function labelText(text,max=36){let str=String(text);return str.length>max?str.slice(0,max-1)+'…':str;}
function chartValueLabel(num,metric){return metric==='tasa_fraude_pct'?fmt(num,4)+' %':fmt(num,0)}
function drawChart(node,key,metric){if(!node||!FRAUD_DATA[key])return;const info=meta[key];const records=FRAUD_DATA[key];const values=records.map(r=>Number(r[metric]));const max=Math.max(...values,0.0001);const safeId=key.replace(/[^a-z0-9]/gi,'_');
let width=650,markup='';
if(key==='06_fraude_mes'&&records.length>=10){const height=260,left=34,top=30,right=36,bottom=46,graphW=width-left-right,graphH=height-top-bottom;markup=`<line x1="${left}" y1="${height-bottom}" x2="${width-right}" y2="${height-bottom}" class="gridline"/>`;
for(let t=0;t<=4;t++){const y=top+t*graphH/4;markup+=`<line x1="${left}" x2="${width-right}" y1="${y}" y2="${y}" class="gridline"/><text x="${left-5}" y="${y+4}" text-anchor="end" class="bar-label">${metric==='tasa_fraude_pct'?fmt((4-t)*max/4,2):fmt((4-t)*max/4,0)}</text>`}
let pts=[];records.forEach((r,i)=>{const x=left+(i/(records.length-1))*graphW;const y=top+(1-Number(r[metric])/max)*graphH;pts.push([x,y]);markup+=`<text x="${x}" y="${height-19}" text-anchor="middle" class="bar-label">${groupLabel(key,r[info.x])}</text>`});const line=pts.map(p=>p.join(',')).join(' ');markup+=`<polyline points="${line}" fill="none" stroke="var(--accent)" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>`;records.forEach((r,i)=>{const p=pts[i];markup+=`<circle cx="${p[0]}" cy="${p[1]}" r="5" fill="var(--accent)" stroke="var(--surface)" stroke-width="2"><title>${groupLabel(key,r[info.x])} · ${chartValueLabel(r[metric],metric)}</title></circle>`});node.innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(info.title)}">${markup}</svg>`;return}
const n=records.length;const height=Math.max(160,n*43+25);const x0=210,xEnd=558,top=14;
records.forEach((r,i)=>{const y=top+i*43;const val=Number(r[metric]);const w=Math.max(2,(val/max)*(xEnd-x0));let label=groupLabel(key,r[info.x]);markup+=`<text x="2" y="${y+22}" class="bar-label">${esc(labelText(label,30))}</text><rect x="${x0}" y="${y+8}" width="${xEnd-x0}" height="22" rx="6" class="bar-bg"/><rect x="${x0}" y="${y+8}" width="${w}" height="22" rx="6" class="bar-fill ${i%2?'alt':''}"><title>${esc(label)} · ${chartValueLabel(val,metric)} · ${fmt(r.transacciones)} operaciones</title></rect><text x="${xEnd+12}" y="${y+22}" class="bar-value">${esc(chartValueLabel(val,metric))}</text>`});node.innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(info.title)}">${markup}</svg>`;}
function renderResultCharts(){ $$('#resultados .chart-render').forEach(node=>drawChart(node,node.dataset.chart,node.dataset.metric)); }
function renderAppCharts(){const holder=$('#app-charts');const metric=$('#metric-select').value;const category=$('#app-category').value;const keys=Object.keys(meta).filter(k=>category==='all'||(category==='verified'?meta[k].kind==='aws':meta[k].kind==='export'));
holder.innerHTML=keys.map(key=>`<article class="glass-card chart-card"><div class="card-title-row"><div><div class="little-label">${meta[key].kind==='aws'?'CAPTURA DE CONSOLA + CSV ATHENA':'RESULTADO CSV EXPORTADO DE ATHENA'}</div><h3>${esc(meta[key].title)}</h3></div><span class="pill ${meta[key].kind==='aws'?'success':'info'}">${meta[key].kind==='aws'?'Captura + CSV':'CSV Athena'}</span></div><div class="chart-render" data-chart="${key}" data-metric="${metric}"></div><p class="chart-note">${esc(meta[key].description)}</p></article>`).join('');
holder.querySelectorAll('.chart-render').forEach(n=>drawChart(n,n.dataset.chart,n.dataset.metric));}
function evidenceRender(){const q=$('#evidence-search').value.toLocaleLowerCase('es').trim();const evidence=EVIDENCES.filter(x=>(evidenceFilter==='Todas'||x.cat===evidenceFilter)&&(!q||(x.title+' '+x.cat+' '+x.section).toLocaleLowerCase('es').includes(q)));$('#evidence-gallery').innerHTML=evidence.length?evidence.map(e=>`<article class="evidence-card"><button class="evidence-preview" data-image="${esc(e.file)}" data-imagetitle="${esc(e.title)}"><img loading="lazy" src="${esc(assetSrc(e.file))}" alt="${esc(e.title)}"></button><div class="evidence-card-body"><small>${String(e.id).padStart(2,'0')} · ${esc(e.cat.toUpperCase())}</small><b>${esc(e.title)}</b><p>${esc(e.section)}</p><button data-image="${esc(e.file)}" data-imagetitle="${esc(e.title)}">Ver captura completa ↗</button></div></article>`).join(''):'<div class="evidence-empty">No se encontraron evidencias con estos filtros.</div>';}
function copyToClipboard(s){if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(s).then(()=>showToast('Comandos copiados')).catch(()=>fallbackCopy(s));}else fallbackCopy(s)}
function fallbackCopy(s){const ta=document.createElement('textarea');ta.value=s;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{document.execCommand('copy');showToast('Comandos copiados')}catch(e){showToast('Selecciona el texto para copiarlo')}ta.remove()}
function exportCsv(){const category=$('#app-category').value;const metric=$('#metric-select').value;let csv='origen,analisis,segmento,transacciones,fraudes,tasa_fraude_pct,metrica_seleccionada,valor\n';for(const [key,m] of Object.entries(meta)){if(category!=='all'&& (category==='verified'?m.kind!=='aws':m.kind!=='export'))continue;for(const r of FRAUD_DATA[key]){const cells=[m.kind==='aws'?'Athena: captura + CSV':'Athena: CSV exportado',m.title,groupLabel(key,r[m.x]),r.transacciones,r.fraudes,r.tasa_fraude_pct,metric,r[metric]];csv+=cells.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')+'\n'}}const blob=new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='fraudcloud_resultados_'+category+'.csv';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);showToast('CSV de agregaciones generado');}
function setTheme(v){document.body.dataset.theme=v;$('#theme-toggle').textContent=v==='dark'?'☀':'☾';try{localStorage.setItem('fraudcloud-theme',v)}catch(e){}}
function setPalette(v){document.body.dataset.accent=v;$$('.swatch').forEach(s=>s.classList.toggle('selected',s.dataset.palette===v));try{localStorage.setItem('fraudcloud-accent',v)}catch(e){}}
// Pantalla completa real del navegador (distinta del modo Presentar, que solo oculta el menú).
function updateFullscreenButton(){const active=Boolean(document.fullscreenElement||document.webkitFullscreenElement);const btn=$('#fullscreen-toggle');if(!btn)return;btn.textContent=active?'⤢ Salir de pantalla completa':'⛶ Pantalla completa';btn.setAttribute('aria-pressed',String(active));btn.setAttribute('aria-label',active?'Salir de pantalla completa':'Activar pantalla completa');btn.title=active?'Salir de pantalla completa (Esc)':'Ver a pantalla completa (Shift+F); Esc para salir'}
async function toggleFullscreen(){const active=Boolean(document.fullscreenElement||document.webkitFullscreenElement);try{if(active){if(document.exitFullscreen)await document.exitFullscreen();else if(document.webkitExitFullscreen)document.webkitExitFullscreen();}else{const root=document.documentElement;if(root.requestFullscreen)await root.requestFullscreen();else if(root.webkitRequestFullscreen)root.webkitRequestFullscreen();else showToast('Este navegador no permite la pantalla completa desde el botón; usa F11.');}}catch(err){showToast('No se pudo activar pantalla completa. Prueba con F11.')}finally{updateFullscreenButton()}}

// Explorador del código auténtico: únicamente fuentes del ZIP proporcionado.
let repoOrigin='aws';let repoCurrent='aws:infra/main.yaml';
function repoFiles(){return (window.FRAUD_REPOSITORY?.files||[]).filter(f=>f.origin===repoOrigin)}
function repoFind(f){return (window.FRAUD_REPOSITORY?.files||[]).find(x=>x.key===f)}
function repoRender(){
 const all=repoFiles(),search=($('#repo-search')?.value||'').trim().toLowerCase();
 const found=all.filter(f=>!search||(f.path+' '+f.description).toLowerCase().includes(search));
 $('#repo-file-count').textContent=found.length+' / '+all.length+' archivos';
 const root={folders:{},files:[]};
 for(const f of found){const segments=f.path.split('/');let node=root;
  for(const p of segments.slice(0,-1)){node.folders[p]??={folders:{},files:[]};node=node.folders[p]}
  node.files.push(f);
 }
 function branch(node,depth=0){
  let out='';for(const [folder,child] of Object.entries(node.folders).sort((a,b)=>a[0].localeCompare(b[0])))
    out+='<details '+(depth===0||search?'open':'')+'><summary>📁 '+esc(folder)+'</summary>'+branch(child,depth+1)+'</details>';
  for(const f of node.files.sort((a,b)=>a.path.localeCompare(b.path)))out+='<button class="repo-file-btn '+(repoCurrent===f.key?'active ':'')+(!f.viewable?'disabled':'')+'" data-open-file="'+esc(f.key)+'">'+(f.viewable?'▤ ':'◫ ')+esc(f.path.split('/').pop())+(!f.viewable?'<span> · binario</span>':'')+'</button>';
  return out;
 }
 $('#repo-tree').innerHTML=found.length?branch(root):'<div class="repo-empty">Sin archivos coincidentes.</div>';
}
function repoOpen(key,navigate=false){const f=repoFind(key);if(!f)return;
 if(navigate)go('repositorio');repoCurrent=key;repoOrigin=f.origin;
 $$('.repo-tabs button').forEach(btn=>btn.classList.toggle('active',btn.dataset.repoOrigin===f.origin));
 $('#repo-file-ext').textContent=f.ext.toUpperCase()+(f.viewable?' · TEXTO FUENTE':' · ARCHIVO BINARIO');
 $('#repo-file-name').textContent=f.path;$('#repo-file-description').textContent=f.description;
 const text=window.FRAUD_REPOSITORY?.contents?.[key];
 $('#repo-code').textContent=typeof text==='string'?text:'Archivo binario o conjunto de datos de gran tamaño. Está incluido en el paquete ZIP original y se omite del HTML para que la presentación sea ligera.';
 $('#repo-line-count').textContent=typeof text==='string'?text.split('\n').length+' líneas · '+(new TextEncoder().encode(text).length/1024).toFixed(1)+' KB':(f.size/1024/1024).toFixed(2)+' MB';
 $('#repo-source-label').textContent=f.origin==='aws'?'Fuente: proyecto AWS original (configuración corregida)':'Fuente: paquete adicional Streamlit EC2';
 $('#repo-copy').disabled=typeof text!=='string';$('#repo-download').disabled=typeof text!=='string';
 $('#repo-code-scroller').scrollTop=0;repoRender();
}
function repoDownload(){const text=window.FRAUD_REPOSITORY?.contents?.[repoCurrent];if(typeof text!=='string')return;
 const f=repoFind(repoCurrent);const blob=new Blob([text],{type:'text/plain;charset=utf-8'});const u=URL.createObjectURL(blob);const a=document.createElement('a');a.href=u;a.download=f.path.split('/').pop();document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1500);showToast('Archivo fuente descargado');}
function repoInit(){
 $$('.repo-tabs button').forEach(b=>b.addEventListener('click',()=>{repoOrigin=b.dataset.repoOrigin;repoCurrent=repoOrigin==='aws'?'aws:infra/main.yaml':'ec2:LEEME_PRIMERO.md';$('#repo-search').value='';repoOpen(repoCurrent)}));
 $('#repo-search').addEventListener('input',repoRender);
 $('#repo-copy').addEventListener('click',()=>{const t=window.FRAUD_REPOSITORY?.contents?.[repoCurrent];if(typeof t==='string')copyToClipboard(t)});
 $('#repo-download').addEventListener('click',repoDownload);
 document.addEventListener('click',e=>{const btn=e.target.closest('[data-open-file]');if(btn){const key=btn.dataset.openFile;repoOpen(key,current!=='repositorio');if(current==='repositorio'&&!btn.closest('#repo-tree'))$('#repo-file-name').scrollIntoView({behavior:'smooth',block:'center'});}});
 repoOpen(repoCurrent);
}

function init(){repoInit();stepRender();evidenceRender();renderAppCharts();renderResultCharts();let theme='dark',accent='blue';try{theme=localStorage.getItem('fraudcloud-theme')||'dark';accent=localStorage.getItem('fraudcloud-accent')||'blue'}catch(e){}setTheme(['light','dark'].includes(theme)?theme:'dark');setPalette(['blue','teal','violet','amber'].includes(accent)?accent:'blue');const hash=location.hash.slice(1);go(pages.includes(hash)?hash:'inicio',false);
document.addEventListener('click',ev=>{let node=ev.target.closest('[data-go]');if(node){ev.preventDefault();go(node.dataset.go);return}let image=ev.target.closest('[data-image]');if(image){ev.preventDefault();openImage(image.dataset.image,image.dataset.imagetitle);return}let copy=ev.target.closest('[data-copy]');if(copy){copyToClipboard(docSteps[Number(copy.dataset.copy)].cmd);return}});
$('#mobile-menu').addEventListener('click',()=>$('#sidebar').classList.toggle('open'));
$('#theme-toggle').addEventListener('click',()=>setTheme(document.body.dataset.theme==='dark'?'light':'dark'));
$$('.swatch').forEach(s=>s.addEventListener('click',()=>setPalette(s.dataset.palette)));
$('#present-mode').addEventListener('click',()=>{document.body.classList.toggle('presentation');$('#present-mode').textContent=document.body.classList.contains('presentation')?'▤ Mostrar menú':'◩ Presentar';});
$('#fullscreen-toggle').addEventListener('click',toggleFullscreen);
document.addEventListener('fullscreenchange',updateFullscreenButton);
document.addEventListener('webkitfullscreenchange',updateFullscreenButton);
$('#prev-tab').addEventListener('click',()=>go(pages[Math.max(0,pages.indexOf(current)-1)]));$('#next-tab').addEventListener('click',()=>go(pages[Math.min(pages.length-1,pages.indexOf(current)+1)]));
$('#metric-select').addEventListener('change',renderAppCharts);$('#app-category').addEventListener('change',renderAppCharts);
$('#refresh-visual').addEventListener('click',()=>{renderAppCharts();showToast('Gráficos actualizados con datos incluidos (sin AWS en vivo)')});$('#export-data').addEventListener('click',exportCsv);
$('#open-snapshot').addEventListener('click',()=>{let box=$('#snapshot-block');box.hidden=!box.hidden;if(!box.hidden){const frame=$('#snapshot-frame');if(window.FRAUD_SNAPSHOT_B64){const bytes=Uint8Array.from(atob(window.FRAUD_SNAPSHOT_B64),c=>c.charCodeAt(0));frame.srcdoc=new TextDecoder('utf-8').decode(bytes)}else if(!frame.src||frame.src==='about:blank')frame.src='documentos/FraudCloud_Streamlit_original_guardado.html';$('#open-snapshot').textContent='◫ Ocultar HTML guardado'}else $('#open-snapshot').textContent='◫ Ver HTML guardado'});
$('#evidence-search').addEventListener('input',evidenceRender);$$('#evidence-filters button').forEach(b=>b.addEventListener('click',()=>{evidenceFilter=b.dataset.filter;$$('#evidence-filters button').forEach(s=>s.classList.toggle('active',s===b));evidenceRender()}));
$('#modal-close').addEventListener('click',closeImage);$('#image-modal').addEventListener('click',e=>{if(e.target.id==='image-modal')closeImage()});
$('#print-page').addEventListener('click',()=>window.print());
window.addEventListener('keydown',e=>{if(e.key==='Escape'){if(document.fullscreenElement||document.webkitFullscreenElement)toggleFullscreen();closeImage();$('#sidebar').classList.remove('open');return}if(e.target.matches('input,select,textarea'))return;if(e.shiftKey&&e.key.toLowerCase()==='f'&&!e.ctrlKey&&!e.altKey&&!e.metaKey){e.preventDefault();toggleFullscreen();return}if(['ArrowRight','ArrowLeft'].includes(e.key)&&$('#image-modal').hidden){const n=pages.indexOf(current)+(e.key==='ArrowRight'?1:-1);if(n>=0&&n<pages.length)go(pages[n])}});
window.addEventListener('hashchange',()=>{const next=location.hash.slice(1);if(pages.includes(next)&&next!==current)go(next,false)});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
