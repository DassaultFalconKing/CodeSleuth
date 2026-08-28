$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$Here;$env:PYTHONPATH" } else { $Here }
& python "$Here/codesleuth_reports.py" @args
exit $LASTEXITCODE
