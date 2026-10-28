// Real installed Chrome DOM; only API/client transport is simulated. No Ollama.
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {build}=require('esbuild');
const root=path.resolve(new URL('../../..',import.meta.url).pathname.replace(/^\/([A-Za-z]:)/,'$1'));
const focused=process.env.UX01_C_TEST_SCOPE==='selectors';
const evidence=path.join(root,'outputs',focused?'ux01_c_selectors_validation':'ux01_c_validation');
fs.mkdirSync(evidence,{recursive:true});
const chrome='C:/Program Files/Google/Chrome/Application/chrome.exe';
if(!fs.existsSync(chrome))throw new Error('BLOCK: installed Chrome unavailable; no download attempted');
const built=await build({entryPoints:[new URL('./ux01c-workbench.browser.ts',import.meta.url).pathname.replace(/^\/([A-Za-z]:)/,'$1')],bundle:true,format:'iife',target:'es2022',write:false});
const script=built.outputFiles[0].text;
const css=fs.readFileSync(new URL('../src/styles.css',import.meta.url),'utf8');
const server=http.createServer((_req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end('<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+css+'</style><body><script>'+script.replace(/<\/script/gi,'<\\/script')+'</script></body>');});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const address=server.address();
const args=['--headless=new','--disable-gpu','--no-first-run','--disable-default-apps','--disable-sync','--disable-background-networking','--no-proxy-server',
  '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost',
  '--user-data-dir='+path.join(evidence,'chrome-profile'), '--window-size=390,844','--virtual-time-budget=12000','--dump-dom',`http://127.0.0.1:${address.port}${focused?'?focus=selectors':''}`];
let stdout='',stderr='';
const child=spawn(chrome,args,{windowsHide:true});
child.stdout.on('data',b=>{stdout+=b;});child.stderr.on('data',b=>{stderr+=b;});
const exit=await new Promise((resolve,reject)=>{child.on('error',reject);child.on('close',resolve);});
server.close();
fs.writeFileSync(path.join(evidence,'browser-dom.html'),stdout);fs.writeFileSync(path.join(evidence,'browser-stderr.log'),stderr);
const raw=/<pre id="ux01c-test-result">([\s\S]*?)<\/pre>/.exec(stdout)?.[1];
if(!raw)throw new Error('BLOCK: no final browser test result; inspect outputs/ux01_c_validation/browser-stderr.log');
const result=JSON.parse(raw.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&'));
fs.writeFileSync(path.join(evidence,'browser-result.json'),JSON.stringify({...result,browser:chrome,transport:'SIMULATED',real_ollama:false,exit},null,2)+'\n');
for(const item of result.results??[])console.log(`${item.pass?'PASS':'BLOCK'} ${item.name}${item.error?' — '+item.error:''}`);
if(result.status!=='PASS'||exit!==0)process.exitCode=1;
console.log(`${result.status}: ${result.cases??0} actual Chrome DOM focal cases; simulated transport; no production server or pilot.`);
