$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:REVIEW_PACK_DISTRIBUTION_ROOT = $Here
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python3 -ErrorAction Stop }
& $Python.Source (Join-Path $Here 'pack/.opencode/bin/review_pack_tui_bootstrap.py') @args
exit $LASTEXITCODE
