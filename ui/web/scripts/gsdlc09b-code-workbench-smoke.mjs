import fs from 'node:fs';
const files={main:fs.readFileSync(new URL('../src/main.ts',import.meta.url),'utf8'),page:fs.readFileSync(new URL('../src/pages/StoryCodeWorkbenchView.ts',import.meta.url),'utf8'),client:fs.readFileSync(new URL('../src/api/client.ts',import.meta.url),'utf8')};
const required=[['main','/story/code'],['main','renderStoryCodeWorkbenchView'],['page','DRAFT ONLY'],['page','APPLY NO DISPONIBLE HASTA 09-C'],['page','source_mutations=false'],['client','storyCodeDraftRecheck']];
for(const [file,token] of required){if(!files[file].includes(token)) throw new Error(`BLOCK missing ${token} in ${file}`);}
for(const forbidden of ['terminal','/story/code/apply']){if(files.page.includes(forbidden) && forbidden==='/story/code/apply') throw new Error('BLOCK apply route exposed in page');}
console.log('PASS - GSDLC-09-B Code Workbench static smoke: bounded draft-only UI, no apply route.');
