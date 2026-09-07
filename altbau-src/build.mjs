import {build} from 'esbuild';
import fs from 'node:fs/promises';
const dest=new URL('../docs/altbau/',import.meta.url);
await build({entryPoints:[new URL('./viewer.mjs',import.meta.url).pathname.replace(/^\/([A-Za-z]:)/,'$1')],bundle:true,format:'esm',minify:true,outfile:new URL('viewer.js',dest).pathname.replace(/^\/([A-Za-z]:)/,'$1'),legalComments:'linked'});
await fs.copyFile(new URL('./node_modules/@thatopen/fragments/dist/Worker/worker.mjs',import.meta.url),new URL('vendor/worker.mjs',dest));

