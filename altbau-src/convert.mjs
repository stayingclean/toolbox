import {IfcImporter} from '@thatopen/fragments';
import fs from 'node:fs/promises';
const importer=new IfcImporter();
importer.wasm={path:new URL('./node_modules/web-ifc/',import.meta.url).pathname.replace(/^\/([A-Za-z]:)/,'$1'),absolute:true};
importer.replaceStoreyElevation=false;importer.replaceSiteElevation=false;
const path=new URL('../docs/altbau/',import.meta.url);
const data=await importer.process({bytes:new Uint8Array(await fs.readFile(new URL('model.ifc',path)))});
await fs.writeFile(new URL('model.frag',path),data);
console.log('Fragments exported',data.length);

