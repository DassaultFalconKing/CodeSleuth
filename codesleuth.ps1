$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:CODESLEUTH_DISTRIBUTION_ROOT = $Here
& python (Join-Path $Here 'pack/.opencode/bin/codesleuth_tui_bootstrap.py') @args
exit $LASTEXITCODE
