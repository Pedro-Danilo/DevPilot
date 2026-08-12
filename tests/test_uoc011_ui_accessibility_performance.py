from pathlib import Path
import json, subprocess
ROOT=Path(__file__).resolve().parents[1]

def _npm_script(name:str):
    return subprocess.run(['node',f'ui/web/scripts/{name}'],cwd=ROOT,text=True,capture_output=True,check=False)

def test_uoc011_ui_source_contracts() -> None:
    main=(ROOT/'ui/web/src/main.ts').read_text(encoding='utf-8'); css=(ROOT/'ui/web/src/styles.css').read_text(encoding='utf-8'); client=(ROOT/'ui/web/src/api/client.ts').read_text(encoding='utf-8'); vite=(ROOT/'ui/web/vite.config.ts').read_text(encoding='utf-8')
    assert 'skip-link' in main and "role', 'main" in main and 'TTL máximo de 8h' in main
    assert ':focus-visible' in css and 'prefers-reduced-motion' in css and 'min-height: 44px' in css
    assert 'TOKEN_SESSION_TTL_MS = 8 * 60 * 60 * 1000' in client and 'TOKEN_STORED_AT_KEY' in client and 'clearExpiredStoredToken' in client
    assert 'Content-Security-Policy' in vite and "frame-ancestors 'none'" in vite

def test_uoc011_node_smokes_pass() -> None:
    for script in ['uoc011-accessibility-smoke.mjs','uoc011-performance-smoke.mjs','uoc011-state-matrix-smoke.mjs']:
        result=_npm_script(script); assert result.returncode==0, result.stdout+result.stderr
        payload=json.loads(result.stdout); assert payload['status']=='PASS'
