"""UX01-C read projection. Existing lifecycle/companion remain the authority."""
from pathlib import Path
import hashlib
from typing import Any


def project_documents(*, workspace_root: Path, arch: dict[str, Any], authoring: dict[str, Any],
                      bundle: dict[str, Any], architecture_path: str, current: bool,
                      owner: bool, candidate_reader) -> dict[str, Any]:
    def source(relative: str, expected: str) -> str:
        target = workspace_root / relative
        if (not expected or not target.resolve().is_relative_to(workspace_root.resolve())
                or any(p.is_symlink() for p in [target, *target.parents] if p != workspace_root.parent)):
            raise ValueError('UX01_C_SOURCE_PATH_BLOCK')
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('UX01_C_SOURCE_HASH_DRIFT')
        return raw.decode('utf-8-sig')

    frozen = arch.get('status') == 'FROZEN'
    editable = bool(owner and current and not arch.get('approval_id')
                    and arch.get('status') in ('MISSING', 'DRAFT', 'FINDINGS', 'APPROVAL_REQUIRED'))
    result = {}
    for kind, key in [('architecture', None), ('technology_options', 'technology'), ('adr', 'adr')]:
        record = arch if key is None else (authoring.get(key) or {})
        row = {'status': 'SIN_GENERAR', 'content': '', 'can_edit': False,
               'source': 'runtime-candidate', 'sha256': '', 'quality': None}
        try:
            if key is None:
                row['quality'] = (arch.get('derivation') or {}).get('ux01_quality')
                if frozen:
                    row.update(content=source(architecture_path, arch.get('approved_sha256', '')),
                               status='FROZEN', source=architecture_path, sha256=arch['approved_sha256'])
                elif arch.get('content'):
                    content = arch['content']
                    digest = hashlib.sha256(content.replace('\r\n', '\n').replace('\r', '\n').encode()).hexdigest()
                    if digest != arch.get('content_sha256'):
                        raise ValueError('UX01_C_DRAFT_HASH_DRIFT')
                    row.update(content=content, status=arch['status'], sha256=digest)
            elif frozen and bundle.get('ready'):
                matches = [d for d in bundle.get('adrs', [])
                           if (d.get('adr_id') == 'TECH-OPTIONS') == (key == 'technology')]
                if len(matches) != 1:
                    raise ValueError('UX01_C_COMPANION_IDENTITY_BLOCK')
                item = matches[0]
                row.update(content=source(item['relative_path'], item['proposed_sha256']),
                           status='FROZEN', source=item['relative_path'], sha256=item['proposed_sha256'])
            elif record:
                row.update(content=candidate_reader(record), status='REVIEW_REQUIRED',
                           sha256=record['candidate_sha256'], quality=record.get('quality'))
            row['candidate_id'] = record.get('candidate_id') or row['sha256']
            row['generation_epoch'] = record.get('generation_epoch') or (arch.get('derivation') or {}).get('generation_epoch')
            row['can_edit'] = editable and (key is None or bool(record)) and not frozen
        except (ValueError, OSError, UnicodeError, KeyError) as exc:
            row.update(status='BLOCK', content='', can_edit=False, error_code=str(exc).split(':')[0])
        result[kind] = row
    return result
