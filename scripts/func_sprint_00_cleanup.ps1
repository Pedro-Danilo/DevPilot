<#
.SYNOPSIS
  Limpieza segura de artefactos generados para FUNC-SPRINT-00.

.DESCRIPTION
  Este script busca artefactos generados que no deben versionarse en DevPilot Local:
  __pycache__, .pytest_cache, *.egg-info y ZIPs locales de exportación.

  Por defecto ejecuta en modo dry-run: solo muestra lo que eliminaría.
  Para eliminar realmente, usar: .\scripts\func_sprint_00_cleanup.ps1 -Execute

.PARAMETER Execute
  Si se especifica, elimina los artefactos encontrados. Sin este parámetro no modifica archivos.
#>

param(
    [switch]$Execute
)

$ErrorActionPreference = "Stop"
$Root = (Get-Location).Path

$Targets = @()

$Targets += Get-ChildItem -Path $Root -Directory -Recurse -Force -Filter "__pycache__" -ErrorAction SilentlyContinue
$Targets += Get-ChildItem -Path $Root -Directory -Recurse -Force -Filter ".pytest_cache" -ErrorAction SilentlyContinue
$Targets += Get-ChildItem -Path $Root -Directory -Recurse -Force -Filter "*.egg-info" -ErrorAction SilentlyContinue
$Targets += Get-ChildItem -Path $Root -File -Force -Filter "DevPilot_Local*.zip" -ErrorAction SilentlyContinue
$Targets += Get-ChildItem -Path $Root -File -Force -Filter "repo_DevPilot_Local*.zip" -ErrorAction SilentlyContinue
$Targets += Get-ChildItem -Path $Root -File -Force -Filter "patch_*.zip" -ErrorAction SilentlyContinue

$Targets = $Targets | Sort-Object FullName -Unique

if (-not $Targets -or $Targets.Count -eq 0) {
    Write-Host "FUNC-SPRINT-00 cleanup: no generated artifacts found."
    exit 0
}

Write-Host "FUNC-SPRINT-00 cleanup: artifacts detected:"
foreach ($Item in $Targets) {
    $Relative = $Item.FullName.Replace($Root, ".")
    Write-Host " - $Relative"
}

if (-not $Execute) {
    Write-Host "Dry-run only. Re-run with -Execute to delete these artifacts."
    exit 0
}

foreach ($Item in $Targets) {
    Remove-Item -LiteralPath $Item.FullName -Recurse -Force
}

Write-Host "FUNC-SPRINT-00 cleanup: generated artifacts removed."
