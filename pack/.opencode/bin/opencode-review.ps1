$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $Here '../..')).Path
$RepoRoot = (Resolve-Path (Join-Path $Here '../../..')).Path
$Settings = Join-Path $Root '.opencode/review-pack-user.json'
$TuiConfig = Join-Path $Root '.opencode/tui.json'
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
if (Test-Path $TuiConfig) { $env:OPENCODE_TUI_CONFIG = $TuiConfig }

# OPENCODE_CONFIG_DIR is additive. When CodeSleuth supplies an external writable
# runtime, explicitly disable target-project .opencode discovery before launch so
# read-only analysis cannot bootstrap or rewrite tracked target package metadata.
if (-not [string]::IsNullOrWhiteSpace($env:CODESLEUTH_EHA_RUNTIME_CONFIG)) {
  $RuntimeConfig = [System.IO.Path]::GetFullPath($env:CODESLEUTH_EHA_RUNTIME_CONFIG)
  $SourceConfig = Join-Path $Root '.opencode'
  $Helper = Join-Path $RepoRoot 'scripts/eha_opencode_runtime.py'
  if (-not (Test-Path -LiteralPath $Helper -PathType Leaf)) {
    throw "CodeSleuth EHA runtime-config helper missing at exact target: $Helper"
  }
  & python3 $Helper --source $SourceConfig --target $RuntimeConfig
  if ($LASTEXITCODE -ne 0) {
    throw "CodeSleuth EHA runtime-config preparation failed with exit code $LASTEXITCODE"
  }
  $env:OPENCODE_CONFIG_DIR = $RuntimeConfig
  $env:OPENCODE_DISABLE_PROJECT_CONFIG = "1"
}

& opencode @args
exit $LASTEXITCODE
