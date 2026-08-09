from __future__ import annotations
from pathlib import Path
import hashlib, json

def create_uoc004_workspace(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    docs={
        'docs/00_product/product_vision.md': '---\ndoc_id: "PV-001"\ntitle: "Product Vision"\nstatus: "approved"\nversion: "1.0.0"\nowner: "Test"\nupdated: "2026-08-08"\napproval: "approved_by_owner"\n---\n\n# Product Vision\n\nOriginal product vision.\n',
        'docs/01_requirements/requirements.json': json.dumps({'requirements':[{'id':'FR-001','title':'Original'}]}, indent=2)+'\n',
        'docs/02_architecture/config.yaml': 'name: inventory-sales-local\nmode: local\n',
        'docs/notes.txt': 'read-only text\n',
    }
    for rel,content in docs.items():
        p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content,encoding='utf-8')
    (root/'.devpilot').mkdir(exist_ok=True)
    (root/'.devpilot/project.yaml').write_text('project_id: inventory-sales-local\nname: Inventory Sales Local\n',encoding='utf-8')
    return root

def snapshot(root: Path) -> dict[str,bytes]:
    return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts and 'outputs' not in p.parts}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
