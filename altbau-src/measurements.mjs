import * as THREE from 'three';
import * as OBF from '@thatopen/components-front';
import {SnappingClass} from '@thatopen/fragments';
import {download, readJSON, validateMeasurements} from './files.mjs';

export function setupMeasurements(components, world, notify, run) {
  const tools = {length: components.get(OBF.LengthMeasurement), area: components.get(OBF.AreaMeasurement), angle: components.get(OBF.AngleMeasurement)};
  let active = null, activeType = null, points = [], revision = 0, pending = Promise.resolve();
  const preview = new THREE.Group(); world.scene.three.add(preview);
  const unit = document.querySelector('#measure-unit'), list = document.querySelector('#measure-list');
  for (const [key, tool] of Object.entries(tools)) {
    tool.world = world; tool.color = new THREE.Color('#b34219'); tool.rounding = 2;
    tool.units = key === 'length' ? 'cm' : key === 'area' ? 'm2' : 'deg';
    tool.snappings = [SnappingClass.POINT, SnappingClass.LINE, SnappingClass.FACE].filter(v=>v!==undefined);
    tool.enabled = false;
    tool.list.onItemAdded.add(render); tool.list.onItemDeleted.add(render); tool.list.onCleared.add(render);
  }
  function render() {
    list.replaceChildren(); let count = 0;
    for (const [type, tool] of Object.entries(tools)) for (const item of tool.list) {
      count++; item.units = tool.units; item.rounding = 2;
      const row = document.createElement('div'); row.className = 'measurement-row';
      const text = document.createElement('span'); text.textContent = `${{length:'Länge',area:'Fläche',angle:'Winkel'}[type]} ${count}: ${item.value.toLocaleString('de-CH')} ${tool.units.replace('m2','m²').replace('deg','°')}`;
      const del = document.createElement('button'); del.textContent = '×'; del.title = 'Diese Messung löschen'; del.setAttribute('aria-label', `Messung ${count} löschen`); del.onclick = ()=>tool.list.delete(item);
      row.append(text, del); list.append(row);
    }
    if (!count) list.textContent = 'Noch keine Messungen.';
  }
  function setMode(mode) {
    cancel();
    // Explicit click coordinates avoid the native preview pick's asynchronous cache.
    for (const tool of Object.values(tools)) tool.enabled = false;
    active = tools[mode] || null; activeType = active ? mode : null;
  }
  function clearPreview(){for(const child of [...preview.children]){child.geometry?.dispose();child.material?.dispose();preview.remove(child);}}
  function cancel(){revision++;points=[];clearPreview();}
  function drawPreview(){clearPreview();if(!points.length)return;const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color:'#b34219',depthTest:false}));line.renderOrder=10;preview.add(line);for(const p of points){const dot=new THREE.Mesh(new THREE.SphereGeometry(.04,8,6),new THREE.MeshBasicMaterial({color:'#b34219',depthTest:false}));dot.position.copy(p);dot.renderOrder=11;preview.add(dot);}}
  function finish(){
    if(!active)return;
    const required=activeType==='length'?2:3;if(points.length<required){notify(`Noch ${required-points.length} Messpunkt(e) setzen.`);return;}
    let item;
    if(activeType==='length')item=new OBF.Line(...points);
    else if(activeType==='angle')item=new OBF.Angle(...points);
    else{item=new OBF.Area(points);if(!item.plane||item.rawValue<=1e-8||points.some(p=>Math.abs(item.plane.distanceToPoint(p))>.005)){notify('Die Fläche benötigt mindestens drei nicht kollineare Punkte in derselben Ebene.');return;}}
    item.units=active.units;item.rounding=2;active.list.add(item);cancel();render();
  }
  function addHit(hit){
    if(!active||!hit?.point)return;
    if(activeType==='length'&&tools.length.mode==='edge'){
      if(!hit.snappedEdgeP1||!hit.snappedEdgeP2){notify('Bitte direkt auf eine Kante klicken.');return;}
      points=[hit.snappedEdgeP1.clone(),hit.snappedEdgeP2.clone()];finish();return;
    }
    if(points.length&&points.at(-1).distanceTo(hit.point)<1e-5){notify('Bitte einen anderen Messpunkt wählen.');return;}
    if(points.length>=100)throw Error('Maximal 100 Punkte pro Fläche.');
    points.push(hit.point.clone());drawPreview();
    if((activeType==='length'&&points.length===2)||(activeType==='angle'&&points.length===3))finish();
    else notify(`${points.length} Messpunkt(e) gesetzt.`);
  }
  function serialize() {
    const measurements = [];
    for (const [type, tool] of Object.entries(tools)) for (const item of tool.list) {
      const points = type === 'area' ? [...item.points] : type === 'angle' ? [item.start,item.vertex,item.end] : [item.start,item.end];
      measurements.push({type, points: points.map(p=>p.toArray())});
    }
    return {format:'altbau-measurements', version:1, coordinateSystem:'Three.js Y-up, metres', measurements};
  }
  function importData(data) {
    const records = validateMeasurements(data);
    // Validate all geometry before replacing existing user work.
    const prepared = records.map(record=>{
      const p = record.points.map(v=>new THREE.Vector3(...v));
      const item = record.type === 'length' ? new OBF.Line(...p) : record.type === 'angle' ? new OBF.Angle(...p) : new OBF.Area(p);
      if (record.type === 'area' && (!item.plane || !Number.isFinite(item.rawValue) || item.rawValue <= 1e-8 || p.some(v=>Math.abs(item.plane.distanceToPoint(v))>.005))) throw Error('Flächen benötigen mindestens drei Punkte in derselben Ebene.');
      item.units = tools[record.type].units; return [record.type, item];
    });
    clear(); for (const [type,item] of prepared) tools[type].list.add(item); render();
  }
  function clear() { cancel(); for (const tool of Object.values(tools)) {tool.cancelCreation();tool.list.clear();} render(); }
  unit.onchange = ()=>{tools.length.units=unit.value;render();};
  document.querySelector('#measure-snap').onchange = e=>{for(const tool of Object.values(tools))tool.snappings=e.target.checked?[SnappingClass.POINT,SnappingClass.LINE,SnappingClass.FACE].filter(v=>v!==undefined):[SnappingClass.FACE];};
  document.querySelector('#measure-edge').onchange = e=>{tools.length.mode=e.target.checked?'edge':'free';};
  document.querySelector('#measure-finish').onclick = ()=>pending.then(finish);
  document.querySelector('#measure-cancel').onclick = ()=>{cancel();notify('Begonnene Messung abgebrochen.');};
  document.querySelector('#measure-clear').onclick = clear;
  document.querySelector('#measure-export').onclick = ()=>download('Altbau-Messungen.json',serialize());
  document.querySelector('#measure-import').onchange = e=>run(async()=>{const file=e.target.files[0];if(!file)return;try{importData(await readJSON(file));notify('Messungen geladen.');}finally{e.target.value='';}});
  render();
  return {tools,setMode,serialize,importData,clear,addHit,finish:()=>pending.then(finish),cancel,setPending:p=>pending=p,get revision(){return revision;},get pointCount(){return points.length;},get snappings(){return activeType==='length'&&tools.length.mode==='edge'?[SnappingClass.LINE]:active?.snappings;},deleteAtCursor:()=>{const item=active&&[...active.list].at(-1);if(item)active.list.delete(item);}};
}
