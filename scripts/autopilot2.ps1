# Rebbi Demo Day v2, unattended. Start once from the repo root, in its own PowerShell window:
#
#     powershell -ExecutionPolicy Bypass -File scripts\autopilot2.ps1 -Machine pietro -Repeats 1-3
#     powershell -ExecutionPolicy Bypass -File scripts\autopilot2.ps1 -Machine eglis -Repeats 4-6
#
# All the logic is in Python (rebbi/demo2/autopilot.py, tested): preflight, calibration and freeze (pietro) or
# waiting for the frozen config (eglis), parallel lanes, export and push, report. This wrapper only keeps the
# computer awake while it runs. Progress: logs\demo2\<machine>\autopilot.log and status.txt.
# Stop with Ctrl+C; run the same command to resume.

param(
    [string]$Machine = "pietro",
    [string]$Repeats = "1-3",
    [int]$Lanes = 3,
    [string]$StopNewRunsAt = "2026-11-22T12:00:00"
)

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:PYTHONIOENCODING = "utf-8"
$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

# Keep the computer awake while this window runs (no change to power settings).
Add-Type -Namespace RebbiWin2 -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
[RebbiWin2.Power]::SetThreadExecutionState([uint32]2147483649) | Out-Null   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED

& $Py -m rebbi.demo2 autopilot --machine $Machine --repeats $Repeats --lanes $Lanes --stop-new-runs-at $StopNewRunsAt
$code = $LASTEXITCODE

[RebbiWin2.Power]::SetThreadExecutionState([uint32]2147483648) | Out-Null   # back to normal
Write-Host "autopilot exited with $code"
exit $code
