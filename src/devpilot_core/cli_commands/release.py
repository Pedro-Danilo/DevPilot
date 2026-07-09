from __future__ import annotations

from pathlib import Path

from devpilot_core.cli_models import CommandResult
from devpilot_core.release import (
    BackupCreateBuilder,
    BackupCreateOptions,
    BackupListBuilder,
    BackupListOptions,
    BackupRestoreBuilder,
    BackupRestoreOptions,
    InstallPlanBuilder,
    InstallPlanOptions,
    PackageBuildBuilder,
    PackageBuildOptions,
    PythonArtifactInstallVerificationOptions,
    PythonArtifactInstallVerifier,
    ReleaseArtifactManifestBuilder,
    ReleaseArtifactManifestOptions,
    ReleaseChangelogBuilder,
    ReleaseChangelogOptions,
    ReleaseChecksumBuilder,
    ReleaseChecksumOptions,
    ReleaseEnvironmentSnapshotBuilder,
    ReleaseEnvironmentSnapshotOptions,
    ReleaseManifestBuilder,
    ReleaseManifestOptions,
    ReleaseReproducibilityPackBuilder,
    ReleaseReproducibilityPackOptions,
    ReleaseReproducibilityVerifier,
    ReleaseReproducibilityVerifyOptions,
    ReleaseSbomBuilder,
    ReleaseSbomOptions,
    ReleaseSmokeTestBuilder,
    ReleaseSmokeTestOptions,
    ReleaseVerifyBuilder,
    ReleaseVerifyOptions,
    SourceArchiveManifestBuilder,
    SourceArchiveManifestOptions,
    SourceZipPolicyOptions,
    SourceZipReleasePolicyValidator,
    UpgradeCheckBuilder,
    UpgradeCheckOptions,
    UpgradeRollbackDryRunOptions,
    UpgradeRollbackDryRunRunner,
    WindowsInstallSmokeOptions,
    WindowsInstallSmokeRunner,
)
from devpilot_core.release_candidate import (
    EvidenceFreshnessOptions,
    EvidenceFreshnessScanner,
    LocalInstallSmokeOptions,
    LocalInstallSmokeRunner,
    LocalReleaseCandidateOptions,
    LocalReleaseCandidateReporter,
    ReleaseCandidateVerificationProfile,
    ReleaseCandidateVerificationProfileOptions,
    UiApiRcSmokeOptions,
    UiApiRcSmokeRunner,
)


def handle_release_manifest(root: Path, *, version: str) -> CommandResult:
    """Build the result for ``release manifest`` without rendering or persistence."""

    return ReleaseManifestBuilder(root, options=ReleaseManifestOptions(version=version)).build()


def handle_release_changelog(
    root: Path,
    *,
    version: str,
    from_sprint: str = "FUNC-SPRINT-74",
    to_sprint: str | None = None,
) -> CommandResult:
    """Build the result for ``release changelog`` without rendering or persistence."""

    return ReleaseChangelogBuilder(
        root,
        options=ReleaseChangelogOptions(version=version, from_sprint=from_sprint, to_sprint=to_sprint),
    ).build()


def handle_release_sbom(root: Path, *, version: str | None = None) -> CommandResult:
    """Build the result for ``release sbom`` without rendering or persistence."""

    return ReleaseSbomBuilder(root, options=ReleaseSbomOptions(version=version)).build()


def handle_release_environment_snapshot(root: Path, *, write_report: bool = False) -> CommandResult:
    """Build the POST-H-017-B environment snapshot result."""

    return ReleaseEnvironmentSnapshotBuilder(
        root,
        options=ReleaseEnvironmentSnapshotOptions(write_report=write_report),
    ).build()


def handle_release_source_archive_manifest(root: Path, *, write_report: bool = False) -> CommandResult:
    """Build the POST-H-017-C source archive manifest result."""

    return SourceArchiveManifestBuilder(
        root,
        options=SourceArchiveManifestOptions(write_report=write_report),
    ).build()


def handle_release_reproducibility_verify(root: Path, *, pack: str, write_report: bool = False) -> CommandResult:
    """Build the POST-H-017-D reproducibility verification result."""

    return ReleaseReproducibilityVerifier(
        root,
        options=ReleaseReproducibilityVerifyOptions(pack=pack, write_report=write_report),
    ).verify()


def handle_release_reproducibility_pack(
    root: Path,
    *,
    write_report: bool = False,
    verify: bool = False,
    require_clean_git: bool = False,
) -> CommandResult:
    """Build the POST-H-017-E local reproducibility pack result."""

    return ReleaseReproducibilityPackBuilder(
        root,
        options=ReleaseReproducibilityPackOptions(
            write_report=write_report,
            verify_after_build=verify,
            require_clean_git=require_clean_git,
        ),
    ).build()


def handle_release_checksum(root: Path, *, artifact: str, version: str | None = None) -> CommandResult:
    """Build the checksum result for one local release artifact."""

    return ReleaseChecksumBuilder(root, options=ReleaseChecksumOptions(artifact=artifact, version=version)).build()


def handle_release_smoke_test(
    root: Path,
    *,
    artifact: str,
    version: str | None = None,
    timeout_seconds: int = 30,
) -> CommandResult:
    """Build the local release smoke-test result for one artifact."""

    return ReleaseSmokeTestBuilder(
        root,
        options=ReleaseSmokeTestOptions(artifact=artifact, version=version, timeout_seconds=timeout_seconds),
    ).build()


def handle_release_verify(
    root: Path,
    *,
    artifact: str,
    version: str | None = None,
    timeout_seconds: int = 30,
) -> CommandResult:
    """Build the consolidated local release verification result."""

    return ReleaseVerifyBuilder(
        root,
        options=ReleaseVerifyOptions(artifact=artifact, version=version, timeout_seconds=timeout_seconds),
    ).build()


def handle_release_artifact_manifest(
    root: Path,
    *,
    version: str = "0.1.0",
    verify_checksums: bool = False,
    write_report: bool = False,
) -> CommandResult:
    """Build the POST-H-027-C artifact manifest result."""

    return ReleaseArtifactManifestBuilder(
        root,
        options=ReleaseArtifactManifestOptions(
            version=version,
            verify_checksums=verify_checksums,
            write_report=write_report,
        ),
    ).build()


def handle_release_upgrade_rollback_dry_run(
    root: Path,
    *,
    from_version: str,
    to_version: str,
    artifact_manifest: str = "outputs/release/release_artifact_manifest.json",
    backup_id: str | None = None,
    output_json: str = "outputs/reports/upgrade_rollback_dry_run_report.json",
    output_markdown: str = "outputs/reports/upgrade_rollback_dry_run_report.md",
    write_report: bool = False,
) -> CommandResult:
    """Build the POST-H-027-E upgrade/rollback dry-run result."""

    return UpgradeRollbackDryRunRunner(
        root,
        UpgradeRollbackDryRunOptions(
            from_version=from_version,
            to_version=to_version,
            artifact_manifest=artifact_manifest,
            backup_id=backup_id,
            output_json=output_json,
            output_markdown=output_markdown,
            write_report=write_report,
        ),
    ).run()


def handle_release_python_artifact_verify(
    root: Path,
    *,
    artifact: str,
    timeout_seconds: int = 60,
    keep_temp: bool = False,
    write_report: bool = False,
) -> CommandResult:
    """Build the POST-H-027-B Python artifact install verification result."""

    return PythonArtifactInstallVerifier(
        root,
        PythonArtifactInstallVerificationOptions(
            artifact=artifact,
            timeout_seconds=timeout_seconds,
            keep_temp=keep_temp,
            write_report=write_report,
        ),
    ).run()


def handle_install_plan(
    root: Path,
    *,
    mode: str = "all",
    version: str | None = None,
    artifact: str | None = None,
    python_executable: str = "python",
) -> CommandResult:
    """Build the local install plan result."""

    return InstallPlanBuilder(
        root,
        options=InstallPlanOptions(
            mode=mode,
            version=version,
            artifact=artifact,
            python_executable=python_executable,
        ),
    ).build()


def handle_install_windows_smoke(
    root: Path,
    *,
    mode: str,
    version: str,
    artifact: str | None = None,
    output_json: str = "outputs/reports/windows_install_smoke_report.json",
    output_markdown: str = "outputs/reports/windows_install_smoke_report.md",
    write_report: bool = False,
) -> CommandResult:
    """Build the POST-H-027-D Windows install smoke result."""

    return WindowsInstallSmokeRunner(
        root,
        WindowsInstallSmokeOptions(
            mode=mode,
            version=version,
            artifact=artifact,
            output_json=output_json,
            output_markdown=output_markdown,
            write_report=write_report,
        ),
    ).run()


def handle_backup_create(root: Path, *, dry_run: bool = True, execute: bool = False) -> CommandResult:
    """Build the backup-create result without CLI rendering or persistence."""

    return BackupCreateBuilder(root, options=BackupCreateOptions(dry_run=dry_run, execute=execute)).build()


def handle_backup_list(root: Path, *, limit: int = 50) -> CommandResult:
    """Build the backup-list result without CLI rendering or persistence."""

    return BackupListBuilder(root, options=BackupListOptions(limit=limit)).build()


def handle_backup_restore(
    root: Path,
    *,
    backup_id: str,
    dry_run: bool = True,
    execute: bool = False,
    confirm_restore: bool = False,
) -> CommandResult:
    """Build the backup-restore result without CLI rendering or persistence."""

    return BackupRestoreBuilder(
        root,
        options=BackupRestoreOptions(
            backup_id=backup_id,
            dry_run=dry_run,
            execute=execute,
            confirm_restore=confirm_restore,
        ),
    ).build()


def handle_upgrade_check(root: Path, *, target_version: str | None = None) -> CommandResult:
    """Build the local upgrade readiness result."""

    return UpgradeCheckBuilder(root, options=UpgradeCheckOptions(target_version=target_version)).build()


def handle_package_build(
    root: Path,
    *,
    kind: str,
    version: str,
    execute: bool = False,
) -> CommandResult:
    """Build or plan local release packages without rendering or persistence."""

    return PackageBuildBuilder(
        root,
        options=PackageBuildOptions(version=version, kind=kind, execute=execute),
    ).build()


def handle_package_source_zip_policy(
    root: Path,
    *,
    artifact: str | None = None,
    policy_path: str = ".devpilot/release/source_zip_release_policy.json",
    write_report: bool = False,
) -> CommandResult:
    """Build the POST-H-027-A source ZIP policy validation result."""

    return SourceZipReleasePolicyValidator(
        root,
        SourceZipPolicyOptions(
            artifact=artifact,
            policy_path=policy_path,
            write_report=write_report,
        ),
    ).run()


def handle_release_candidate_evidence_freshness(
    root: Path,
    *,
    criteria_path: str = ".devpilot/release/local_release_candidate_criteria.json",
    output_json: str = "outputs/reports/evidence_freshness_report.json",
    output_markdown: str = "outputs/reports/evidence_freshness_report.md",
    write_report: bool = False,
) -> CommandResult:
    """Build the POST-H-026-A evidence freshness result."""

    return EvidenceFreshnessScanner(
        root,
        options=EvidenceFreshnessOptions(
            criteria_path=criteria_path,
            output_json=output_json,
            output_markdown=output_markdown,
            write_report=write_report,
        ),
    ).scan()


def handle_release_candidate_profile(
    root: Path,
    *,
    profile: str,
    test_profiles_path: str,
    tcr_v2_path: str,
    output_json: str,
    output_markdown: str,
    write_report: bool = False,
) -> CommandResult:
    """Build the POST-H-026-B release candidate profile result."""

    return ReleaseCandidateVerificationProfile(
        root,
        ReleaseCandidateVerificationProfileOptions(
            profile_id=profile,
            test_profiles_path=test_profiles_path,
            tcr_v2_path=tcr_v2_path,
            output_json=output_json,
            output_markdown=output_markdown,
            write_report=write_report,
        ),
    ).inspect()


def handle_release_candidate_ui_api_smoke(
    root: Path,
    *,
    base_url: str = "http://127.0.0.1:8787",
    ui_origin: str = "http://127.0.0.1:5173",
    output_json: str = "outputs/reports/ui_api_rc_smoke_report.json",
    output_markdown: str = "outputs/reports/ui_api_rc_smoke_report.md",
    write_report: bool = False,
) -> CommandResult:
    """Build the POST-H-026-C UI/API local RC smoke result."""

    return UiApiRcSmokeRunner(
        root,
        UiApiRcSmokeOptions(
            base_url=base_url,
            ui_origin=ui_origin,
            output_json=output_json,
            output_markdown=output_markdown,
            write_report=write_report,
        ),
    ).run()


def handle_release_candidate_install_smoke(
    root: Path,
    *,
    output_json: str,
    output_markdown: str,
    candidate_zip: str | None = None,
    write_report: bool = False,
) -> CommandResult:
    """Build the POST-H-026-D local install smoke result."""

    return LocalInstallSmokeRunner(
        root,
        LocalInstallSmokeOptions(
            output_json=output_json,
            output_markdown=output_markdown,
            candidate_zip=candidate_zip,
            write_report=write_report,
        ),
    ).run()


def handle_release_candidate_final(
    root: Path,
    *,
    criteria_path: str = ".devpilot/release/local_release_candidate_criteria.json",
    output_json: str = "outputs/reports/local_release_candidate_report.json",
    output_markdown: str = "outputs/reports/local_release_candidate_report.md",
    write_report: bool = False,
) -> CommandResult:
    """Build the POST-H-026-E final local release candidate result."""

    return LocalReleaseCandidateReporter(
        root,
        LocalReleaseCandidateOptions(
            criteria_path=criteria_path,
            output_json=output_json,
            output_markdown=output_markdown,
            write_report=write_report,
        ),
    ).run()
