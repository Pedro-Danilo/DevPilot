from __future__ import annotations

import argparse
import json
import os
import py_compile
import shutil
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .governed_job_capability_registry import GovernedJobCapabilityRegistry
from .governed_job_operations import ControlledProcessTree, GovernedJobLogStore, GovernedJobOperationsApplicationService
from .governed_jobs import GovernedJobFramework, GovernedJobStore
from .story_validation_jobs import CAPABILITY_REGISTRY, StoryValidationJobApplicationService


def _pytest_summary(xml_path: Path, returncode: int) -> dict[str, Any]:
    tests = failures = errors = skipped = 0
    try:
        root = ET.parse(xml_path).getroot()
        suites = [root] if root.tag == 'testsuite' else list(root.findall('testsuite'))
        tests = sum(int(s.attrib.get('tests', '0')) for s in suites)
        failures = sum(int(s.attrib.get('failures', '0')) for s in suites)
        errors = sum(int(s.attrib.get('errors', '0')) for s in suites)
        skipped = sum(int(s.attrib.get('skipped', '0')) for s in suites)
    except Exception:
        pass
    return {'tests': tests, 'passed': max(0, tests - failures - errors - skipped), 'failed': failures, 'errors': errors, 'skipped': skipped, 'returncode': returncode}


def _stream_process(root: Path, job_id: str, argv: list[str], *, timeout_seconds: int, logs: GovernedJobLogStore, heartbeat=None) -> tuple[int, bool]:
    kwargs: dict[str, Any] = {'cwd': str(root), 'stdin': subprocess.DEVNULL, 'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE, 'text': True, 'shell': False, 'bufsize': 1}
    if os.name != 'nt':
        kwargs['start_new_session'] = True
    proc = subprocess.Popen(argv, **kwargs)
    stop = threading.Event()
    def pump(stream, level: str) -> None:
        try:
            for line in iter(stream.readline, ''):
                if stop.is_set():
                    break
                text = line.rstrip('\r\n')
                if text:
                    logs.append(job_id, level=level, phase='process', message=text)
        finally:
            try: stream.close()
            except Exception: pass
    threads = [threading.Thread(target=pump, args=(proc.stdout, 'INFO'), daemon=True), threading.Thread(target=pump, args=(proc.stderr, 'WARN'), daemon=True)]
    for thread in threads: thread.start()
    timed_out = False
    deadline = time.monotonic() + max(1, int(timeout_seconds))
    next_heartbeat = time.monotonic()
    rc = None
    try:
        while rc is None:
            rc = proc.poll()
            now = time.monotonic()
            if rc is not None:
                break
            if now >= deadline:
                timed_out = True
                ControlledProcessTree.terminate(proc.pid)
                try: rc = proc.wait(timeout=5)
                except Exception: rc = 124
                break
            if heartbeat is not None and now >= next_heartbeat:
                heartbeat()
                next_heartbeat = now + 3.0
            time.sleep(0.20)
    finally:
        stop.set()
        for thread in threads: thread.join(timeout=1)
    return int(rc if rc is not None else 124), timed_out


def _result_path(root: Path, job_id: str) -> Path:
    path = root / 'outputs/runtime/gsdlc10b_story_validation/results' / f'{job_id}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def run_job(root: Path, job_id: str) -> int:
    root = Path(root).resolve()
    registry = GovernedJobCapabilityRegistry(root, registry_path=CAPABILITY_REGISTRY)
    store = GovernedJobStore(root)
    framework = GovernedJobFramework(root, registry=registry, store=store)
    ops = GovernedJobOperationsApplicationService(root)
    logs = GovernedJobLogStore(root)
    record = store.load(job_id)
    ref = str(record.get('runtime_context_ref') or '')
    context_path = (root / ref).resolve()
    context = json.loads(context_path.read_text(encoding='utf-8'))
    # Integrity of the context is checked again without relying on browser input.
    import hashlib
    core = {k: v for k, v in context.items() if k != 'context_hash'}
    actual = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()
    if actual != str(context.get('context_hash')):
        framework.complete(job_id, status='error', error='StoryValidationJob immutable context hash mismatch.'); return 30
    framework.start(job_id)
    ops.record_progress(job_id=job_id, phase='running', progress_percent=5, worker_pid=os.getpid(), message=f'GSDLC-10-B {context["job_kind"]} adapter started; shell=false; Full=false')
    kind = str(context['job_kind']); limits = dict(context.get('limits') or {}); timeout = int(limits.get('timeout_seconds', record.get('timeout_seconds', 120)))
    result: dict[str, Any] = {'schema_id': 'SCHEMA-DEVPL-GSDLC-10-B-STORY-VALIDATION-JOB-RESULT-V1', 'job_id': job_id, 'job_kind': kind, 'context_hash': context['context_hash'], 'story_test_plan_id': context['story_test_plan_id'], 'story_test_plan_hash': context['story_test_plan_hash'], 'full_regression': False, 'network_used': False, 'external_api_used': False}
    artifact_refs: list[str] = []
    try:
        if kind == 'test':
            targets = list(context.get('test_targets') or [])
            max_targets = int(limits.get('max_targets', 200))
            if not targets or len(targets) > max_targets:
                raise RuntimeError('Typed test target set is empty or exceeds its immutable budget.')
            junit = root / 'outputs/runtime/gsdlc10b_story_validation/junit' / f'{job_id}.xml'; junit.parent.mkdir(parents=True, exist_ok=True)
            argv = [sys.executable, '-m', 'pytest', '-q', *targets, f'--junitxml={junit}']
            rc, timed_out = _stream_process(root, job_id, argv, timeout_seconds=timeout, logs=logs, heartbeat=lambda: ops.record_progress(job_id=job_id, phase='running', progress_percent=50, worker_pid=os.getpid(), message=None))
            result['timed_out'] = timed_out; result['summary'] = _pytest_summary(junit, rc)
            if junit.is_file(): artifact_refs.append(str(junit.relative_to(root)).replace('\\', '/'))
        elif kind == 'build':
            npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm') or shutil.which('npm')
            if not npm:
                raise RuntimeError('Typed build adapter requires npm from the validated local toolchain.')
            argv = [npm, '--prefix', 'ui/web', 'run', 'build']
            rc, timed_out = _stream_process(root, job_id, argv, timeout_seconds=timeout, logs=logs, heartbeat=lambda: ops.record_progress(job_id=job_id, phase='running', progress_percent=50, worker_pid=os.getpid(), message=None))
            result['timed_out'] = timed_out; result['summary'] = {'returncode': rc, 'build_profile': 'ui-vite-build', 'dist_present': (root / 'ui/web/dist').is_dir()}
        elif kind == 'lint':
            paths = [str(x) for x in context.get('changed_paths', []) if str(x).endswith('.py')]
            max_targets = int(limits.get('max_targets', 100))
            if len(paths) > max_targets:
                raise RuntimeError('Typed lint target set exceeds immutable budget.')
            failed: list[dict[str, str]] = []
            for rel in paths:
                path = (root / rel).resolve()
                try: path.relative_to(root)
                except ValueError: raise RuntimeError('Lint target escaped repository root.')
                try: py_compile.compile(str(path), doraise=True)
                except py_compile.PyCompileError as exc: failed.append({'path': rel, 'error': str(exc)[:1000]})
            rc = 0 if not failed else 1; timed_out = False
            result['timed_out'] = False; result['summary'] = {'returncode': rc, 'checked': len(paths), 'failed': len(failed), 'failures': failed}
            logs.append(job_id, level='INFO' if rc == 0 else 'WARN', phase='lint', message=f'Typed Python syntax lint checked={len(paths)} failed={len(failed)}')
        else:
            raise RuntimeError(f'Unsupported StoryValidationJob kind: {kind}')

        result_file = _result_path(root, job_id)
        result_file.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
        artifact_refs.append(str(result_file.relative_to(root)).replace('\\', '/'))
        if result.get('timed_out'):
            framework.complete(job_id, status='error', result_summary={'job_kind': kind, 'timed_out': True, **dict(result.get('summary') or {})}, artifact_refs=artifact_refs, error='Typed validation job exceeded timeout budget.')
            return 30
        rc = int((result.get('summary') or {}).get('returncode', 0))
        status = 'pass' if rc == 0 else 'block'
        ops.record_progress(job_id=job_id, phase='completed', progress_percent=100, message=f'GSDLC-10-B {kind} completed status={status}')
        framework.complete(job_id, status=status, result_summary={'job_kind': kind, 'timed_out': False, **dict(result.get('summary') or {})}, artifact_refs=artifact_refs)
        return 0 if status == 'pass' else 20
    except Exception as exc:
        logs.append(job_id, level='ERROR', phase='worker', message=f'{type(exc).__name__}: {exc}')
        framework.complete(job_id, status='error', result_summary={'job_kind': kind, 'timed_out': False}, error=f'{type(exc).__name__}: {exc}')
        return 30


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', required=True)
    parser.add_argument('--job-id', required=True)
    args = parser.parse_args()
    return run_job(Path(args.repo_root), args.job_id)


if __name__ == '__main__':
    raise SystemExit(main())
