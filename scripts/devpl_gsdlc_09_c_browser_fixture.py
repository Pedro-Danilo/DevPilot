from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path
from devpilot_core.story_execution import StoryExecutionState, StoryExecutionStatus, StoryExecutionStore

def semantic_sha(p:Path)->str:
 raw=p.read_bytes()
 try: raw=raw.decode('utf-8').replace('\r\n','\n').replace('\r','\n').encode('utf-8')
 except UnicodeDecodeError: pass
 return hashlib.sha256(raw).hexdigest()
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--action',choices=['prepare','external-edit','restore','status'],default='prepare');a=ap.parse_args();root=Path(a.root).resolve();ctl=root/'.devpilot/gsdlc09c_browser_fixture.json'
 if a.action=='prepare':
  if root.exists():shutil.rmtree(root)
  (root/'.devpilot').mkdir(parents=True);(root/'src').mkdir(parents=True)
  (root/'.devpilot/project.yaml').write_text('project_id: gsdlc-09-c-browser\nproject_name: GSDLC 09-C Browser Fixture\nproject_type: software\n',encoding='utf-8')
  original='def answer():\n    return 42\n';(root/'src/app.py').write_text(original,encoding='utf-8');(root/'src/util.py').write_text('VALUE = 1\n',encoding='utf-8')
  s=StoryExecutionState(execution_id='story-exec-gsdlc09c-browser-000001',workspace_id=root.name,project_id='gsdlc-09-c-browser',story_id='STORY-09C-BROWSER',story_version='1.0.0',status=StoryExecutionStatus.IN_PROGRESS,sequence=1,dor_report_sha256='a'*64,context_pack_id='story-context-gsdlc09c-browser-01',context_pack_sha256='b'*64,created_at_utc='2026-09-08T12:00:00+00:00',updated_at_utc='2026-09-08T12:00:00+00:00')
  StoryExecutionStore(root,workspace_id=root.name).save_state(s)
  ctl.write_text(json.dumps({'source':'src/app.py','original':original,'original_sha256':semantic_sha(root/'src/app.py'),'external':'# controlled external edit\ndef answer():\n    return 77\n'},indent=2)+'\n',encoding='utf-8')
  print('PASS - GSDLC-09-C browser fixture prepared and source baseline sealed.');return 0
 if not ctl.is_file():print('BLOCK - fixture control missing.');return 2
 d=json.loads(ctl.read_text());src=root/d['source']
 if a.action=='external-edit':src.write_text(d['external'],encoding='utf-8');print('PASS - controlled external edit applied.');return 0
 if a.action=='restore':src.write_text(d['original'],encoding='utf-8');print('PASS - source restored to sealed baseline.');return 0
 print(json.dumps({'root':str(root),'sha256':semantic_sha(src),'baseline_sha256':d['original_sha256'],'baseline_equal':semantic_sha(src)==d['original_sha256']},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
