import {build} from 'esbuild';
import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const dest=new URL('../docs/altbau/',import.meta.url);
await build({entryPoints:[fileURLToPath(new URL('./main.mjs',import.meta.url))],bundle:true,format:'esm',minify:true,outfile:fileURLToPath(new URL('viewer.js',dest)),legalComments:'linked'});
await fs.copyFile(new URL('./node_modules/@thatopen/fragments/dist/Worker/worker.mjs',import.meta.url),new URL('vendor/worker.mjs',dest));
const html=(await fs.readFile(new URL('./viewer.html',import.meta.url),'utf8')).trimEnd()+'\n';
await fs.writeFile(new URL('index.html',dest),html);
await fs.writeFile(new URL('../altbau-viewer.html',import.meta.url),html);
