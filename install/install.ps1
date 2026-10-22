$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Skills = @("soil-motion-html")

$Targets = @(
  @{ Name = "Google Antigravity"; Path = "$HOME\.gemini\config\skills" },
  @{ Name = "OpenCode (.config)"; Path = "$HOME\.config\opencode\skills" },
  @{ Name = "OpenCode (.agents)"; Path = "$HOME\.agents\skills" },
  @{ Name = "Claude Code / Cowork"; Path = "$HOME\.claude\skills" },
  @{ Name = "Codex"; Path = "$HOME\.codex\skills" }
)

foreach ($Target in $Targets) {
  $DestRoot = $Target.Path
  if (-not (Test-Path $DestRoot)) {
    New-Item -ItemType Directory -Force -Path $DestRoot | Out-Null
  }
  foreach ($Skill in $Skills) {
    $Src = Join-Path $RepoRoot "skills\$Skill"
    $Dest = Join-Path $DestRoot $Skill
    if (Test-Path $Dest) {
      Remove-Item -Recurse -Force $Dest
    }
    Copy-Item -Path $Src -Destination $Dest -Recurse -Force
  }
  Write-Host "[OK] Installed ($($Skills -join ', ')) to $($Target.Name): $DestRoot" -ForegroundColor Green
}

Write-Host "`n🎉 The SOIL Motion skill (soil-motion-html) is installed!" -ForegroundColor Cyan
Write-Host "👉 Open a new chat in Antigravity, OpenCode, Claude Code, or Codex to start animating your teaching slides." -ForegroundColor Cyan
