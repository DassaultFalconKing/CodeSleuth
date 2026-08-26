$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    $Python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $Python) {
    throw 'review-pack updater requires Python 3'
}

& $Python.Source (Join-Path $Here 'review-pack-update.py') @args
exit $LASTEXITCODE
