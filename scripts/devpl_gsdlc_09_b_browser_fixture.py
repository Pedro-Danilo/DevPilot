from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path
from devpilot_core.story_execution import StoryExecutionState, StoryExecutionStatus, StoryExecutionStore

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--action',choices=['prepare','external-edit','restore','status'],default='prepare'); args=ap.parse_args(); root=Path(args.root).resolve(); control=root/'.devpilot/gsdlc09b_browser_fixture.json'
 if args.action=='prepare':
  if root.exists(): shutil.rmtree(root)
  (root/'.devpilot').mkdir(parents=True); (root/'src').mkdir(parents=True)
  (root/'.devpilot/project.yaml').write_text('project_id: gsdlc-09-b-browser\nproject_name: GSDLC 09-B Browser Fixture\nproject_type: software\n',encoding='utf-8')
  original="def answer():\n    return 42\n"; (root/'src/app.py').write_text(original,encoding='utf-8'); (root/'src/view.ts').write_text("export const view = 'browser';\n",encoding='utf-8')
  state=StoryExecutionState(execution_id='story-exec-gsdlc09b-browser-000001',workspace_id=root.name,project_id='gsdlc-09-b-browser',story_id='STORY-09B-BROWSER',story_version='1.0.0',status=StoryExecutionStatus.IN_PROGRESS,sequence=1,dor_report_sha256='a'*64,context_pack_id='story-context-gsdlc09b-browser-01',context_pack_sha256='b'*64,created_at_utc='2026-09-07T12:00:00+00:00',updated_at_utc='2026-09-07T12:00:00+00:00')
  StoryExecutionStore(root,workspace_id=root.name).save_state(state)
  control.write_text(json.dumps({'source':'src/app.py','original':original,'original_sha256':sha(root/'src/app.py'),'external':'# external edit\ndef answer():\n    return 77\n'},indent=2)+'\n',encoding='utf-8')
  print('PASS - browser fixture prepared; source baseline sealed; runtime story state available.'); return 0
 if not control.is_file(): print('BLOCK - browser fixture control missing; run prepare first.'); return 2
 data=json.loads(control.read_text()); src=root/data['source']
 if args.action=='external-edit': src.write_text(data['external'],encoding='utf-8'); print('PASS - controlled external edit applied to browser fixture source.'); return 0
 if args.action=='restore': src.write_text(data['original'],encoding='utf-8'); print('PASS - browser fixture source restored to sealed baseline.'); return 0
 print(json.dumps({'root':str(root),'source':data['source'],'sha256':sha(src),'baseline_sha256':data['original_sha256'],'baseline_equal':sha(src)==data['original_sha256']},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
