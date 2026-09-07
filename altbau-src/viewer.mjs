import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {FragmentsModels} from '@thatopen/fragments';
const status=document.querySelector('#status'),view=document.querySelector('#view');
try {
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(innerWidth,innerHeight);renderer.setClearColor(0xedf0eb);view.appendChild(renderer.domElement);
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(40,innerWidth/innerHeight,.05,1000),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.maxDistance=140;controls.minDistance=1;
scene.add(new THREE.HemisphereLight(0xffffff,0x777e71,2.5));const sun=new THREE.DirectionalLight(0xfff4e4,3);sun.position.set(20,40,30);scene.add(sun);const fill=new THREE.DirectionalLight(0xe2edff,1.5);fill.position.set(-25,15,-15);scene.add(fill);
const fragments=new FragmentsModels(new URL('./vendor/worker.mjs',import.meta.url).href,{maxWorkers:2});
const defs=[['UG','Untergeschoss'],['EG','Erdgeschoss'],['OG1','1. Obergeschoss'],['OG2','2. Obergeschoss'],['Dach','Dach']],groups=new Map(),inputs=new Map();let center=new THREE.Vector3(),distance=65,model;
let pending=Promise.resolve();
function queueVisibility(){const snapshot=[...groups].map(([id,g])=>({ids:g.ids,visible:g.visible}));pending=pending.then(async()=>{for(const g of snapshot)await model.setVisible(g.ids,g.visible);await fragments.update(true);}).catch(error=>{console.error(error);status.textContent='Die Geschossansicht konnte nicht aktualisiert werden. Bitte neu laden.';});return pending;}
for(const [id,label] of defs){const row=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=true;input.disabled=true;input.dataset.floor=id;row.append(input,document.createTextNode(label));document.querySelector('#floors').append(row);inputs.set(id,input);input.addEventListener('change',()=>{groups.get(id).visible=input.checked;queueVisibility();});}
function reset(){controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(1,.72,1.15).normalize().multiplyScalar(distance*Math.max(1,.8/camera.aspect)));camera.up.set(0,1,0);controls.update();}
document.querySelector('#reset').onclick=reset;document.querySelector('#top').onclick=()=>{controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(0,distance,.001));controls.update();};
function visibility(only){if(!model)return;for(const [id,input] of inputs){input.checked=only===null||id===only;groups.get(id).visible=input.checked;}queueVisibility();}
document.querySelector('#all').onclick=()=>visibility(null);document.querySelector('#eg').onclick=()=>visibility('EG');document.querySelector('#toggle').onclick=()=>{const hidden=document.querySelector('#panel').classList.toggle('collapsed');document.querySelector('#toggle').setAttribute('aria-expanded',String(!hidden));};
controls.addEventListener('change',()=>fragments.update());
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);reset();});renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
async function fetchOK(url){const r=await fetch(url);if(!r.ok)throw Error(`${url}: ${r.status}`);return r;}
const [bytes,elements]=await Promise.all([fetchOK('./model.frag').then(r=>r.arrayBuffer()),fetchOK('./elements.json').then(r=>r.json())]);
model=await fragments.load(bytes,{modelId:'Altbau',camera});scene.add(model.object);model.useCamera(camera);
const ids=await model.getLocalIdsByGuids(elements.map(e=>e.guid)),byId=new Map();
elements.forEach((e,i)=>{if(ids[i]===null)throw Error('IFC-Element fehlt: '+e.name);byId.set(ids[i],e);});
for(const [id] of defs){groups.set(id,{ids:elements.flatMap((e,i)=>e.floor===id?[ids[i]]:[]),visible:true});inputs.get(id).disabled=false;}
model.box.getCenter(center);const size=model.box.getSize(new THREE.Vector3());distance=Math.max(size.x,size.y,size.z)*2.05;reset();await fragments.update(true);status.textContent='';
let down;renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});
renderer.domElement.addEventListener('pointerup',async e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;try{const rect=renderer.domElement.getBoundingClientRect();const hit=await model.raycast({camera,mouse:new THREE.Vector2(e.clientX-rect.left,e.clientY-rect.top),dom:renderer.domElement});const el=hit&&byId.get(hit.localId);const detail=document.querySelector('#detail');detail.replaceChildren();if(el){const title=document.createElement('strong');title.textContent=el.name;const info=document.createElement('p');info.textContent=`${el.type} · ${defs.find(d=>d[0]===el.floor)[1]} · ${el.estimated?'Foto-/Interpretationsdetail, angenähert':'Aus DXF rekonstruiert'}`;detail.append(title,info);}else detail.textContent='Bauteil antippen, um IFC-Daten anzuzeigen.';}catch(error){console.error(error);}});
window.viewerState={groups,scene,camera,renderer,model,fragments,elements,settled:()=>pending};
}catch(error){console.error(error);status.textContent='Das IFC-Modell konnte nicht angezeigt werden. Bitte den Link in einem aktuellen Browser öffnen. Die IFC-Datei kann weiterhin heruntergeladen werden.';}
