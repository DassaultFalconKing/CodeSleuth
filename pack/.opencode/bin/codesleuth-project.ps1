$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
& python (Join-Path $Here 'codesleuth_project.py') @args
exit $LASTEXITCODE
