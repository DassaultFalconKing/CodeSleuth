$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $Here '../..')).Path
$env:REVIEW_PACK_TARGET_ROOT = $Root
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python3 -ErrorAction Stop }
& $Python.Source (Join-Path $Here 'review_pack_tui_bootstrap.py') --target $Root @args
exit $LASTEXITCODE
