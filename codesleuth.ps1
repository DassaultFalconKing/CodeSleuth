$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:REVIEW_PACK_DISTRIBUTION_ROOT = $Here
& python (Join-Path $Here 'pack/.opencode/bin/review_pack_tui_bootstrap.py') @args
exit $LASTEXITCODE
