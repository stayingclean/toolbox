export function download(name, value, mime = 'application/json') {
  const blob = value instanceof Blob ? value : new Blob([typeof value === 'string' ? value : JSON.stringify(value, null, 2)], {type: mime});
  const url = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 30000);
}
export const pointOK = value => Array.isArray(value) && value.length === 3 && value.every(n => Number.isFinite(n) && Math.abs(n) < 10000);
export function validateMeasurements(data) {
  if (data?.format !== 'altbau-measurements' || data.version !== 1 || !Array.isArray(data.measurements) || data.measurements.length > 1000) throw Error('Keine gültige Altbau-Messdatei (Version 1, maximal 1000 Messungen).');
  for (const item of data.measurements) {
    const counts = {length: [2, 2], angle: [3, 3], area: [3, 100]};
    const range = counts[item.type];
    if (!range || !Array.isArray(item.points) || item.points.length < range[0] || item.points.length > range[1] || !item.points.every(pointOK)) throw Error('Die Messdatei enthält ungültige Messpunkte.');
    const distance = (a,b) => Math.hypot(...a.map((n,i)=>n-b[i]));
    if (item.type === 'length' && distance(...item.points) < 1e-6) throw Error('Eine Länge darf nicht null sein.');
    if (item.type === 'angle' && (distance(item.points[0],item.points[1]) < 1e-6 || distance(item.points[2],item.points[1]) < 1e-6)) throw Error('Ein Winkel benötigt drei gültige Punkte.');
  }
  return data.measurements;
}
export function validateView(data, knownGuids) {
  if (data?.zoom !== undefined && (!Number.isFinite(data.zoom) || data.zoom <= 0 || data.zoom > 1000)) throw Error('Ungültiger Kamera-Zoom.');
  if (data?.format !== 'altbau-view' || data.version !== 1 || !pointOK(data.position) || !pointOK(data.target) || !['Perspective','Orthographic'].includes(data.projection)) throw Error('Keine gültige Altbau-Ansichtsdatei.');
  if (Math.hypot(...data.position.map((v,i)=>v-data.target[i]))<.001) throw Error('Kameraposition und Blickziel müssen verschieden sein.');
  if (!Array.isArray(data.visible) || data.visible.length > knownGuids.size || data.visible.some(g=>!knownGuids.has(g)) || new Set(data.visible).size !== data.visible.length) throw Error('Die Ansicht gehört zu einem anderen Modell oder enthält ungültige Bauteile.');
  if (!Array.isArray(data.planes) || data.planes.length > 12 || data.planes.some(p=>!pointOK(p.normal)||!pointOK(p.origin)||Math.abs(Math.hypot(...p.normal)-1)>.001)) throw Error('Ungültige Schnittebenen.');
  return data;
}
export async function readJSON(file) {
  if (!file || file.size > 5 * 1024 * 1024) throw Error('Bitte eine JSON-Datei mit höchstens 5 MB wählen.');
  return JSON.parse(await file.text());
}
