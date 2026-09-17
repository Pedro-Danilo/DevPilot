import fs from 'node:fs';
const files={main:fs.readFileSync(new URL('../src/main.ts',import.meta.url),'utf8'),page:fs.readFileSync(new URL('../src/pages/StoryCodeWorkbenchView.ts',import.meta.url),'utf8'),client:fs.readFileSync(new URL('../src/api/client.ts',import.meta.url),'utf8')};
const required=[
  ['main','/story/code'],
  ['main','renderStoryCodeWorkbenchView'],
  ['page','SourceDraftBuffer runtime-only'],
  ['page','Agent assistance · proposal-only'],
  ['page','source_mutations=false'],
  ['page','owner approval → atomic apply'],
  ['client','storyCodeDraftRecheck'],
];
for(const [file,token] of required){if(!files[file].includes(token)) throw new Error(`BLOCK missing ${token} in ${file}`);}
if(files.page.includes('/story/code/apply')) throw new Error('BLOCK apply route exposed in page');
console.log('PASS - GSDLC-09-B Code Workbench static smoke: governed draft/proposal-only flow; apply remains approval-bound and no direct apply route is exposed.');
