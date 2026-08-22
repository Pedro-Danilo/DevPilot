from __future__ import annotations

import argparse
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

SCRIPT_ID="DEVPL-GSDLC-04-D-RUNTIME-CONSOLE"
VERSION="1.0.0"
DEFAULT_FIXTURE=r"D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_D_BROWSER"


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

def validate_fixture(raw:str)->Path:
    f=Path(raw).resolve(); expected=Path(DEFAULT_FIXTURE).resolve()
    if f!=expected: raise RuntimeError(f'Fixture 04-D no autorizado: {f}; esperado exactamente {expected}.')
    if not f.is_dir() or not (f/'.git').exists(): raise RuntimeError('Fixture 04-D no existe o no es Git; ejecute prepare-browser desde Consola 1.')
    required=[f/'.devpilot/project.yaml',f/'docs/baseline.md',f/'docs/baseline.json']
    missing=[str(x) for x in required if not x.is_file()]
    if missing: raise RuntimeError(f'Fixture incompleto: {missing}')
    if 'inventory-sales-local' in str(f).lower() or 'devpilot_workspaces' in str(f).lower(): raise RuntimeError('Workspace piloto real prohibido en 04-D.')
    clean,rows=git_clean(f)
    if not clean: raise RuntimeError(f'Fixture Git dirty antes de runtime: {rows}. No use git clean/reset; preserve evidencia.')
    return f

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
    p=argparse.ArgumentParser(description='Dedicated 04-D API/UI launcher. Use separate Console 2/3.')
    p.add_argument('--role',choices=['api','ui'],required=True)
    p.add_argument('--repo-root',default=r'D:\Projects\DevPilot_Local')
    p.add_argument('--evidence-dir',default=r'D:\Projects\DevPilot_E2E_Evaluation\evidence\DEVPL-GSDLC-04-D')
    p.add_argument('--browser-fixture-root',default=DEFAULT_FIXTURE)
    a=p.parse_args(); repo=Path(a.repo_root).resolve(); evidence=Path(a.evidence_dir).resolve(); runtime=evidence/'runtime'; runtime.mkdir(parents=True,exist_ok=True)
    role=a.role; port=8787 if role=='api' else 5173; url='http://127.0.0.1:8787/api/v1/health' if role=='api' else 'http://127.0.0.1:5173/'
    log=runtime/f'{role}_console.log'; state=runtime/f'{role}_console_state.json'; proc=None; handle=None
    try:
        if not repo.is_dir(): raise RuntimeError(f'Repo no existe: {repo}')
        if port_open(port): raise RuntimeError(f'Puerto {port} ocupado. Use runtime-stop desde Consola 1; no mate procesos por nombre.')
        env=dict(os.environ); env['PYTHONPATH']='src'; binding=None
        if role=='api':
            fixture=validate_fixture(a.browser_fixture_root)
            py=repo/'.venv'/'Scripts'/'python.exe'
            if not py.is_file(): raise RuntimeError('Falta .venv\\Scripts\\python.exe.')
            env['DEVPILOT_ALLOWED_WORKSPACE_ROOTS']=str(fixture); env['DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT']=str(fixture); env.pop('DEVPILOT_UI_WORKSPACE_REGISTRY_PATH',None)
            env['DEVPILOT_API_TOKEN']=secrets.token_urlsafe(32)
            binding={'allowed_workspace_root':str(fixture),'active_workspace_root':str(fixture),'registry_env_cleared':True,'scope':'gsdlc-04-d-browser-fixture-only'}
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
