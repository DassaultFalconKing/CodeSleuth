$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $Here '../..')).Path
$env:REVIEW_PACK_TARGET_ROOT = $Root
& python (Join-Path $Here 'review_pack_tui_bootstrap.py') --target $Root @args
exit $LASTEXITCODE
