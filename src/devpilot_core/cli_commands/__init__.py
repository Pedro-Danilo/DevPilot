"""Explicit CLI command handler modules for POST-H-006 migrations.

The package contains small, domain-oriented handlers that build
``CommandResult`` instances without printing, dispatching or dynamically loading
code. ``src/devpilot_core/cli.py`` remains the public parser/UX boundary while
micro-sprints migrate implementation logic incrementally.
"""

from .industrial_readiness import (
    handle_industrial_readiness_check,
    handle_industrial_readiness_production_ready_local,
    handle_industrial_readiness_production_ready_local_final,
)
from .release import (
    handle_backup_create,
    handle_backup_list,
    handle_backup_restore,
    handle_install_plan,
    handle_install_windows_smoke,
    handle_package_build,
    handle_package_source_zip_policy,
    handle_release_artifact_manifest,
    handle_release_candidate_evidence_freshness,
    handle_release_candidate_final,
    handle_release_candidate_install_smoke,
    handle_release_candidate_profile,
    handle_release_candidate_ui_api_smoke,
    handle_release_changelog,
    handle_release_checksum,
    handle_release_environment_snapshot,
    handle_release_manifest,
    handle_release_python_artifact_verify,
    handle_release_reproducibility_pack,
    handle_release_reproducibility_verify,
    handle_release_sbom,
    handle_release_smoke_test,
    handle_release_source_archive_manifest,
    handle_release_upgrade_rollback_dry_run,
    handle_release_verify,
    handle_upgrade_check,
)
from .workspace import handle_workspace_bootstrap, handle_workspace_init, handle_workspace_readiness_preview, handle_workspace_status
from .validation import handle_validate_scope

__all__ = [
    "handle_backup_create",
    "handle_backup_list",
    "handle_backup_restore",
    "handle_install_plan",
    "handle_install_windows_smoke",
    "handle_package_build",
    "handle_package_source_zip_policy",
    "handle_release_artifact_manifest",
    "handle_release_candidate_evidence_freshness",
    "handle_release_candidate_final",
    "handle_release_candidate_install_smoke",
    "handle_release_candidate_profile",
    "handle_release_candidate_ui_api_smoke",
    "handle_release_changelog",
    "handle_release_checksum",
    "handle_release_environment_snapshot",
    "handle_release_manifest",
    "handle_release_python_artifact_verify",
    "handle_release_reproducibility_pack",
    "handle_release_reproducibility_verify",
    "handle_release_sbom",
    "handle_release_smoke_test",
    "handle_release_source_archive_manifest",
    "handle_release_upgrade_rollback_dry_run",
    "handle_release_verify",
    "handle_upgrade_check",
    "handle_industrial_readiness_check",
    "handle_industrial_readiness_production_ready_local",
    "handle_industrial_readiness_production_ready_local_final",
    "handle_validate_scope",
    "handle_workspace_bootstrap",
    "handle_workspace_init",
    "handle_workspace_readiness_preview",
    "handle_workspace_status",
]
