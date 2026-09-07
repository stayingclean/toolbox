// Convert IFC's cyclic relation graph into a finite, readable property tree.
export function propertyTree(data, seen = new WeakSet(), depth = 0) {
  if (!data || typeof data !== 'object') return data;
  if (seen.has(data) || depth > 8) return null;
  seen.add(data);
  if (Array.isArray(data)) return data.map(v => propertyTree(v, seen, depth + 1)).filter(v => v !== null);
  if ('value' in data) return data.value;
  const out = {};
  for (const [key, value] of Object.entries(data)) {
    if (['DefinesOccurrence', 'DefinesType', '_localId'].includes(key)) continue;
    const result = propertyTree(value, seen, depth + 1);
    if (result !== null && (!Array.isArray(result) || result.length)) out[key] = result;
  }
  return out;
}

export async function readProperties(model, id) {
  const [data] = await model.getItemsData([id], {
    attributesDefault: true,
    relations: Object.fromEntries(['IsDefinedBy', 'HasProperties', 'Quantities', 'HasAssociations', 'RelatingMaterial', 'Materials', 'MaterialLayers', 'Material', 'ForLayerSet', 'IsTypedBy', 'HasPropertySets'].map(k => [k, {attributes: true, relations: true}])),
    relationsDefault: {attributes: false, relations: false},
  });
  return propertyTree(data);
}

const labels = {_category: 'IFC-Klasse', _guid: 'IFC-GUID', Name: 'Name', Description: 'Beschreibung', IsDefinedBy: 'Property-Sets', HasProperties: 'Eigenschaften', NominalValue: 'Wert', HasAssociations: 'Zuordnungen', IsTypedBy: 'Bauteiltyp', HasPropertySets: 'Typ-Eigenschaften'};
export function renderProperties(container, data) {
  container.replaceChildren();
  function append(parent, obj) {
    const table = document.createElement('table'); table.className = 'property-table';
    for (const [key, value] of Object.entries(obj || {})) {
      if (value && typeof value === 'object') continue;
      const row = table.insertRow(); const th = document.createElement('th'); th.textContent = labels[key] || key;
      const td = document.createElement('td'); td.textContent = value === null ? '—' : String(value); row.append(th, td);
    }
    if (table.rows.length) parent.append(table);
    for (const [key, value] of Object.entries(obj || {})) {
      if (!value || typeof value !== 'object') continue;
      const section = document.createElement('details'); section.open = true;
      const title = document.createElement('summary'); title.textContent = labels[key] || key; section.append(title);
      for (const entry of Array.isArray(value) ? value : [value]) {
        if (entry && typeof entry === 'object') append(section, entry);
      }
      parent.append(section);
    }
  }
  append(container, data);
  if (!container.childNodes.length) container.textContent = 'Keine weiteren Eigenschaften im IFC vorhanden.';
}
