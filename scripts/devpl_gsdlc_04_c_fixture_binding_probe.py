from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PROBE_ID="DEVPL-GSDLC-04-C-FIXTURE-BINDING-PROBE"
VERSION="1.0.0"
DEFAULT_FIXTURE=r"D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_C_BROWSER"

def ansi()->None:
    if os.name!='nt': return
    try:
        import ctypes
        k=ctypes.windll.kernel32; h=k.GetStdHandle(-11); m=ctypes.c_uint32()
        if k.GetConsoleMode(h,ctypes.byref(m)): k.SetConsoleMode(h,m.value|0x0004)
    except Exception: pass

def verdict(status:str,msg:str)->None:
    ansi(); c='\x1b[92m' if status=='PASS' else '\x1b[91m'; print(f'{c}{status} — {msg}\x1b[0m',flush=True)

def git_state(f:Path)->tuple[str,list[str]]:
    h=subprocess.run(['git','rev-parse','HEAD'],cwd=str(f),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,shell=False)
    if h.returncode!=0: raise RuntimeError('Fixture no es Git válido.')
    s=subprocess.run(['git','status','--porcelain=v1','-z'],cwd=str(f),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,shell=False)
    if s.returncode!=0: raise RuntimeError('No se pudo inspeccionar Git status del fixture.')
    rows=[x.decode('utf-8',errors='replace') for x in s.stdout.split(b'\0') if x]
    return h.stdout.strip(),rows

def main()->int:
    p=argparse.ArgumentParser(description='Read-only 04-C PathGuard/UI binding precheck.')
    p.add_argument('--repo-root',required=True); p.add_argument('--browser-fixture-root',default=DEFAULT_FIXTURE); a=p.parse_args()
    repo=Path(a.repo_root).resolve(); fixture=Path(a.browser_fixture_root).resolve()
    try:
        if not repo.is_dir(): raise RuntimeError(f'Repo root no existe: {repo}')
        if fixture!=Path(DEFAULT_FIXTURE).resolve(): raise RuntimeError(f'Fixture debe ser exactamente {DEFAULT_FIXTURE}.')
        if not fixture.is_dir(): raise RuntimeError(f'Fixture no existe: {fixture}')
        if 'inventory-sales-local' in str(fixture).lower() or 'devpilot_workspaces' in str(fixture).lower(): raise RuntimeError('Workspace piloto real prohibido.')
        missing=[str(x) for x in [fixture/'.devpilot/project.yaml',fixture/'docs/baseline.md',fixture/'docs/baseline.json'] if not x.is_file()]
        if missing: raise RuntimeError(f'Fixture incompleto: {missing}')
        head,rows=git_state(fixture)
        if rows: raise RuntimeError(f'Fixture debe estar Git clean antes de Project Entry: {rows}')
        os.environ['DEVPILOT_ALLOWED_WORKSPACE_ROOTS']=str(fixture); os.environ['DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT']=str(fixture); os.environ.pop('DEVPILOT_UI_WORKSPACE_REGISTRY_PATH',None)
        from devpilot_core.application.ui_workspace_context import UiWorkspaceContextResolver
        from devpilot_core.workspace.project_entry_contracts import ProjectEntryContractService
        from devpilot_core.workspace.project_entry_dry_run import ProjectEntryDryRunService
        intake:dict[str,Any]={
          'schema_id':'SCHEMA-DEVPL-GSDLC-03-A-PROJECT-INTAKE-V1','schema_version':'1.0','project_id':'gsdlc04c-browser','project_name':'GSDLC 04-C browser fixture','project_type':'agent-assisted-sdlc','entry_mode':'OPEN_EXISTING','target_root':str(fixture),
          'stack':{'frontend':'react-typescript','backend':'fastapi-python','database':'sqlite'},'standards':['MIPSoftware','MIASI'],'provider':{'mode':'none','provider_id':None},
          'restrictions':{'arbitrary_shell_allowed':False,'silent_network_allowed':False,'remote_git_execute_allowed':False},
        }
        contract=ProjectEntryContractService(repo).validate_intake(intake); dry=ProjectEntryDryRunService(repo).dry_run(intake=intake); context=UiWorkspaceContextResolver(repo).resolve()
        if not contract.ok: raise RuntimeError(f'ProjectIntake/PathGuard BLOCK: {contract.to_dict()}')
        if not dry.ok: raise RuntimeError(f'Project Entry dry-run precheck BLOCK: {dry.to_dict()}')
        if not context.valid or context.active_workspace_root!=fixture: raise RuntimeError(f'UI workspace context no resolvió fixture exacto: {context.summary()}')
        payload={'status':'PASS','probe_id':PROBE_ID,'version':VERSION,'fixture':str(fixture),'project_intake_ok':True,'dry_run_ok':True,'dry_run_writes_performed':bool(dry.data.get('writes_performed',False)),'dry_run_network_used':bool(dry.data.get('network_used',False)),'ui_workspace_context':context.summary(),'fixture_git_clean':True,'fixture_git_head':head,'pilot_workspace_accessed':False}
        print(json.dumps(payload,indent=2,ensure_ascii=False)); verdict('PASS','fixture binding + Project Entry dry-run precheck completado'); return 0
    except Exception as exc:
        payload={'status':'BLOCK','probe_id':PROBE_ID,'version':VERSION,'message':str(exc)}; print(json.dumps(payload,indent=2,ensure_ascii=False)); verdict('BLOCK',str(exc).splitlines()[0]); return 20

if __name__=='__main__': raise SystemExit(main())
