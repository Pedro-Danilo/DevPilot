from __future__ import annotations
import argparse, hashlib, json, os, secrets, subprocess
from datetime import datetime, timezone
from pathlib import Path

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def now()->str:return datetime.now(timezone.utc).isoformat()
def browser_executable()->str|None:
 for x in [os.environ.get('DEVPILOT_BROWSER_EXECUTABLE'),'C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','/usr/bin/chromium','/usr/bin/google-chrome']:
  if x and Path(x).is_file(): return x
 return None

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--workspace-root',required=True); ap.add_argument('--auth-root',required=True); ap.add_argument('--evidence-dir',required=True); ap.add_argument('--ui-url',default='http://127.0.0.1:5173/story/code'); ap.add_argument('--api-url',default='http://127.0.0.1:8787/api/v1'); ap.add_argument('--component-harness',action='store_true'); ap.add_argument('--component-bundle'); args=ap.parse_args()
 try: from playwright.sync_api import sync_playwright
 except Exception: print('BLOCK - Python Playwright unavailable. Use the manual browser checklist in the Windows guide; do not mark browser PASS automatically.'); return 2
 root=Path(args.workspace_root).resolve(); auth_root=Path(args.auth_root).resolve(); evidence=Path(args.evidence_dir).resolve(); evidence.mkdir(parents=True,exist_ok=True); source=root/'src/app.py'; seal=root/'.devpilot/gsdlc09b_browser_fixture.json'
 if not source.is_file() or not seal.is_file(): print('BLOCK - browser fixture not prepared.'); return 2
 baseline=json.loads(seal.read_text()); baseline_sha=baseline['original_sha256']; password='Browser09B-'+secrets.token_urlsafe(12); results=[]
 with sync_playwright() as pw:
  exe=browser_executable(); browser=pw.chromium.launch(headless=True,executable_path=exe) if exe else pw.chromium.launch(headless=True); context=browser.new_context(viewport={'width':1440,'height':1000}); req=context.request
  if args.component_harness:
   ui_url=Path(args.ui_url).resolve().as_uri() if not str(args.ui_url).startswith(('http:','file:')) else args.ui_url
  else:
   ui_url=args.ui_url
   r=req.post(args.api_url+'/auth/bootstrap/owner',headers={'Origin':'http://127.0.0.1:5173'},data={'username':'browser.owner','display_name':'Browser Owner','password':password})
   if r.status not in (201,409): print('BLOCK - transient owner bootstrap failed',r.status,r.text()); return 2
   if r.status==409:
    r=req.post(args.api_url+'/auth/login',headers={'Origin':'http://127.0.0.1:5173'},data={'username':'browser.owner','password':password})
    if r.status!=200: print('BLOCK - transient browser auth store is not fresh. Remove only the dedicated browser auth-root and retry.'); return 2
   context.add_init_script("sessionStorage.setItem('devpilot.gsdlc03e.projectJourneyContext.v1', JSON.stringify({phase:'project',entry_mode:'OPEN_EXISTING',project_id:'gsdlc-09-b-browser',target_root:"+json.dumps(str(root))+",activated_at:new Date().toISOString()}));")
  page=context.new_page();
  if args.component_harness:
   if not args.component_bundle: print('BLOCK - component bundle missing.'); return 2
   page.set_content('<!doctype html><html><body><main id="app"></main></body></html>')
   # set_content() runs under an opaque origin in the controlled tool environment, where
   # Chromium denies native sessionStorage access. The component harness therefore uses
   # an in-memory browser-local storage shim only for this isolated transport-mock mode.
   # Live Windows acceptance never uses this shim.
   page.evaluate("""Object.defineProperty(globalThis,'sessionStorage',{value:{_m:new Map(),getItem(k){return this._m.has(k)?this._m.get(k):null},setItem(k,v){this._m.set(k,String(v))},removeItem(k){this._m.delete(k)},clear(){this._m.clear()}},configurable:true}); Object.defineProperty(document,'cookie',{value:'',writable:true,configurable:true});""")
   page.add_script_tag(path=str(Path(args.component_bundle).resolve()))
  else: page.goto(ui_url,wait_until='load')
  page.locator('[data-gsdlc09b="code-workbench"]').wait_for(); page.locator('[data-source-path="src/app.py"]').wait_for(); page.screenshot(path=str(evidence/'01_story_code_ready.png'),full_page=True); results.append(('open-story-context',True))
  item=page.locator('[data-source-path="src/app.py"]'); item.click(); page.locator('[data-draft-editor="true"]').wait_for(); before=sha(source); results.append(('navigate-source',before==baseline_sha))
  editor=page.locator('[data-draft-editor="true"]'); editor.fill('def answer():\n    return 43\n'); page.locator('[data-save-draft="true"]').click(); page.get_by_text('PASS · draft guardado; source real permanece sin cambios.').wait_for(); results.append(('draft-source-unchanged',sha(source)==before==baseline_sha)); page.screenshot(path=str(evidence/'02_draft_saved_source_unchanged.png'),full_page=True)
  page.get_by_label('Operación de draft').select_option('CREATE'); page.locator('[data-target-path="true"]').fill('../escape.py'); editor.fill('x=1\n'); page.locator('[data-save-draft="true"]').click(); page.get_by_text('BLOCK ·',exact=False).wait_for(); results.append(('path-escape-block',True)); page.screenshot(path=str(evidence/'03_path_escape_block.png'),full_page=True)
  item.click(); editor.fill('def answer():\n    return 44\n'); page.locator('[data-save-draft="true"]').click(); page.get_by_text('PASS · draft guardado; source real permanece sin cambios.').wait_for()
  subprocess.run([os.sys.executable,str(Path(__file__).with_name('devpl_gsdlc_09_b_browser_fixture.py')),'--root',str(root),'--action','external-edit'],check=True,capture_output=True,text=True)
  if args.component_harness: page.evaluate('globalThis.__externalEdit=true')
  page.locator('[data-recheck-draft="true"]').click(); page.get_by_text('CONFLICT · external edit/revalidation requerida').wait_for(); results.append(('external-edit-conflict-visible',True)); page.screenshot(path=str(evidence/'04_external_edit_conflict.png'),full_page=True)
  if args.component_harness:
   role_url=ui_url+'?role=architect'
  else:
   from devpilot_core.identity.auth_store import LocalAuthStore
   LocalAuthStore(auth_root).update_identity_authority('local-owner',roles=('architect',),workspace_scopes=('devpilot-local',),changed_at=now()); context.clear_cookies(); rr=req.post(args.api_url+'/auth/login',headers={'Origin':'http://127.0.0.1:5173'},data={'username':'browser.owner','password':password}); results.append(('architect-login',rr.status==200)); role_url=ui_url
  
  if args.component_harness:
   # A fresh Chromium page is required: set_content() replaces DOM but does not provide a
   # reliable fresh global lexical environment for reinjecting the bundled `const`s.
   role_page=context.new_page()
   role_page.set_content('<!doctype html><html><body><main id="app"></main></body></html>')
   role_page.evaluate("""Object.defineProperty(globalThis,'sessionStorage',{value:{_m:new Map(),getItem(k){return this._m.has(k)?this._m.get(k):null},setItem(k,v){this._m.set(k,String(v))},removeItem(k){this._m.delete(k)},clear(){this._m.clear()}},configurable:true}); Object.defineProperty(document,'cookie',{value:'',writable:true,configurable:true}); globalThis.__role='architect';""")
   role_page.add_script_tag(path=str(Path(args.component_bundle).resolve()))
  else:
   page.goto(role_url,wait_until='load')
   role_page=page
  role_page.locator('[data-gsdlc09b="code-workbench"]').wait_for(); role_page.locator('[data-source-path="src/app.py"]').click(); results.append(('role-negative-authoring-disabled',role_page.locator('[data-save-draft="true"]').is_disabled())); role_page.screenshot(path=str(evidence/'05_role_negative_read_only.png'),full_page=True); browser.close()
 subprocess.run([os.sys.executable,str(Path(__file__).with_name('devpl_gsdlc_09_b_browser_fixture.py')),'--root',str(root),'--action','restore'],check=True,capture_output=True,text=True); restored=sha(source)==baseline_sha; results.append(('source-restored',restored))
 ok=all(v for _,v in results); report={'schema_id':'DEVPL-GSDLC-09-B-BROWSER-ACCEPTANCE-V1','status':'PASS' if ok else 'BLOCK','mode':'browser-real/component-mock-transport' if args.component_harness else 'browser-real/live-api-ui','cases':[{'id':k,'pass':v} for k,v in results],'screenshots':sorted(p.name for p in evidence.glob('*.png')),'source_baseline_sha256':baseline_sha,'source_restored':restored,'full_regression_runs':0,'browser_runs':1,'network_runtime_used':False,'external_api_used':False,'source_mutations_performed_by_workbench':False,'generated_at_utc':now()}; (evidence/'DEVPL_GSDLC_09_B_BROWSER_ACCEPTANCE.json').write_text(json.dumps(report,indent=2)+'\n'); print(('PASS' if ok else 'BLOCK')+f' - browser acceptance {sum(1 for _,v in results if v)}/{len(results)}'); return 0 if ok else 2
if __name__=='__main__': raise SystemExit(main())
