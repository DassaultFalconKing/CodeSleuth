$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $Here '../..')).Path
$Settings = Join-Path $Root '.opencode/codesleuth-user.json'
$ExaEnabled = $true
if (Test-Path $Settings) {
  try {
    $Config = Get-Content -Raw $Settings | ConvertFrom-Json
    if ($null -ne $Config.runtime.exaEnabled) { $ExaEnabled = [bool]$Config.runtime.exaEnabled }
  } catch {
    $ExaEnabled = $true
  }
}
if ($ExaEnabled) { $env:OPENCODE_ENABLE_EXA = '1' } else { Remove-Item Env:OPENCODE_ENABLE_EXA -ErrorAction SilentlyContinue }
& opencode @args
exit $LASTEXITCODE
