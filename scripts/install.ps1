$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
& (Join-Path $RepoRoot "install\install.ps1")
