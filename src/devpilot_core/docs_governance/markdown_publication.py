"""R01-07: governed Markdown publication. No UI writes and no model calls.

The canonical Source Registry and authority graph are updated together with
an approved Markdown document; preview is read-only by default.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any

from .authority import DerivedMetadataProjection

REGISTRY = '.devpilot/docs_governance/source_registry.json'
GRAPH = '.devpilot/docs_governance/documentation_authority_graph.json'
OVERLAY = '.devpilot/docs_governance/rebaseline_p0_overlay.json'
DOC_ROOT = 'docs/published/'
MAX_DOCUMENT_BYTES = 1024 * 1024


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(raw: bytes) -> bytes:
    return raw.replace(b'\r\n', b'\n')


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def _safe_path(root: Path, raw: str) -> Path:
    if not isinstance(raw, str) or len(raw) > 220 or not raw.startswith(DOC_ROOT):
        raise ValueError('PUBLICATION_PATH_NOT_GOVERNED')
    posix = PurePosixPath(raw)
    parts = raw.split('/')
    if (posix.is_absolute() or any(part in ('', '.', '..') for part in parts)
            or any(not re.fullmatch(r'[A-Za-z0-9_.-]+', part) for part in parts)
            or any(part.lower() in {'.git', '.devpilot', '.venv', 'node_modules'} for part in parts)
            or not raw.lower().endswith('.md') or '\\' in raw or ':' in raw):
        raise ValueError('PUBLICATION_PATH_UNSAFE')
    path = root.joinpath(*parts)
    # Never follow symlinks, including Windows junction/reparse symlink targets.
    for ancestor in (root, *(root.joinpath(*parts[:n]) for n in range(1, len(parts)+1))):
        if ancestor.is_symlink() or ancestor.is_junction():
            raise ValueError('PUBLICATION_SYMLINK_DENIED')
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('PUBLICATION_ESCAPE')
    return path


def _atomic(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.mp132-pub-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@dataclass(frozen=True)
class MarkdownPublication:
    relative_path: str
    doc_id: str
    owner: str
    content: str
    required_tests: tuple[str, ...]
    approved: bool = False


class GovernedMarkdownPublisher:
    """Explicit, bounded writer; not exposed by the read-only document viewer."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    def publish(self, request: MarkdownPublication, *, expected_registry_sha256: str,
                execute: bool = False) -> dict[str, Any]:
        if not re.fullmatch(r'[A-Za-z0-9_.-]{3,128}', request.doc_id):
            raise ValueError('PUBLICATION_DOC_ID_INVALID')
        if not isinstance(request.owner, str) or not request.owner.strip():
            raise ValueError('PUBLICATION_OWNER_REQUIRED')
        if not request.required_tests or not all(isinstance(x, str) and x.startswith('tests/') and
              x.endswith('.py') and '..' not in x.split('/') for x in request.required_tests):
            raise ValueError('PUBLICATION_REQUIRED_TESTS_INVALID')
        for test in request.required_tests:
            if not (self.root / test).is_file() or (self.root / test).is_symlink() or not (self.root / test).resolve().is_relative_to(self.root):
                raise ValueError('PUBLICATION_REQUIRED_TEST_MISSING')
        if not isinstance(request.content, str):
            raise ValueError('PUBLICATION_CONTENT_INVALID')
        content = _canonical(request.content.encode('utf-8'))
        if len(content) > MAX_DOCUMENT_BYTES or len(content) < 40 or b'\x00' in content:
            raise ValueError('PUBLICATION_CONTENT_INVALID')
        # Read frontmatter just for approval metadata; no arbitrary YAML interpretation.
        lines = content.decode('utf-8').splitlines()
        if not lines or lines[0] != '---' or '---' not in lines[1:60]:
            raise ValueError('PUBLICATION_FRONTMATTER_REQUIRED')
        fm = lines[1:lines.index('---', 1)]
        values = {}
        for line in fm:
            if ':' in line:
                key, value = line.split(':', 1)
                values[key.strip()] = value.strip().strip('"\'')
        if (values.get('status', '').lower() != 'approved' or
                values.get('doc_id') != request.doc_id or values.get('owner') != request.owner):
            raise ValueError('PUBLICATION_APPROVAL_METADATA_MISMATCH')
        destination = _safe_path(self.root, request.relative_path)
        registry_path, graph_path = self.root / REGISTRY, self.root / GRAPH
        overlay_path = self.root / OVERLAY
        if any(p.is_symlink() or p.is_junction() for p in (registry_path, graph_path, overlay_path)):
            raise ValueError('PUBLICATION_GOVERNANCE_SYMLINK_DENIED')
        current = registry_path.read_bytes()
        if _sha(_canonical(current)) != expected_registry_sha256:
            raise ValueError('PUBLICATION_REGISTRY_DRIFT')
        graph_raw = graph_path.read_bytes()
        overlay_raw = overlay_path.read_bytes()
        registry, graph, overlay = json.loads(current), json.loads(graph_raw), json.loads(overlay_raw)
        docs = registry.get('documents')
        nodes = graph.get('nodes')
        if not isinstance(docs, list) or not isinstance(nodes, list):
            raise ValueError('PUBLICATION_REGISTRY_GRAPH_INVALID')
        matches = [d for d in docs if d.get('path') == request.relative_path or d.get('doc_id') == request.doc_id]
        graph_matches = [n for n in nodes if n.get('path') == request.relative_path or n.get('doc_id') == request.doc_id]
        if matches or graph_matches or destination.exists():
            if (len(matches) == len(graph_matches) == 1 and destination.is_file() and
                    matches[0].get('path') == request.relative_path and
                    matches[0].get('doc_id') == request.doc_id and
                    graph_matches[0].get('path') == request.relative_path and
                    graph_matches[0].get('doc_id') == request.doc_id and
                    _canonical(destination.read_bytes()) == content):
                return {'status': 'NO_OP_ACCEPTED', 'path': request.relative_path,
                        'sha256': _sha(content), 'registry_documents': len(docs)}
            raise ValueError('PUBLICATION_FROZEN_OR_EXISTING_PATH_DENIED')
        # Historical/frozen entries are never overwritten, even if content is identical.
        entry = {'doc_id': request.doc_id, 'path': request.relative_path,
                 'owner': request.owner, 'classification': 'source-of-truth',
                 'criticality': 'P1', 'domain': 'documentation.governed',
                 'lifecycle': 'active', 'status_required': 'approved',
                 'required_tests': list(request.required_tests), 'sync_rules': ['test_must_pass'],
                 'notes': ['R01-07 governed human-approved Markdown publication']}
        node = {'node_id': 'publication-' + _sha(request.doc_id.encode())[:16],
                'doc_id': request.doc_id, 'path': request.relative_path,
                'subject': 'governed-publication', 'authority_rank': 50,
                'authority_kind': 'current-active', 'lifecycle': 'active',
                'classification': 'source-of-truth', 'successor': None}
        old_total = len(docs)
        authority = overlay.get('authority', {})
        if authority.get('mp_registry_state') != f'PROGRAM_132_PUBLISHED/{old_total}_ENTRIES':
            raise ValueError('PUBLICATION_OVERLAY_REGISTRY_DRIFT')
        docs.append(entry)
        nodes.append(node)
        authority['mp_registry_state'] = f'PROGRAM_132_PUBLISHED/{len(docs)}_ENTRIES'
        registry.setdefault('summary', {}).update(DerivedMetadataProjection.source_registry_summary(registry))
        planned = {'status': 'PREVIEW_APPROVED' if request.approved else 'PREVIEW_APPROVAL_REQUIRED',
                   'path': request.relative_path, 'sha256': _sha(content),
                   'registry_documents': len(docs), 'source_graph_node_id': node['node_id'],
                   'mutations_performed': False}
        if not execute:
            return planned
        if not request.approved:
            raise ValueError('PUBLICATION_OWNER_APPROVAL_REQUIRED')
        lock = self.root / '.devpilot/docs_governance/.r01_07_publication.lock'
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ValueError('PUBLICATION_CONCURRENT_LOCK') from exc
        os.close(fd)
        created = False
        updated_registry = False
        updated_graph = False
        try:
            if _sha(_canonical(registry_path.read_bytes())) != expected_registry_sha256 or \
                    graph_path.read_bytes() != graph_raw or overlay_path.read_bytes() != overlay_raw or destination.exists():
                raise ValueError('PUBLICATION_SOURCE_DRIFT_UNDER_LOCK')
            _atomic(destination, content); created = True
            _atomic(registry_path, _json_bytes(registry)); updated_registry = True
            _atomic(graph_path, _json_bytes(graph)); updated_graph = True
            _atomic(overlay_path, _json_bytes(overlay))
        except Exception:
            # Restore the original authority before propagating a failed publish.
            if updated_graph:
                _atomic(graph_path, graph_raw)
            if updated_registry:
                _atomic(registry_path, current)
            if created:
                destination.unlink(missing_ok=True)
            raise
        finally:
            lock.unlink(missing_ok=True)
        planned['status'] = 'PUBLISHED'
        planned['mutations_performed'] = True
        return planned
