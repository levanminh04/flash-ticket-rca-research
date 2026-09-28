$ErrorActionPreference = 'Stop'
$taskRunRoot = [System.IO.Path]::GetFullPath('D:\Project\flash-ticket-rca-research\results\task-e\e27-041-rcd-development-recovery')
$taskRootPrefix = $taskRunRoot.TrimEnd('\') + '\'
$taskPreviousReceipt = Join-Path $taskRunRoot 'resume-01-execution.json'
while (-not (Test-Path -LiteralPath $taskPreviousReceipt)) { Start-Sleep -Seconds 2 }
$taskPrevious = Get-Content -Raw -LiteralPath $taskPreviousReceipt | ConvertFrom-Json
if ($taskPrevious.exit_code -eq 0) { throw 'Unexpected successful prior controller; no recovery mutation permitted.' }
$taskActive = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python' -and $_.CommandLine -match 'rcd_recovery.py|scripts.task_e.rcd_single_worker' })
if ($taskActive.Count -gt 0) { throw 'RCD controller or child is still active; preserve nothing yet.' }
$taskPlanPath = Join-Path $taskRunRoot 'abandoned-six-preservation-plan.json'
$taskPlan = Get-Content -Raw -LiteralPath $taskPlanPath | ConvertFrom-Json
if ($taskPlan.entries.Count -ne 6) { throw 'Expected exactly six interrupted chunks.' }
$taskReceiptPath = Join-Path $taskRunRoot 'abandoned-six-preservation-receipt.json'
if (Test-Path -LiteralPath $taskReceiptPath) { throw 'Preservation receipt already exists; do not repeat.' }
# Verify every resolved target stays inside the named run before any move.
foreach ($taskEntry in $taskPlan.entries) {
    $taskSource = [System.IO.Path]::GetFullPath($taskEntry.source)
    $taskDestination = [System.IO.Path]::GetFullPath($taskEntry.destination)
    if (-not $taskSource.StartsWith($taskRootPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or -not $taskDestination.StartsWith($taskRootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Preservation path escapes intended run.' }
    if ((Test-Path -LiteralPath (Join-Path $taskSource 'seal.json')) -or (Test-Path -LiteralPath $taskDestination)) { throw 'Completed source or existing destination must remain untouched.' }
    foreach ($taskArtifact in $taskEntry.files) {
        $taskActual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $taskSource $taskArtifact.name)).Hash.ToLowerInvariant()
        if ($taskActual -ne $taskArtifact.sha256) { throw 'Interrupted evidence changed before preservation.' }
    }
}
foreach ($taskEntry in $taskPlan.entries) {
    $taskParent = Split-Path -Parent $taskEntry.destination
    if (-not (Test-Path -LiteralPath $taskParent)) { [void](New-Item -ItemType Directory -Path $taskParent) }
    Move-Item -LiteralPath $taskEntry.source -Destination $taskEntry.destination
    foreach ($taskArtifact in $taskEntry.files) {
        $taskActual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $taskEntry.destination $taskArtifact.name)).Hash.ToLowerInvariant()
        if ($taskActual -ne $taskArtifact.sha256) { throw 'Preserved bytes mismatch.' }
    }
}
$taskReceipt = @{status='PRESERVED_ALL_SIX_BYTE_IDENTICAL'; plan_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $taskPlanPath).Hash.ToLowerInvariant(); source_and_destination_within_run_verified=$true; complete_artifacts_moved=0; scientific_method_changed=$false; recorded_utc=[DateTime]::UtcNow.ToString('o')}
[System.IO.File]::WriteAllText($taskReceiptPath, ($taskReceipt | ConvertTo-Json -Depth 8), [System.Text.UTF8Encoding]::new($false))
& 'D:\Project\flash-ticket-rca-research\.venv\Scripts\python.exe' -B 'D:\Project\flash-ticket-rca-research\results\task-e\resume_rcd_041_remaining.py'
exit $LASTEXITCODE
