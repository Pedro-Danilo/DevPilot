from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def browser_executable() -> str | None:
    for candidate in [
        os.environ.get("DEVPILOT_BROWSER_EXECUTABLE"),
        r"C:/Program Files/Google/Chrome/Application/chrome.exe",
        r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
        r"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
        r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
    ]:
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def _notice(page) -> str:
    try:
        return page.locator('[role="status"]').inner_text(timeout=1000).strip()
    except Exception:
        return ""


def wait_notice(page, *, previous: str, expected_prefix: str, timeout_ms: int = 12000) -> str:
    deadline = time.monotonic() + timeout_ms / 1000.0
    last = previous
    while time.monotonic() < deadline:
        try:
            text = _notice(page)
            if text:
                last = text
            if text != previous:
                if text.startswith(expected_prefix):
                    return text
                if text.startswith(("BLOCK", "ERROR", "CONFLICT")):
                    raise RuntimeError(f"UI returned {text}")
        except RuntimeError:
            raise
        except Exception:
            pass
        page.wait_for_timeout(100)
    raise TimeoutError(f"UI state did not reach {expected_prefix!r}; last_notice={last!r}")


def wait_source_loaded(page, relative_path: str, timeout_ms: int = 12000) -> None:
    deadline = time.monotonic() + timeout_ms / 1000.0
    last_notice = ""
    last_hash = ""
    last_target = ""
    while time.monotonic() < deadline:
        last_notice = _notice(page)
        try:
            last_hash = page.locator('[data-source-hash="true"]').inner_text(timeout=500).strip()
        except Exception:
            last_hash = ""
        try:
            last_target = page.locator('[data-target-path="true"]').input_value(timeout=500).strip()
        except Exception:
            last_target = ""
        if last_notice.startswith(("BLOCK", "ERROR")):
            raise RuntimeError(f"source load failed: {last_notice}")
        if (
            last_notice == "PASS · source leído por opaque id."
            and last_target == relative_path
            and last_hash.startswith("preimage ")
            and len(last_hash.split(" ", 1)[1]) == 64
        ):
            return
        page.wait_for_timeout(100)
    raise TimeoutError(
        "source did not reach loaded/preimage state; "
        f"notice={last_notice!r}; target={last_target!r}; hash={last_hash!r}"
    )


def capture_failure(evidence: Path, page, *, step: str, error: BaseException, events: list[dict[str, Any]]) -> None:
    evidence.mkdir(parents=True, exist_ok=True)
    screenshot = evidence / "99_browser_failure.png"
    try:
        page.screenshot(path=str(screenshot), full_page=True)
    except Exception:
        pass
    payload = {
        "schema_id": "DEVPL-GSDLC-09-B-BROWSER-FAILURE-V1",
        "status": "BLOCK",
        "step": step,
        "error_type": type(error).__name__,
        "error": str(error),
        "ui_notice": _notice(page),
        "events": events[-100:],
        "screenshot": screenshot.name if screenshot.is_file() else None,
        "generated_at_utc": now(),
    }
    (evidence / "DEVPL_GSDLC_09_B_BROWSER_FAILURE.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace-root", required=True)
    ap.add_argument("--auth-root", required=True)
    ap.add_argument("--evidence-dir", required=True)
    ap.add_argument("--ui-url", default="http://127.0.0.1:5173/story/code")
    ap.add_argument("--api-url", default="http://127.0.0.1:8787/api/v1")
    ap.add_argument("--fixture-script")
    ap.add_argument("--browser-prep-id", required=True)
    ap.add_argument("--implementation-commit", required=True)
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        print(f"BLOCK - Python Playwright unavailable: {exc}")
        return 2

    root = Path(args.workspace_root).resolve()
    auth_root = Path(args.auth_root).resolve()
    evidence = Path(args.evidence_dir).resolve()
    fixture_script = Path(args.fixture_script).resolve() if args.fixture_script else Path(__file__).with_name("devpl_gsdlc_09_b_browser_fixture.py").resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    source = root / "src/app.py"
    seal = root / ".devpilot/gsdlc09b_browser_fixture.json"
    if not source.is_file() or not seal.is_file() or not fixture_script.is_file():
        print("BLOCK - browser fixture or fixture script not prepared.")
        return 2

    baseline = json.loads(seal.read_text(encoding="utf-8"))
    baseline_sha = str(baseline["original_sha256"])
    password = "Browser09B-" + secrets.token_urlsafe(12)
    results: list[tuple[str, bool]] = []
    events: list[dict[str, Any]] = []
    page = None
    step = "startup"
    restored = False
    synthetic_architect_created = False
    synthetic_architect_removed = False
    owner_preserved = False

    try:
        with sync_playwright() as pw:
            exe = browser_executable()
            browser = pw.chromium.launch(headless=True, executable_path=exe) if exe else pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 1000})
            req = context.request

            def on_response(response) -> None:
                if "/story/code" in response.url or "/auth/" in response.url:
                    events.append({
                        "kind": "response",
                        "method": response.request.method,
                        "status": response.status,
                        "url": response.url,
                    })

            def on_console(message) -> None:
                if message.type in {"error", "warning"}:
                    events.append({"kind": "console", "type": message.type, "text": message.text})

            def on_page_error(error) -> None:
                events.append({"kind": "pageerror", "text": str(error)})

            def on_request_failed(request) -> None:
                if "/story/code" in request.url or "/auth/" in request.url:
                    events.append({
                        "kind": "requestfailed",
                        "method": request.method,
                        "url": request.url,
                        "failure": request.failure,
                    })

            step = "bootstrap-owner"
            r = req.post(
                args.api_url + "/auth/bootstrap/owner",
                headers={"Origin": "http://127.0.0.1:5173"},
                data={"username": "browser.owner", "display_name": "Browser Owner", "password": password},
            )
            if r.status not in (201, 409):
                raise RuntimeError(f"transient owner bootstrap failed status={r.status} body={r.text()[:500]}")
            if r.status == 409:
                r = req.post(
                    args.api_url + "/auth/login",
                    headers={"Origin": "http://127.0.0.1:5173"},
                    data={"username": "browser.owner", "password": password},
                )
                if r.status != 200:
                    raise RuntimeError("transient browser auth store is stale; rerun browser-prep before acceptance")

            project_context_script = (
                "sessionStorage.setItem('devpilot.gsdlc03e.projectJourneyContext.v1', JSON.stringify({phase:'project',entry_mode:'OPEN_EXISTING',project_id:'gsdlc-09-b-browser',target_root:"
                + json.dumps(str(root))
                + ",activated_at:new Date().toISOString()}));"
            )
            context.add_init_script(project_context_script)
            page = context.new_page()
            page.on("response", on_response)
            page.on("console", on_console)
            page.on("pageerror", on_page_error)
            page.on("requestfailed", on_request_failed)

            step = "open-story-context"
            page.goto(args.ui_url, wait_until="load")
            page.locator('[data-gsdlc09b="code-workbench"]').wait_for()
            page.locator('[data-source-path="src/app.py"]').wait_for()
            page.screenshot(path=str(evidence / "01_story_code_ready.png"), full_page=True)
            results.append(("open-story-context", True))

            step = "navigate-source"
            item = page.locator('[data-source-path="src/app.py"]')
            before_notice = _notice(page)
            item.click()
            wait_source_loaded(page, "src/app.py")
            before = sha(source)
            results.append(("navigate-source", before == baseline_sha))

            step = "draft-source-unchanged"
            editor = page.locator('[data-draft-editor="true"]')
            editor.fill("def answer():\n    return 43\n")
            previous = _notice(page)
            page.locator('[data-save-draft="true"]').click()
            wait_notice(page, previous=previous, expected_prefix="PASS · draft guardado; source real permanece sin cambios.")
            results.append(("draft-source-unchanged", sha(source) == before == baseline_sha))
            page.screenshot(path=str(evidence / "02_draft_saved_source_unchanged.png"), full_page=True)

            # Each browser case owns its runtime draft lifecycle.  Do not carry the
            # draft from the source-unchanged proof into the next scenarios: the
            # backend correctly enforces optimistic draft revisions, and reopening
            # the same source intentionally clears the UI-local draft pointer.
            step = "discard-first-draft"
            previous = _notice(page)
            page.locator('[data-discard-draft="true"]').click()
            wait_notice(page, previous=previous, expected_prefix="PASS · runtime draft descartado.")

            step = "path-escape-block"
            page.get_by_label("Operación de draft").select_option("CREATE")
            page.locator('[data-target-path="true"]').fill("../escape.py")
            editor.fill("x=1\n")
            previous = _notice(page)
            page.locator('[data-save-draft="true"]').click()
            deadline = time.monotonic() + 12
            block_text = ""
            while time.monotonic() < deadline:
                block_text = _notice(page)
                if block_text != previous and block_text.startswith("BLOCK ·"):
                    break
                if block_text.startswith("ERROR ·"):
                    raise RuntimeError(block_text)
                page.wait_for_timeout(100)
            if not block_text.startswith("BLOCK ·"):
                raise TimeoutError(f"path escape did not reach BLOCK; last_notice={block_text!r}")
            results.append(("path-escape-block", True))
            page.screenshot(path=str(evidence / "03_path_escape_block.png"), full_page=True)

            step = "external-edit-conflict-visible"
            item.click()
            wait_source_loaded(page, "src/app.py")
            editor.fill("def answer():\n    return 44\n")
            previous = _notice(page)
            page.locator('[data-save-draft="true"]').click()
            wait_notice(page, previous=previous, expected_prefix="PASS · draft guardado; source real permanece sin cambios.")
            subprocess.run(
                [sys.executable, str(fixture_script), "--root", str(root), "--action", "external-edit"],
                check=True,
                capture_output=True,
                text=True,
            )
            page.locator('[data-recheck-draft="true"]').click()
            conflict = page.locator('[data-draft-status="true"]')
            conflict.wait_for()
            deadline = time.monotonic() + 12
            text = ""
            while time.monotonic() < deadline:
                text = conflict.inner_text().strip()
                if text.startswith("CONFLICT · external edit/revalidation requerida"):
                    break
                page.wait_for_timeout(100)
            if not text.startswith("CONFLICT · external edit/revalidation requerida"):
                raise TimeoutError(f"external edit did not reach CONFLICT; draft_status={text!r}; notice={_notice(page)!r}")
            results.append(("external-edit-conflict-visible", True))
            page.screenshot(path=str(evidence / "04_external_edit_conflict.png"), full_page=True)

            # Restore the controlled external edit before the role-negative case,
            # then recheck once to refresh the server-side draft revision and
            # discard the runtime draft.  This makes each case independent and
            # leaves no stale draft state for subsequent steps.
            step = "restore-after-conflict"
            subprocess.run(
                [sys.executable, str(fixture_script), "--root", str(root), "--action", "restore"],
                check=True,
                capture_output=True,
                text=True,
            )
            if sha(source) != baseline_sha:
                raise RuntimeError("fixture restore after conflict did not recover the sealed source baseline")
            previous = _notice(page)
            page.locator('[data-recheck-draft="true"]').click()
            wait_notice(page, previous=previous, expected_prefix="PASS · preimage vigente; source sigue sin cambios.")
            previous = _notice(page)
            page.locator('[data-discard-draft="true"]').click()
            wait_notice(page, previous=previous, expected_prefix="PASS · runtime draft descartado.")

            step = "role-negative-authoring-disabled"
            # Do NOT demote the only owner. The UI first-run guard intentionally
            # requires at least one active owner; mutating local-owner to architect
            # makes /auth/bootstrap/status report first_run_required=true and turns
            # a valid negative-role test into a false First Run redirect. Provision
            # a separate synthetic architect in the transient browser auth store,
            # then authenticate through the real LoginView in a fresh browser context.
            from devpilot_core.identity.auth_models import CredentialRecord, LocalIdentity, utc_now_iso
            from devpilot_core.identity.auth_store import LocalAuthStore
            from devpilot_core.identity.credential_kdf import CredentialKdf

            store = LocalAuthStore(auth_root)
            store.initialize()
            if not store.owner_exists():
                raise RuntimeError("negative-role setup invariant failed: active owner must remain present")
            actor = "gsdlc09b-browser-architect"
            username = "browser.architect"
            display_name = "GSDLC 09-B Browser Architect"
            existing_by_user = store.get_identity_by_username(username)
            existing_by_actor = store.get_identity(actor)
            if existing_by_user is not None or existing_by_actor is not None:
                raise RuntimeError("synthetic architect already exists; rerun browser-prep for a clean auth store")
            architect_password = "Browser09B-Architect-" + secrets.token_urlsafe(12)
            kdf = CredentialKdf()
            digest, salt, params = kdf.hash_password(architect_password)
            created = utc_now_iso()
            identity = LocalIdentity(
                actor_id=actor,
                username=username,
                display_name=display_name,
                roles=("architect",),
                workspace_scopes=("devpilot-local",),
                status="active",
                created_at=created,
            )
            credential = CredentialRecord(
                actor, username, digest, salt, kdf.algorithm, kdf.params.version, params, created, created, 1
            )
            with store.transaction() as con:
                con.execute(
                    "INSERT INTO identities(actor_id,username,display_name,roles_json,workspace_scopes_json,status,created_at) VALUES(?,?,?,?,?,?,?)",
                    (identity.actor_id, identity.username, identity.display_name, json.dumps(list(identity.roles)), json.dumps(list(identity.workspace_scopes)), identity.status, identity.created_at),
                )
                con.execute(
                    "INSERT INTO credentials(actor_id,username,password_hash,salt,kdf_algorithm,kdf_version,kdf_params_json,created_at,updated_at,credential_version) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (credential.actor_id, credential.username, credential.password_hash, credential.salt, credential.kdf_algorithm, credential.kdf_version, json.dumps(credential.kdf_params, sort_keys=True), credential.created_at, credential.updated_at, credential.credential_version),
                )
            synthetic_architect_created = True
            owner_preserved = store.owner_exists()
            if not owner_preserved:
                raise RuntimeError("negative-role setup violated owner-presence invariant")

            # Isolate the negative role from the owner browser session/cookies.
            page.close()
            context.close()
            negative_context = browser.new_context(viewport={"width": 1440, "height": 1000})
            negative_context.add_init_script(project_context_script)
            negative_page = negative_context.new_page()
            page = negative_page
            negative_page.on("response", on_response)
            negative_page.on("console", on_console)
            negative_page.on("pageerror", on_page_error)
            negative_page.on("requestfailed", on_request_failed)

            ui = urlsplit(args.ui_url)
            login_url = f"{ui.scheme}://{ui.netloc}/login?reason=required&return={quote('/story/code', safe='')}"
            negative_page.goto(login_url, wait_until="load")
            negative_page.locator(".login-view").wait_for(timeout=12000)
            negative_page.locator('input[name="username"]').fill(username)
            negative_page.locator('input[name="password"]').fill(architect_password)
            negative_page.locator('button[type="submit"]').click()
            negative_page.locator('[data-gsdlc09b="code-workbench"]').wait_for(timeout=15000)

            session_check = negative_context.request.get(
                args.api_url + "/auth/session", headers={"Origin": f"{ui.scheme}://{ui.netloc}"}
            )
            if session_check.status != 200:
                raise RuntimeError(f"architect negative-role session check failed status={session_check.status}")
            session_payload = session_check.json()
            roles = list((((session_payload.get("session") or {}).get("principal") or {}).get("roles") or []))
            if "architect" not in roles or any(role in {"owner", "developer"} for role in roles):
                raise RuntimeError(f"negative-role session authority mismatch roles={roles}")
            route_meta = negative_page.locator(".route-header p").inner_text(timeout=3000)
            if "architect" not in route_meta or "owner" in route_meta or "developer" in route_meta:
                raise RuntimeError(f"negative-role UI authority mismatch route_meta={route_meta!r}")
            negative_page.locator('[data-source-path="src/app.py"]').click()
            wait_source_loaded(negative_page, "src/app.py")
            disabled = negative_page.locator('[data-save-draft="true"]').is_disabled()
            if not disabled:
                raise RuntimeError("architect negative-role UI unexpectedly enabled Save Draft")
            results.append(("role-negative-authoring-disabled", True))
            negative_page.screenshot(path=str(evidence / "05_role_negative_read_only.png"), full_page=True)
            negative_context.close()

            # Remove the exact synthetic identity before leaving the live test.
            existing = store.get_identity_by_username(username)
            if existing is None or existing.actor_id != actor or existing.display_name != display_name or tuple(existing.roles) != ("architect",):
                raise RuntimeError("synthetic architect cleanup invariant mismatch")
            with store.transaction() as con:
                con.execute("DELETE FROM identities WHERE actor_id=? AND username=?", (actor, username))
            synthetic_architect_removed = store.get_identity_by_username(username) is None
            owner_preserved = store.owner_exists()
            if not synthetic_architect_removed or not owner_preserved:
                raise RuntimeError("synthetic architect cleanup or owner-presence invariant failed")
            browser.close()

    except BaseException as exc:
        if page is not None:
            capture_failure(evidence, page, step=step, error=exc, events=events)
        print(f"BLOCK - browser acceptance step={step}: {type(exc).__name__}: {exc}")
        return_code = 2
    else:
        return_code = 0
    finally:
        if synthetic_architect_created and not synthetic_architect_removed:
            try:
                from devpilot_core.identity.auth_store import LocalAuthStore
                store = LocalAuthStore(auth_root)
                existing = store.get_identity_by_username("browser.architect")
                if existing is not None and existing.actor_id == "gsdlc09b-browser-architect" and existing.display_name == "GSDLC 09-B Browser Architect" and tuple(existing.roles) == ("architect",):
                    with store.transaction() as con:
                        con.execute("DELETE FROM identities WHERE actor_id=? AND username=?", ("gsdlc09b-browser-architect", "browser.architect"))
                    synthetic_architect_removed = store.get_identity_by_username("browser.architect") is None
                owner_preserved = store.owner_exists()
            except Exception as cleanup_exc:
                print(f"BLOCK - synthetic architect cleanup failed: {cleanup_exc}")
                return_code = 2
        try:
            subprocess.run(
                [sys.executable, str(fixture_script), "--root", str(root), "--action", "restore"],
                check=True,
                capture_output=True,
                text=True,
            )
            restored = source.is_file() and sha(source) == baseline_sha
        except Exception as restore_exc:
            print(f"BLOCK - browser fixture restore failed: {restore_exc}")
            restored = False
            return_code = 2

    results.append(("source-restored", restored))
    ok = return_code == 0 and all(value for _, value in results)
    report = {
        "schema_id": "DEVPL-GSDLC-09-B-BROWSER-ACCEPTANCE-V1",
        "status": "PASS" if ok else "BLOCK",
        "mode": "browser-real/live-api-ui",
        "browser_prep_id": args.browser_prep_id,
        "implementation_commit": args.implementation_commit,
        "cases": [{"id": key, "pass": value} for key, value in results],
        "screenshots": sorted(p.name for p in evidence.glob("*.png") if p.name != "99_browser_failure.png"),
        "failure_artifact": "DEVPL_GSDLC_09_B_BROWSER_FAILURE.json" if (evidence / "DEVPL_GSDLC_09_B_BROWSER_FAILURE.json").is_file() else None,
        "source_baseline_sha256": baseline_sha,
        "source_restored": restored,
        "full_regression_runs": 0,
        "browser_runs": 1,
        "network_runtime_used": False,
        "external_api_used": False,
        "source_mutations_performed_by_workbench": False,
        "negative_role_identity_strategy": "separate-synthetic-architect/fresh-browser-context/real-login-view",
        "synthetic_architect_removed": synthetic_architect_removed,
        "owner_preserved": owner_preserved,
        "diagnostic_events": events,
        "generated_at_utc": now(),
    }
    (evidence / "DEVPL_GSDLC_09_B_BROWSER_ACCEPTANCE.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    passed = sum(1 for _, value in results if value)
    print(("PASS" if ok else "BLOCK") + f" - browser acceptance {passed}/{len(results)}; source_restored={restored}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
