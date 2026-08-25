param(
    [Parameter(Mandatory = $true)]
    [string]$Repository
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = if ($env:CODESLEUTH_MCP_PYTHON) { $env:CODESLEUTH_MCP_PYTHON } else { "python" }
& $python -m codesleuth_mcp.server --repo $Repository
exit $LASTEXITCODE
