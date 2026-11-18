# Rebbi Demo Day autopilot: builds, calibrates, runs and reports the five budget scenarios with
# no human input. Start it once from the repo root, in its own PowerShell window:
#
#     powershell -ExecutionPolicy Bypass -File scripts\autopilot.ps1
#
# It loops through phases, each marked by a file in docs\demo\state\ so any restart resumes:
#   1. BUILD_DONE   Claude Code (headless) builds rebbi/demo per docs/demo/TASK.md, with tests
#                   and a zero-usage rehearsal.
#   2. RUNS_DONE    python -m rebbi.demo run-all: calibration, then every scenario, one run at a
#                   time, results saved after each run. A plan-limit stop just waits and resumes.
#   3. FINAL_DONE   Claude Code (headless) checks the results page, writes the hand-back, commits.
# A Claude session that ends early (plan limit, crash) is simply started again after a wait.
# Stop it any time with Ctrl+C; run the same command to resume.

param(
    [string]$StopNewRunsAt = "2026-11-18T21:00:00",   # no new run starts after this (local time)
    [string]$HardStop = "2026-11-18T23:00:00",        # finalize with whatever is done
    [int]$LimitWaitMinutes = 20,                      # wait after a plan-limit stop
    [int]$MaxClaudeSessions = 60
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:GIT_TERMINAL_PROMPT = "0"          # never hang on a git credential prompt
$env:PYTHONIOENCODING = "utf-8"
$State = Join-Path $Root "docs\demo\state"
$Logs = Join-Path $Root "logs\autopilot"
New-Item -ItemType Directory -Force -Path $State, $Logs | Out-Null
$Py = Join-Path $Root ".venv\Scripts\python.exe"

# Keep the computer awake while this window runs (no change to power settings).
Add-Type -Namespace RebbiWin -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
[RebbiWin.Power]::SetThreadExecutionState([uint32]2147483649) | Out-Null   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED

function Log([string]$msg) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Write-Host $line
    Add-Content -Path (Join-Path $Logs "autopilot.log") -Value $line -Encoding utf8
}

function Done([string]$name) { Test-Path (Join-Path $State $name) }

# Permission mode for headless Claude Code: auto if this account has it, else acceptEdits with
# an allow list. Headless sessions never wait for input: anything not allowed is refused.
$script:ClaudeArgs = @("--permission-mode", "auto")
$probe = & claude -p "Reply with the word ready." --permission-mode auto --output-format text 2>&1 | Out-String
if ($LASTEXITCODE -ne 0 -or $probe -notmatch "ready") {
    Log "auto mode unavailable ($($probe.Trim())); using acceptEdits with an allow list"
    $script:ClaudeArgs = @("--permission-mode", "acceptEdits", "--allowedTools",
        "Bash", "PowerShell", "Read", "Edit", "Write", "Glob", "Grep", "WebSearch", "WebFetch", "TodoWrite")
}

$script:Sessions = 0
function Invoke-Claude([string]$tag, [string]$prompt) {
    $script:Sessions++
    if ($script:Sessions -gt $MaxClaudeSessions) { Log "too many Claude sessions; stopping"; exit 2 }
    $out = Join-Path $Logs ("claude-{0:D3}-{1}.jsonl" -f $script:Sessions, $tag)
    Log "Claude session $($script:Sessions) ($tag) -> $out"
    & claude -p $prompt @script:ClaudeArgs --output-format stream-json --verbose 2>&1 | Out-File -FilePath $out -Encoding utf8
    $code = $LASTEXITCODE
    $tail = (Get-Content $out -Tail 5 -ErrorAction SilentlyContinue) -join " "
    if ($code -ne 0 -or $tail -match '"is_error":\s*true') {
        Log "Claude session ended with an error (exit $code); waiting $LimitWaitMinutes min, then resuming"
        Start-Sleep -Seconds ($LimitWaitMinutes * 60)
    }
}

$Common = "Work autonomously: nobody will answer questions. Read docs/demo/TASK.md (the full task) and docs/demo/PROGRESS.md (where earlier sessions stopped; create it if missing). Update PROGRESS.md after every step, and commit locally after every step (never push from this phase)."

Log "autopilot started in $Root (stop new runs at $StopNewRunsAt, hard stop $HardStop)"
while ($true) {
    $now = Get-Date
    if (Done "FINAL_DONE") { Log "all phases done; see docs\demo\results.html"; break }

    if (-not (Done "BUILD_DONE")) {
        if ($now -gt ([datetime]$HardStop)) { Log "hard stop reached before the build finished"; break }
        Invoke-Claude "build" "$Common Phase: BUILD (TASK.md sections 3 to 6). Build everything, run the tests and the zero-usage rehearsal, fix what fails. When run-all, report and the rehearsal all work, create docs/demo/state/BUILD_DONE and stop."
        continue
    }

    if (-not (Done "RUNS_DONE")) {
        if (-not (Test-Path $Py)) { Log "missing $Py; asking Claude to repair the setup"; Remove-Item (Join-Path $State "BUILD_DONE"); continue }
        Log "run-all starting"
        & $Py -m rebbi.demo run-all --stop-new-runs-at $StopNewRunsAt 2>&1 | Out-File -FilePath (Join-Path $Logs "run-all.log") -Append -Encoding utf8
        $code = $LASTEXITCODE
        Log "run-all exited with $code"
        if ($code -eq 0) {                                      # nothing pending, or the stop time passed
            New-Item -ItemType File -Force -Path (Join-Path $State "RUNS_DONE") | Out-Null
            continue
        }
        if ($code -eq 3) { Start-Sleep -Seconds ($LimitWaitMinutes * 60); continue }   # plan limit
        Invoke-Claude "fix" "$Common Phase: FIX. 'python -m rebbi.demo run-all' just failed with exit code $code. Read the end of logs/autopilot/run-all.log, find the cause, fix it with a test, and make sure completed runs and results are untouched. Do not start experiment runs yourself; stop when the fix is committed."
        continue
    }

    Invoke-Claude "final" "$Common Phase: FINAL (TASK.md section 8). Regenerate the report, check docs/demo/results.html against runs/demo/results.csv, write DECISIONS.md, README.md and HANDBACK.md, commit, try 'git push -u origin demo-scenarios' once (skip if it fails), then create docs/demo/state/FINAL_DONE."
    if (-not (Done "FINAL_DONE") -and (Get-Date) -gt ([datetime]$HardStop).AddHours(1)) { Log "final phase did not finish"; break }
}
[RebbiWin.Power]::SetThreadExecutionState([uint32]2147483648) | Out-Null   # back to normal
Log "autopilot finished"
