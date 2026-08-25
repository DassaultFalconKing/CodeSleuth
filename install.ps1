$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    $Python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $Python) {
    throw 'review-pack installer requires Python 3'
}

& $Python.Source (Join-Path $Here 'install.py') @args
exit $LASTEXITCODE
