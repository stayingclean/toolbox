import * as THREE from 'three';
import * as OBC from '@thatopen/components';
import * as OBF from '@thatopen/components-front';
import {readProperties,renderProperties} from './properties.mjs';
import {setupMeasurements} from './measurements.mjs';
import {download,readJSON,validateView} from './files.mjs';
const $=s=>document.querySelector(s),status=$('#status'),view=$('#view');
let toastTimer;
function notify(message){$('#notice').textContent=message;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#notice').textContent='',6500);}
async function run(action){try{return await action();}catch(e){notify(e.message||'Die Aktion konnte nicht ausgeführt werden.');}}
function tab(id){for(const b of document.querySelectorAll('[data-tab]'))b.setAttribute('aria-selected',String(b.dataset.tab===id));for(const p of document.querySelectorAll('[data-pane]'))p.hidden=p.dataset.pane!==id;$('#panel').classList.remove('collapsed');$('#toggle').setAttribute('aria-expanded','true');for(const b of document.querySelectorAll('[data-open]'))b.setAttribute('aria-selected',String(b.dataset.open===id));$('#cut-tool').setAttribute('aria-selected',String(id==='cut'));dispatchEvent(new Event('viewer-layout'));}
for(const b of document.querySelectorAll('[data-tab]'))b.onclick=()=>tab(b.dataset.tab);
$('#toggle').onclick=()=>{const hidden=$('#panel').classList.toggle('collapsed');$('#toggle').setAttribute('aria-expanded',String(!hidden));dispatchEvent(new Event('viewer-layout'));};
for(const b of document.querySelectorAll('[data-open]'))b.onclick=()=>tab(b.dataset.open);
for(const b of document.querySelectorAll('[data-command]'))b.onclick=()=>$('#'+b.dataset.command).click();
try{
const components=new OBC.Components(),world=components.get(OBC.Worlds).create();
world.scene=new OBC.SimpleScene(components);world.scene.setup();world.scene.three.background=new THREE.Color('#dfe4e9');
world.renderer=new OBF.RendererWith2D(components,view,{antialias:true,preserveDrawingBuffer:true});world.renderer.showLogo=false;
// RendererWith2D sets relative positioning; restore the app's fixed viewport.
view.style.position='fixed';world.renderer.resize();
world.renderer.three.setPixelRatio(Math.min(devicePixelRatio,2));world.camera=new OBC.OrthoPerspectiveCamera(components);world.camera.threePersp.fov=45;world.camera.threePersp.near=.03;world.camera.threePersp.far=1000;world.camera.threePersp.updateProjectionMatrix();components.init();
const renderer=world.renderer.three,scene=world.scene.three,controls=world.camera.controls;
const fragments=components.get(OBC.FragmentsManager);fragments.init(new URL('./vendor/worker.mjs',import.meta.url).href);
controls.addEventListener('update',()=>fragments.core.update());world.camera.projection.onChanged.add(()=>{for(const m of fragments.list.values())m.useCamera(world.camera.three);fragments.core.update(true);});
const clipper=components.get(OBC.Clipper);clipper.enabled=true;clipper.visible=false;
const defs=[['UG','Untergeschoss',-2.42],['EG','Erdgeschoss',.13],['OG1','1. Obergeschoss',2.93],['OG2','2. Obergeschoss',5.62],['Dach','Dach',8.3]];
const groups=new Map(),inputs=new Map(),selection=new Set(),hidden=new Set();let isolated=null,model,elements,ids,byId,byGuid,pending=Promise.resolve(),mode='select',selectionRevision=0,lastProperties=null;
let center=new THREE.Vector3(),distance=60;
function isVisible(id){const e=byId.get(id);return groups.get(e.floor).visible&&!hidden.has(id)&&(!isolated||isolated.has(id));}
function queueVisibility(){const shown=ids.filter(isVisible);pending=pending.then(async()=>{await model.setVisible(undefined,false);if(shown.length)await model.setVisible(shown,true);await fragments.core.update(true);$('#visible-count').textContent=`${shown.length.toLocaleString('de-CH')} / ${ids.length.toLocaleString('de-CH')} Bauteile sichtbar`;});return pending;}
for(const[key,label]of defs){const row=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=true;input.disabled=true;input.dataset.floor=key;row.append(input,document.createTextNode(label));$('#floors').append(row);inputs.set(key,input);input.onchange=()=>run(()=>{groups.get(key).visible=input.checked;return queueVisibility();});for(const s of[$('#filter-floor'),$('#walk-floor')]){const o=document.createElement('option');o.value=key;o.textContent=label;s.append(o);}}
$('#walk-floor').querySelector('option[value="Dach"]')?.remove();$('#walk-floor').value='EG';
function all(only=null){hidden.clear();isolated=null;for(const[key,input]of inputs){input.checked=only===null||key===only;input.indeterminate=false;groups.get(key).visible=input.checked;}return queueVisibility();}
$('#all').onclick=()=>run(()=>all());$('#eg').onclick=()=>run(()=>all('EG'));
const measures=setupMeasurements(components,world,notify,run);
const hints={select:'Bauteil anklicken · Umschalt oder «Mehrfach» für mehrere · Ziehen zum Drehen',length:'Zwei Punkte anklicken. Esc bricht die begonnene Messung ab.',area:'Ebene Fläche: Punkte anklicken; «Abschliessen» oder Enter beendet die Fläche.',angle:'Drei Punkte anklicken: Anfang – Scheitel – Ende.',cut:'Auf eine Fläche klicken, um dort eine Schnittebene anzulegen.',walk:'Ziehen: umsehen · W/A/S/D: gehen · R/F: hoch/runter · Esc: verlassen',teleport:'Eine Bodenfläche anklicken: dort startet die Begehung auf Augenhöhe.'};
function setMode(value){mode=value;measures.setMode(value);for(const b of document.querySelectorAll('[data-mode]'))b.setAttribute('aria-pressed',String(b.dataset.mode===value));$('#mode-hint').textContent=hints[value];$('#walk-controls').hidden=value!=='walk';if(['length','area','angle'].includes(value))tab('measure');if(value==='cut')tab('cut');if(['walk','teleport'].includes(value))tab('view');if(value!=='walk'&&world.camera.mode.id==='FirstPerson')world.camera.set('Orbit');}
for(const b of document.querySelectorAll('[data-mode]'))b.onclick=()=>run(()=>b.dataset.mode==='walk'?startWalk():setMode(b.dataset.mode));
function orbit(){world.camera.set('Orbit');controls.minDistance=.2;controls.maxDistance=250;}
async function reset(){setMode('select');orbit();await world.camera.projection.set('Perspective');$('#projection').value='Perspective';const d=distance*Math.max(1,.85/(view.clientWidth/view.clientHeight)),p=center.clone().add(new THREE.Vector3(1,.72,1.15).normalize().multiplyScalar(d));await controls.setLookAt(...p,...center,false);await fragments.core.update(true);}
$('#reset').onclick=()=>run(reset);
async function direction(dir){setMode('select');orbit();await world.camera.projection.set('Orthographic');$('#projection').value='Orthographic';const p=center.clone().addScaledVector(new THREE.Vector3(...dir),distance);await controls.setLookAt(...p,...center,false);await controls.fitToBox(model.box,false,{paddingTop:2,paddingBottom:2,paddingLeft:2,paddingRight:2});if(dir[1]>.9)world.camera.set('Plan');await fragments.core.update(true);}
$('#top').onclick=()=>run(()=>direction([0,1,.0001]));for(const b of document.querySelectorAll('[data-direction]'))b.onclick=()=>run(()=>direction(JSON.parse(b.dataset.direction)));
$('#projection').onchange=e=>run(async()=>{if(mode==='walk')setMode('select');if(e.target.value==='Perspective'&&world.camera.mode.id==='Plan')orbit();await world.camera.projection.set(e.target.value);});
async function fetchOK(url){const r=await fetch(url);if(!r.ok)throw Error(`${url}: ${r.status}`);return r;}
const data=await Promise.all([fetchOK('./model.frag').then(r=>r.arrayBuffer()),fetchOK('./elements.json').then(r=>r.json())]);elements=data[1];model=await fragments.core.load(data[0],{modelId:'Altbau',camera:world.camera.three});model.useCamera(world.camera.three);scene.add(model.object);
ids=await model.getLocalIdsByGuids(elements.map(e=>e.guid));byId=new Map();byGuid=new Map();elements.forEach((e,i)=>{if(ids[i]===null)throw Error('IFC-Element fehlt: '+e.name);byId.set(ids[i],e);byGuid.set(e.guid,ids[i]);});
model.getClippingPlanesEvent=()=>world.renderer.clippingPlanes;
for(const[key]of defs){groups.set(key,{ids:ids.filter(id=>byId.get(id).floor===key),visible:true});inputs.get(key).disabled=false;}
model.box.getCenter(center);distance=Math.max(...model.box.getSize(new THREE.Vector3()).toArray())*1.85;
const grid=components.get(OBC.Grids).create(world);grid.three.position.y=model.box.min.y-.03;grid.visible=false;$('#grid').onchange=e=>grid.visible=e.target.checked;$('#background').onchange=e=>scene.background=new THREE.Color(e.target.value);
await reset();await queueVisibility();status.textContent='';$('#app-tools').inert=false;$('#panel').inert=false;
async function paintSelection(){await model.resetHighlight();if($('#xray').checked)await model.highlight(undefined,{color:new THREE.Color('#cad6d0'),opacity:.18,transparent:true,renderedFaces:2,depthWrite:false});if(selection.size)await model.highlight([...selection],{color:new THREE.Color('#f3a52c'),opacity:1,transparent:false,renderedFaces:2});await fragments.core.update(true);}
async function select(id,add=false){if(!add)selection.clear();if(id!==null){if(add&&selection.has(id))selection.delete(id);else selection.add(id);}const revision=++selectionRevision;await paintSelection();$('#selection-count').textContent=`${selection.size} ausgewählt`;for(const b of document.querySelectorAll('[data-selection-action]'))b.disabled=!selection.size;lastProperties=null;$('#properties').replaceChildren();if(!selection.size){$('#selected-name').textContent='Kein Bauteil ausgewählt';$('#selected-meta').textContent='';return;}const selectedId=[...selection].at(-1),el=byId.get(selectedId);$('#selected-name').textContent=el.name;$('#selected-meta').textContent=`${el.type} · ${defs.find(d=>d[0]===el.floor)[1]}`;$('#properties').textContent='IFC-Eigenschaften werden geladen …';tab('properties');const props=await readProperties(model,selectedId);if(revision!==selectionRevision)return;lastProperties=props;renderProperties($('#properties'),props);}
$('#clear-selection').onclick=()=>run(()=>select(null));$('#xray').onchange=()=>run(paintSelection);
$('#hide-selected').onclick=()=>run(()=>{for(const id of selection)hidden.add(id);return queueVisibility();});
$('#isolate-selected').onclick=()=>run(()=>{isolated=new Set(selection);for(const id of selection){hidden.delete(id);const key=byId.get(id).floor;groups.get(key).visible=true;inputs.get(key).checked=true;}return queueVisibility();});
$('#focus-selected').onclick=()=>run(async()=>{setMode('select');orbit();const box=new THREE.Box3();for(const b of await model.getBoxes([...selection]))box.union(b);await controls.fitToBox(box,true,{paddingTop:1,paddingBottom:1,paddingLeft:1,paddingRight:1});});
$('#export-properties').onclick=()=>run(async()=>{const properties=[];for(const id of selection)properties.push(await readProperties(model,id));download('Altbau-Eigenschaften.json',properties);});
let resultLimit=60;
function results(){const query=$('#search').value.trim().toLocaleLowerCase(),floor=$('#filter-floor').value,type=$('#filter-type').value,found=ids.filter(id=>{const e=byId.get(id);return(!floor||e.floor===floor)&&(!type||e.type===type)&&(!query||`${e.name} ${e.type} ${e.guid}`.toLocaleLowerCase().includes(query));});$('#result-count').textContent=`${found.length} Treffer`;$('#results').replaceChildren();for(const id of found.slice(0,resultLimit)){const el=byId.get(id),b=document.createElement('button');b.className='result';b.textContent=el.name;b.title=`${el.type} · ${el.guid}`;b.onclick=e=>run(()=>select(id,e.shiftKey||$('#multi-select').checked));$('#results').append(b);}$('#more-results').hidden=found.length<=resultLimit;}
for(const type of[...new Set(elements.map(e=>e.type))].sort()){const o=document.createElement('option');o.value=type;o.textContent=type;$('#filter-type').append(o);}
for(const input of[$('#search'),$('#filter-floor'),$('#filter-type')])input.addEventListener('input',()=>{resultLimit=60;results();});$('#more-results').onclick=()=>{resultLimit+=60;results();};results();
let activePlane=null;
function sectionBounds(normal){let min=Infinity,max=-Infinity;for(const x of[model.box.min.x,model.box.max.x])for(const y of[model.box.min.y,model.box.max.y])for(const z of[model.box.min.z,model.box.max.z]){const d=normal.dot(new THREE.Vector3(x,y,z));min=Math.min(min,d);max=Math.max(max,d);}return{min,max};}
function syncSection(){const p=clipper.list.get(activePlane);for(const id of['section-slider','section-position','section-flip','section-center'])$('#'+id).disabled=!p;for(const b of document.querySelectorAll('[data-cut-axis]'))b.setAttribute('aria-pressed',String(!!p&&Math.abs(p.normal.dot(new THREE.Vector3(...JSON.parse(b.dataset.cutAxis))))>.999));if(!p){$('#section-extent').textContent='—';return;}const{min,max}=sectionBounds(p.normal),d=p.origin.dot(p.normal);$('#section-slider').min=Math.floor(min*100)/100;$('#section-slider').max=Math.ceil(max*100)/100;$('#section-slider').value=d;$('#section-position').max=Math.round((max-min)*100);$('#section-position').value=Math.round((d-min)*100);$('#section-extent').textContent=`${Math.round((max-min)*100).toLocaleString('de-CH')} cm`;}
function planeRows(){const list=$('#plane-list');list.replaceChildren();for(const[id,p]of clipper.list){const row=document.createElement('div');row.className='measurement-row';const pick=document.createElement('button');const label=Math.abs(p.normal.y)>.999?'Horizontal':Math.abs(p.normal.x)>.999?'Längs · X':Math.abs(p.normal.z)>.999?'Quer · Y':'Freier Schnitt';pick.textContent=`${list.children.length+1} · ${label}`;pick.setAttribute('aria-pressed',String(activePlane===id));pick.onclick=()=>{activePlane=id;planeRows();};const del=document.createElement('button');del.textContent='×';del.title='Schnitt löschen';del.setAttribute('aria-label',`${label} löschen`);del.onclick=()=>run(async()=>{await clipper.delete(world,id);if(activePlane===id)activePlane=[...clipper.list.keys()].at(-1)||null;planeRows();});row.append(pick,del);list.append(row);}if(!clipper.list.size){list.textContent='Kein Schnitt aktiv. Oben eine Richtung wählen.';list.className='empty-cut';}else list.className='';syncSection();}
function addPlane(normal,point){if(clipper.list.size>=12)throw Error('Maximal 12 Schnitte. Bitte zuerst einen löschen.');activePlane=clipper.createFromNormalAndCoplanarPoint(world,normal,point);clipper.visible=$('#section-helpers').checked;planeRows();return activePlane;}
function quickSection(normal){setMode('select');tab('cut');const p=clipper.list.get(activePlane);if(p)p.setFromNormalAndCoplanarPoint(normal,center.clone());else addPlane(normal,center.clone());planeRows();$('#mode-hint').textContent='Schnitt aktiv · Richtung und Position im Inspektor ändern · «Alle entfernen» zeigt das ganze Modell';return fragments.core.update(true);}
$('#cut-tool').onclick=()=>run(()=>{if(!clipper.list.size)return quickSection(new THREE.Vector3(0,-1,0));setMode('select');tab('cut');planeRows();});
for(const b of document.querySelectorAll('[data-cut-axis]'))b.onclick=()=>run(()=>quickSection(new THREE.Vector3(...JSON.parse(b.dataset.cutAxis))));
async function moveSection(value){const p=clipper.list.get(activePlane);if(!p)return;const{min,max}=sectionBounds(p.normal);if(!Number.isFinite(value))return syncSection();const d=Math.max(min,Math.min(max,value));p.setFromNormalAndCoplanarPoint(p.normal.clone(),p.origin.clone().addScaledVector(p.normal,d-p.origin.dot(p.normal)));syncSection();await fragments.core.update(true);}
$('#section-slider').oninput=e=>run(()=>moveSection(Number(e.target.value)));
$('#section-position').onchange=e=>run(()=>{const p=clipper.list.get(activePlane);if(p)return moveSection(sectionBounds(p.normal).min+Number(e.target.value)/100);});
$('#section-center').onclick=()=>run(()=>{const p=clipper.list.get(activePlane);if(p)return moveSection(center.dot(p.normal));});
$('#section-new').onclick=()=>run(()=>{setMode('select');tab('cut');addPlane(new THREE.Vector3(0,-1,0),center.clone());return fragments.core.update(true);});
$('#section-flip').onclick=()=>run(async()=>{const p=clipper.list.get(activePlane);if(p)p.setFromNormalAndCoplanarPoint(p.normal.clone().negate(),p.origin.clone());planeRows();await fragments.core.update(true);});$('#section-helpers').onchange=e=>clipper.visible=e.target.checked;$('#section-clear').onclick=()=>run(async()=>{clipper.deleteAll();activePlane=null;planeRows();await fragments.core.update(true);});planeRows();
const pressed=new Set();let lastFrame=performance.now();
async function startWalk(point){
 const floor=$('#walk-floor').value;groups.get(floor).visible=true;inputs.get(floor).checked=true;await queueVisibility();
 let start=point?.clone();
 if(!start){const candidates=groups.get(floor).ids.filter(id=>/Bodenaufbau/.test(byId.get(id).name));const preferred=candidates.find(id=>/Saal|Gang|Galerie/.test(byId.get(id).name))??candidates[0];
  if(preferred===undefined)throw Error('Bitte den Startpunkt auf einer Bodenfläche anklicken.');
  const box=await model.getMergedBox([preferred]);start=box.getCenter(new THREE.Vector3());start.y=box.max.y;
 }
 await world.camera.projection.set('Perspective');$('#projection').value='Perspective';world.camera.set('FirstPerson');controls.truckSpeed=1;
 const p=start.add(new THREE.Vector3(0,1.65,0));await controls.setLookAt(p.x,p.y,p.z,p.x,p.y,p.z-1,false);setMode('walk');
}
$('#walk-start').onclick=()=>run(()=>startWalk());$('#walk-place').onclick=()=>setMode('teleport');$('#walk-exit').onclick=()=>{pressed.clear();setMode('select');};
for(const b of document.querySelectorAll('[data-move]')){b.onpointerdown=e=>{e.preventDefault();b.setPointerCapture(e.pointerId);pressed.add(b.dataset.move);};const stop=()=>pressed.delete(b.dataset.move);b.onpointerup=stop;b.onpointercancel=stop;b.onlostpointercapture=stop;}
const keys={KeyW:'forward',ArrowUp:'forward',KeyS:'back',ArrowDown:'back',KeyA:'left',ArrowLeft:'left',KeyD:'right',ArrowRight:'right',KeyR:'up',KeyF:'down'};
addEventListener('keydown',e=>{if(e.target.closest('input,select,textarea'))return;if(e.code==='Escape'){pressed.clear();measures.cancel();setMode('select');return;}if(e.code==='Enter'){measures.finish();return;}if(e.code==='Delete'&&['length','area','angle'].includes(mode)){measures.deleteAtCursor();return;}if(mode==='walk'&&keys[e.code]){e.preventDefault();pressed.add(keys[e.code]);}});addEventListener('keyup',e=>pressed.delete(keys[e.code]));addEventListener('blur',()=>pressed.clear());
world.renderer.onBeforeUpdate.add(()=>{const now=performance.now(),dt=Math.min((now-lastFrame)/1000,.05);lastFrame=now;if(mode!=='walk'||!pressed.size)return;const step=Number($('#walk-speed').value)*dt,pos=controls.getPosition(new THREE.Vector3()),target=controls.getTarget(new THREE.Vector3()),forward=target.clone().sub(pos);forward.y=0;forward.normalize();const right=new THREE.Vector3().crossVectors(forward,new THREE.Vector3(0,1,0)),delta=new THREE.Vector3();if(pressed.has('forward'))delta.add(forward);if(pressed.has('back'))delta.sub(forward);if(pressed.has('right'))delta.add(right);if(pressed.has('left'))delta.sub(right);if(pressed.has('up'))delta.y++;if(pressed.has('down'))delta.y--;if(delta.lengthSq()){delta.normalize().multiplyScalar(step);pos.add(delta);target.add(delta);controls.setLookAt(...pos,...target,false);}});
let down,pointQueue=Promise.resolve();renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY,e.pointerId]);
renderer.domElement.addEventListener('pointerup',e=>run(async()=>{
 if(!down||e.pointerId!==down[2]||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5||e.button!==0)return;
 const clickMode=mode,cast={camera:world.camera.three,mouse:new THREE.Vector2(e.clientX,e.clientY),dom:renderer.domElement};
 if(['length','area','angle'].includes(clickMode)){
  cast.camera=cast.camera.clone();const snappingClasses=measures.snappings,revision=measures.revision;
  pointQueue=pointQueue.then(async()=>{if(mode!==clickMode||revision!==measures.revision)return;const hits=await model.raycastWithSnapping({...cast,snappingClasses});if(mode!==clickMode||revision!==measures.revision)return;if(!hits?.length){notify('Kein Messpunkt getroffen. Bitte direkt auf das Modell klicken.');return;}hits.sort((a,b)=>(a.snappingClass-b.snappingClass)||(a.distance-b.distance));measures.addHit(hits[0]);}).catch(error=>notify(error.message));
  measures.setPending(pointQueue);
  await pointQueue;return;
 }
 if(mode==='walk')return;cast.camera=cast.camera.clone();
 pointQueue=pointQueue.then(async()=>{
  if(mode!==clickMode)return;const hit=await model.raycast(cast);if(mode!==clickMode)return;
  if(!hit){if(mode==='select')await select(null);return;}
  if(mode==='teleport'){await startWalk(hit.point);return;}
  if(mode==='cut'){if(hit.normal)addPlane(hit.normal.clone().normalize(),hit.point);return;}
  await select(hit.localId,e.shiftKey||$('#multi-select').checked);
 }).catch(error=>notify(error.message));await pointQueue;
}));
function serializeView(){return{format:'altbau-view',version:1,position:controls.getPosition(new THREE.Vector3()).toArray(),target:controls.getTarget(new THREE.Vector3()).toArray(),projection:world.camera.projection.current,zoom:world.camera.three.zoom,visible:ids.filter(isVisible).map(id=>byId.get(id).guid),planes:[...clipper.list.values()].map(p=>({normal:p.normal.toArray(),origin:p.origin.toArray()}))};}
async function importView(raw){const data=validateView(raw,new Set(byGuid.keys()));setMode('select');orbit();hidden.clear();isolated=null;const visible=new Set(data.visible);for(const[key,g]of groups){g.visible=g.ids.some(id=>visible.has(byId.get(id).guid));inputs.get(key).checked=g.visible;inputs.get(key).indeterminate=g.visible&&g.ids.some(id=>!visible.has(byId.get(id).guid));}for(const id of ids)if(!visible.has(byId.get(id).guid))hidden.add(id);clipper.deleteAll();activePlane=null;for(const p of data.planes)addPlane(new THREE.Vector3(...p.normal),new THREE.Vector3(...p.origin));planeRows();await world.camera.projection.set(data.projection);$('#projection').value=data.projection;await controls.setLookAt(...data.position,...data.target,false);await controls.zoomTo(data.zoom??1,false);await queueVisibility();}
$('#view-export').onclick=()=>download('Altbau-Ansicht.json',serializeView());$('#view-import').onchange=e=>run(async()=>{const f=e.target.files[0];if(!f)return;try{await importView(await readJSON(f));notify('Ansicht wiederhergestellt.');}finally{e.target.value='';}});
$('#screenshot').onclick=()=>run(async()=>{await fragments.core.update(true);renderer.render(scene,world.camera.three);const canvas=document.createElement('canvas');canvas.width=renderer.domElement.width;canvas.height=renderer.domElement.height;const ctx=canvas.getContext('2d');ctx.drawImage(renderer.domElement,0,0);const rect=renderer.domElement.getBoundingClientRect(),sx=canvas.width/rect.width,sy=canvas.height/rect.height;for(const label of world.renderer.three2D.domElement.querySelectorAll('div')){if(label.children.length||!label.textContent.trim())continue;const r=label.getBoundingClientRect(),style=getComputedStyle(label);if(!r.width||!r.height||style.visibility==='hidden'||style.display==='none')continue;ctx.fillStyle='#fff';ctx.fillRect((r.left-rect.left)*sx,(r.top-rect.top)*sy,r.width*sx,r.height*sy);ctx.fillStyle='#7f3118';ctx.font=`${12*sx}px sans-serif`;ctx.fillText(label.textContent,(r.left-rect.left)*sx+3,(r.top-rect.top)*sy+14*sx);}canvas.toBlob(blob=>{if(blob)download('Altbau-Ansicht.png',blob);});});
$('#fullscreen').onclick=()=>run(()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen());
window.viewerState={groups,scene,renderer,model,fragments:fragments.core,elements,world,components,selection,measures,clipper,select,serializeView,importView,settled:()=>pending,get camera(){return world.camera.three;},get mode(){return mode;},get properties(){return lastProperties;}};setMode('select');
let resizeTimer;addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{if(mode==='select'&&world.camera.mode.id==='Orbit')run(reset);},180);});
addEventListener('viewer-layout',()=>{world.renderer.resize();world.camera.updateAspect();fragments.core.update(true);});
}catch(error){console.error(error);status.textContent='Das Modell konnte nicht geladen werden. Bitte die Seite neu laden oder die IFC-Datei herunterladen.';}
