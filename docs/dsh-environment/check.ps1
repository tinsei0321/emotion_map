# EMC arrival health check (PT-CB16 S1 M3)
# Usage: powershell -ExecutionPolicy Bypass -File docs/dsh-environment/check.ps1 [-ExpectedBranch EMC_Codex_Harness]
param(
  [string]$ExpectedBranch = "EMC_Codex_Harness"
)
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$DshHome = Join-Path $env:USERPROFILE ".dsh"
$script:fail = $false

function Check([string]$name, [scriptblock]$cond, [string]$fix) {
  if (& $cond) { Write-Host "[OK] $name" }
  else { Write-Host "[WARN] $name"; Write-Host "       fix: $fix"; $script:fail = $true }
}

Check "EMC repo exists" { Test-Path $Repo } "git clone/pull to {REPO}"

$branch = git -C $Repo rev-parse --abbrev-ref HEAD 2>$null
Check "branch = $ExpectedBranch" { $branch -eq $ExpectedBranch } "git -C {REPO} switch $ExpectedBranch"

Check "dsh profile emc-test exists" { Test-Path (Join-Path $DshHome "profiles\emc-test") } "copy {DSH_HOME}/profiles/emc-analysis template and name as needed"
Check "dsh profile emc-analysis exists" { Test-Path (Join-Path $DshHome "profiles\emc-analysis") } "copy docs/dsh-environment/profiles/emc-analysis to {DSH_HOME}/profiles/emc-analysis"

Check "port 8600 MCP alive" { (Get-NetTCPConnection -LocalPort 8600 -State Listen -ErrorAction SilentlyContinue) -ne $null } "py tools/mcp_server_emc.py --http --port 8600"
Check "port 8000 backend alive" { (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) -ne $null } "py -m uvicorn api.main:app --port 8000"
Check "port 8080 frontend alive" { (Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue) -ne $null } "py frontend/serve.py 8080 --open=none"

$pending = @(Get-ChildItem -LiteralPath (Join-Path $Repo "DATA\Export\exports\render_inbox") -Filter *.json -File -ErrorAction SilentlyContinue)
Check "render_inbox no pending" { $pending.Count -eq 0 } "remove {REPO}/DATA/Export/exports/render_inbox/*.json"

Write-Host "=== RAG freshness (reuse check_server_freshness) ==="
py (Join-Path $Repo "tools\check_server_freshness.py")

if ($script:fail) { Write-Host "[FAIL] some checks failed; apply fixes above"; exit 1 }
Write-Host "[OK] all checks passed"
