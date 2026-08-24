from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_ID="DEVPL-GSDLC-04-E-RUNTIME-CONSOLE"
VERSION="1.0.2"
DEFAULT_FIXTURE=r"D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER"
REQUIRED_FIXTURE_FILES=(
    ".gitignore",
    ".devpilot/project.yaml",
    "docs/manual_authoring.md",
    "docs/manual_authoring.json",
    "docs/baseline.md",
)
ALLOWED_BROWSER_DIRTY_PATHS={
    "docs/gsdlc04e_import.md",
    "docs/manual_authoring.md",
    "docs/manual_authoring.json",
    "docs/gsdlc04e_review_candidate.md",
    "docs/gsdlc04e_stale_target.md",
}

B15_BASELINE_PATH="docs/baseline.md"
B15_TARGET_PATH="docs/gsdlc04e_review_candidate.md"
B15_RECOVERY_PREFLIGHT="recovery_009/recovery_009_preflight.json"
FULL_REGRESSION_MARKER="DEVPL_GSDLC_04_E_FULL_REGRESSION_RUN_MARKER.json"


def now()->str: return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def ansi()->None:
    if os.name!='nt': return
    try:
        import ctypes
        k=ctypes.windll.kernel32; h=k.GetStdHandle(-11); m=ctypes.c_uint32()
        if k.GetConsoleMode(h,ctypes.byref(m)): k.SetConsoleMode(h,m.value|0x0004)
    except Exception: pass

def verdict(status:str,msg:str)->None:
    ansi(); c='\x1b[92m' if status=='PASS' else '\x1b[91m'; print(f'{c}{status} — {msg}\x1b[0m',flush=True)

def port_open(port:int)->bool:
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=.5): return True
    except OSError: return False

def ready(url:str)->bool:
    try:
        with urllib.request.urlopen(url,timeout=1.5) as r: return 200<=r.status<500
    except Exception: return False

def git_clean(fixture:Path)->tuple[bool,list[str]]:
    cp=subprocess.run(['git','status','--porcelain=v1','-z'],cwd=str(fixture),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,shell=False)
    if cp.returncode!=0: raise RuntimeError(cp.stderr.decode(errors='replace')[-2000:])
    rows=[x.decode('utf-8',errors='replace') for x in cp.stdout.split(b'\0') if x]
    return not rows,rows

def _dirty_rel(row:str)->str:
    value=row[3:] if len(row)>=4 else row
    if ' -> ' in value: value=value.split(' -> ')[-1]
    return value.strip('"').replace('\\','/')

def _sha_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def _sha(path:Path)->str:
    return _sha_bytes(path.read_bytes())

def _execution_record(repo:Path,execution_id:str)->tuple[Path,dict[str,Any]]:
    candidates=[repo/'outputs'/'uoc005_control'/'records'/f'{execution_id}.json']
    outputs=repo/'outputs'
    if outputs.is_dir():
        for candidate in outputs.glob(f'**/records/{execution_id}.json'):
            if candidate not in candidates: candidates.append(candidate)
    for candidate in candidates:
        if candidate.is_file():
            try:
                return candidate,json.loads(candidate.read_text(encoding='utf-8'))
            except (OSError,json.JSONDecodeError) as exc:
                raise RuntimeError(f'Execution record B15 inválido: {candidate}: {exc}') from exc
    raise RuntimeError(f'Execution record B15 no encontrado para {execution_id}.')

def _allow_b15_applied_runtime(repo:Path,fixture:Path,evidence:Path,dirty_paths:list[str])->dict[str,Any]:
    expected_dirty=sorted([B15_BASELINE_PATH,B15_TARGET_PATH])
    if sorted(dirty_paths)!=expected_dirty:
        raise RuntimeError(f'B15 applied runtime requiere dirty scope exacto {expected_dirty}; actual={sorted(dirty_paths)}.')
    authority=evidence/B15_RECOVERY_PREFLIGHT
    if not authority.is_file():
        raise RuntimeError(f'Falta authority Recovery-009 para aceptar baseline aplicado: {authority}.')
    try:
        preflight=json.loads(authority.read_text(encoding='utf-8'))
    except (OSError,json.JSONDecodeError) as exc:
        raise RuntimeError(f'Authority Recovery-009 inválida: {exc}') from exc
    if preflight.get('status')!='PASS' or preflight.get('resume_mode')!='ROLLBACK_REAUTH_NEW_RUNTIME':
        raise RuntimeError('Recovery-009 preflight no autoriza fresh-runtime rollback continuation.')
    b15=dict(preflight.get('recognized_resume_state',{}).get('b15') or {})
    execution_id=str(b15.get('execution_id') or '')
    if not execution_id:
        raise RuntimeError('Recovery-009 preflight no contiene execution_id B15.')
    record_path,record=_execution_record(repo,execution_id)
    if str(record.get('status') or '')!='applied':
        raise RuntimeError(f'Execution B15 ya no está applied: {record.get("status")!r}.')
    if str(record.get('relative_path') or '')!=B15_BASELINE_PATH:
        raise RuntimeError(f'Execution B15 apunta a {record.get("relative_path")!r}, no a {B15_BASELINE_PATH}.')
    baseline=fixture/B15_BASELINE_PATH
    if not baseline.is_file():
        raise RuntimeError('docs/baseline.md no existe en fixture B15.')
    current_sha=_sha(baseline)
    post_sha=str(record.get('post_sha256') or '')
    pre_sha=str(record.get('pre_sha256') or '')
    if current_sha!=post_sha or current_sha!=str(b15.get('record_post_sha256') or ''):
        raise RuntimeError(f'Baseline B15 no coincide con post SHA persistido: current={current_sha} record_post={post_sha}.')
    blob=subprocess.run(['git','show',f'HEAD:{B15_BASELINE_PATH}'],cwd=str(fixture),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,shell=False)
    if blob.returncode!=0:
        raise RuntimeError('No se pudo leer Git preimage de docs/baseline.md.')
    git_pre_sha=_sha_bytes(blob.stdout)
    if git_pre_sha!=pre_sha or git_pre_sha!=str(b15.get('record_pre_sha256') or ''):
        raise RuntimeError(f'Git preimage B15 no coincide con execution authority: git={git_pre_sha} record_pre={pre_sha}.')
    if (evidence/FULL_REGRESSION_MARKER).exists():
        raise RuntimeError('Full regression marker ya existe; no se autoriza recovery runtime B15 después de la corrida única.')
    if any((evidence/name).exists() for name in ('15_rollback_verify_v1_0_9.json','15_rollback_verify_v1_0_10.json')):
        raise RuntimeError('Rollback verification ya existe; baseline aplicado no debe reabrirse como fresh-runtime rollback.')
    return {
        'mode':'b15-applied-rollback-recovery',
        'execution_id':execution_id,
        'execution_record_path':str(record_path),
        'execution_status':'applied',
        'pre_sha256':pre_sha,
        'post_sha256':post_sha,
        'dirty_paths':expected_dirty,
        'authority':'persisted-uoc005-execution+recovery009-preflight+git-preimage',
    }

def validate_fixture(raw:str,repo:Path,evidence:Path)->tuple[Path,dict[str,Any]]:
    f=Path(raw).resolve(); expected=Path(DEFAULT_FIXTURE).resolve()
    if f!=expected: raise RuntimeError(f'Fixture 04-E no autorizado: {f}; esperado exactamente {expected}.')
    if not f.is_dir() or not (f/'.git').exists(): raise RuntimeError('Fixture 04-E no existe o no es Git; ejecute prepare-browser desde Consola 1.')
    required=[f/Path(rel) for rel in REQUIRED_FIXTURE_FILES]
    missing=[str(x) for x in required if not x.is_file()]
    if missing: raise RuntimeError(f'Fixture incompleto: {missing}')
    if 'inventory-sales-local' in str(f).lower() or 'devpilot_workspaces' in str(f).lower(): raise RuntimeError('Workspace piloto real prohibido en 04-E.')
    clean,rows=git_clean(f)
    policy={'mode':'clean','dirty_paths':[]}
    if not clean:
        paths=sorted(_dirty_rel(row) for row in rows)
        if B15_BASELINE_PATH in paths:
            policy=_allow_b15_applied_runtime(repo,f,evidence,paths)
        else:
            unexpected=[row for row in rows if _dirty_rel(row) not in ALLOWED_BROWSER_DIRTY_PATHS]
            if unexpected: raise RuntimeError(f'Fixture Git dirty fuera del browser scope 04-E: {unexpected}. No use git clean/reset; preserve evidencia.')
            policy={'mode':'browser-allowed-dirty','dirty_paths':paths,'authority':'static-browser-scope'}
    return f,policy

def stop(proc:subprocess.Popen[Any])->None:
    if proc.poll() is not None: return
    if os.name=='nt':
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,shell=False)
        time.sleep(.8)
        if proc.poll() is None: subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,shell=False)
    else:
        try: os.killpg(os.getpgid(proc.pid),signal.SIGTERM)
        except Exception: proc.terminate()

def main()->int:
    p=argparse.ArgumentParser(description='Dedicated 04-E API/UI launcher. Use separate Console 2/3.')
    p.add_argument('--role',choices=['api','ui'],required=True)
    p.add_argument('--repo-root',default=r'D:\Projects\DevPilot_Local')
    p.add_argument('--evidence-dir',default=r'D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-E')
    p.add_argument('--browser-fixture-root',default=DEFAULT_FIXTURE)
    p.add_argument('--validate-only',action='store_true',help='Validate runtime prerequisites and fixture authority without starting a child process.')
    a=p.parse_args(); repo=Path(a.repo_root).resolve(); evidence=Path(a.evidence_dir).resolve(); runtime=evidence/'runtime'; runtime.mkdir(parents=True,exist_ok=True)
    role=a.role; port=8787 if role=='api' else 5173; url='http://127.0.0.1:8787/api/v1/health' if role=='api' else 'http://127.0.0.1:5173/'
    log=runtime/f'{role}_console.log'; state=runtime/f'{role}_console_state.json'; proc=None; handle=None
    try:
        if not repo.is_dir(): raise RuntimeError(f'Repo no existe: {repo}')
        if port_open(port): raise RuntimeError(f'Puerto {port} ocupado. Use runtime-stop desde Consola 1; no mate procesos por nombre.')
        if a.validate_only:
            validation={'status':'PASS','role':role,'version':VERSION,'validate_only':True,'timestamp':now(),'port':port,'port_free':True,'token_persisted':False,'token_printed':False}
            if role=='api':
                fixture,fixture_policy=validate_fixture(a.browser_fixture_root,repo,evidence)
                py=repo/'.venv'/'Scripts'/'python.exe'
                if not py.is_file(): raise RuntimeError('Falta .venv\\Scripts\\python.exe.')
                validation['workspace_binding']={'allowed_workspace_root':str(fixture),'active_workspace_root':str(fixture),'scope':'gsdlc-04-e-browser-fixture-only','fixture_dirty_policy':fixture_policy}
            else:
                npm=shutil.which('npm.cmd') or shutil.which('npm')
                if not npm: raise RuntimeError('npm.cmd/npm no disponible en PATH.')
                validation['npm_available']=True
            print(json.dumps(validation,indent=2,ensure_ascii=False)); verdict('PASS',f'{role.upper()} preflight runtime validado; no se inició ningún proceso'); return 0
        env=dict(os.environ); env['PYTHONPATH']='src'; binding=None
        if role=='api':
            fixture,fixture_policy=validate_fixture(a.browser_fixture_root,repo,evidence)
            py=repo/'.venv'/'Scripts'/'python.exe'
            if not py.is_file(): raise RuntimeError('Falta .venv\\Scripts\\python.exe.')
            env['DEVPILOT_ALLOWED_WORKSPACE_ROOTS']=str(fixture); env['DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT']=str(fixture); env.pop('DEVPILOT_UI_WORKSPACE_REGISTRY_PATH',None)
            env['DEVPILOT_API_TOKEN']=secrets.token_urlsafe(32)
            binding={'allowed_workspace_root':str(fixture),'active_workspace_root':str(fixture),'registry_env_cleared':True,'scope':'gsdlc-04-e-browser-fixture-only','fixture_dirty_policy':fixture_policy}
            argv=[str(py),'-m','devpilot_core','api','serve','--host','127.0.0.1','--port','8787','--execute']
        else:
            npm=shutil.which('npm.cmd') or shutil.which('npm')
            if not npm: raise RuntimeError('npm.cmd/npm no disponible en PATH.')
            argv=[npm,'--prefix','ui/web','run','dev','--','--host','127.0.0.1','--port','5173']
        handle=log.open('a',encoding='utf-8')
        kwargs={'cwd':str(repo),'stdout':handle,'stderr':subprocess.STDOUT,'env':env,'shell':False}
        if os.name=='nt': kwargs['creationflags']=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0)
        else: kwargs['start_new_session']=True
        proc=subprocess.Popen(argv,**kwargs)
        payload={'status':'STARTING','role':role,'version':VERSION,'started_at':now(),'launcher_pid':os.getpid(),'child_pid':proc.pid,'port':port,'ready_url':url,'log':str(log),'token_persisted':False,'token_printed':False,'three_console_runtime_required':True}
        if binding: payload['workspace_binding']=binding
        state.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        deadline=time.time()+75
        while time.time()<deadline and proc.poll() is None:
            if ready(url): break
            time.sleep(1)
        if proc.poll() is not None or not ready(url):
            stop(proc); tail=log.read_text(encoding='utf-8',errors='replace')[-3500:] if log.exists() else ''; raise RuntimeError(f'{role.upper()} no alcanzó readiness. Revise {log}. Tail:\n{tail}')
        payload['status']='PASS'; payload['ready_at']=now(); state.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(json.dumps(payload,indent=2,ensure_ascii=False))
        if role=='api': print(f'INFO — HTTP requests se registran en {log}; esta consola queda silenciosa por diseño.',flush=True)
        verdict('PASS',f'{role.upper()} lista en {url}; mantenga ESTA consola abierta')
        while proc.poll() is None: time.sleep(1)
        verdict('PASS',f'{role.upper()} finalizada; puede cerrar esta consola'); return 0
    except Exception as exc:
        if proc is not None: stop(proc)
        payload={'status':'BLOCK','script_id':SCRIPT_ID,'version':VERSION,'role':role,'timestamp':now(),'message':str(exc),'token_persisted':False,'token_printed':False}
        print(json.dumps(payload,indent=2,ensure_ascii=False)); verdict('BLOCK',f'{role.upper()}: {exc}'); return 20
    finally:
        if handle: handle.close()

if __name__=='__main__': raise SystemExit(main())
