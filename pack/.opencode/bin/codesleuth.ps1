$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $Here '../..')).Path
$env:CODESLEUTH_TARGET_ROOT = $Root
& python (Join-Path $Here 'codesleuth_tui_bootstrap.py') --target $Root @args
exit $LASTEXITCODE
