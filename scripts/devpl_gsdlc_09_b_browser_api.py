from __future__ import annotations
import argparse, os
from pathlib import Path
import uvicorn
from devpilot_core.application import AuthApplicationService
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.interfaces.api.app import create_app

def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--platform-root',required=True); ap.add_argument('--workspace-root',required=True); ap.add_argument('--auth-root',required=True); ap.add_argument('--port',type=int,default=8787); a=ap.parse_args()
 platform=Path(a.platform_root).resolve(); workspace=Path(a.workspace_root).resolve(); auth_root=Path(a.auth_root).resolve(); auth_root.mkdir(parents=True,exist_ok=True)
 os.environ['DEVPILOT_ALLOWED_WORKSPACE_ROOTS']=str(workspace); os.environ['DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT']=str(workspace); os.environ.pop('DEVPILOT_UI_WORKSPACE_REGISTRY_PATH',None)
 auth=AuthApplicationService(auth_root,store=LocalAuthStore(auth_root)); app=create_app(platform,api_token='gsdlc09b-browser-legacy-disabled',auth_service=auth)
 print('PASS - GSDLC-09-B browser API foreground ready on 127.0.0.1:%d; transient auth root outside source.'%a.port,flush=True)
 uvicorn.run(app,host='127.0.0.1',port=a.port,log_level='warning'); return 0
if __name__=='__main__': raise SystemExit(main())
