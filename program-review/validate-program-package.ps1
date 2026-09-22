[CmdletBinding()]
param(
    [string]$PlatformRoot = 'D:/Project/flash-ticket-platform',
    [string]$ResearchRoot = 'D:/Project/flash-ticket-rca-research'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$utf8 = [System.Text.UTF8Encoding]::new($false, $true)
$failures = [System.Collections.Generic.List[string]]::new()
$rcaDocs = Join-Path $PlatformRoot 'docs/research-rca'
$reviewRoot = Join-Path $ResearchRoot 'program-review'
$baseline = Get-Content -LiteralPath (Join-Path $reviewRoot 'pre-change-inventory.json') -Raw | ConvertFrom-Json
$canonicalNames = @(
    'RESEARCH-DECISIONS.md', 'task-c-research-decision-lock.md',
    'MASTER-RESEARCH-PROGRAM.md', 'CURRENT-STATE.md', 'ARTIFACT-MAP.md',
    'SESSION-BOOTSTRAP.md', 'task-b-dataset-capability-summary.md'
)
$packagePaths = @($canonicalNames | ForEach-Object { Join-Path $rcaDocs $_ }) + @(
    (Join-Path $rcaDocs 'README.md'),
    (Join-Path $rcaDocs 'R0-boi-canh-va-rang-buoc.md'),
    (Join-Path $rcaDocs 'task-c-independent-research-shortlist.md'),
    (Join-Path $PlatformRoot 'docs/project/decision-register.md'),
    (Join-Path $PlatformRoot 'docs/quy-trinh-lam-viec.md'),
    (Join-Path $PlatformRoot 'docs/report/report-outline.md'),
    (Join-Path $ResearchRoot 'README.md'),
    (Join-Path $ResearchRoot 'task-c/task-c-resume-state.md'),
    (Join-Path $reviewRoot 'independent-workflow-review.md')
)
$permittedChanges = @(
    (Join-Path $rcaDocs 'README.md'),
    (Join-Path $rcaDocs 'R0-boi-canh-va-rang-buoc.md'),
    (Join-Path $rcaDocs 'task-c-independent-research-shortlist.md'),
    (Join-Path $PlatformRoot 'docs/project/decision-register.md'),
    (Join-Path $PlatformRoot 'docs/quy-trinh-lam-viec.md'),
    (Join-Path $PlatformRoot 'docs/report/report-outline.md'),
    (Join-Path $ResearchRoot 'task-c/task-c-resume-state.md')
) | ForEach-Object { [System.IO.Path]::GetFullPath($_) }

function Get-StringHash([string]$Text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return [Convert]::ToHexString($sha.ComputeHash($utf8.GetBytes($Text))) }
    finally { $sha.Dispose() }
}

function Test-RestoredText([string]$Text, [string]$ExpectedHash) {
    $lf = $Text.Replace("`r`n", "`n")
    $variants = [ordered]@{ AsRead = $Text; LF = $lf; CRLF = $lf.Replace("`n", "`r`n") }
    foreach ($entry in $variants.GetEnumerator()) {
        if ((Get-StringHash $entry.Value) -eq $ExpectedHash) { return $entry.Key }
    }
    return 'NO_MATCH'
}

$fileResults = @()
$linkCount = 0
$remoteLinksSkipped = 0
$textByPath = @{}
foreach ($path in $packagePaths) {
    $path = [System.IO.Path]::GetFullPath($path)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $failures.Add("Missing package file: $path")
        continue
    }
    $bytes = [System.IO.File]::ReadAllBytes($path)
    try { $body = $utf8.GetString($bytes) }
    catch { $failures.Add("Invalid UTF-8: $path"); continue }
    if ($body.Contains([char]0) -or $body.Contains([char]0xFFFD)) {
        $failures.Add("NUL or replacement character: $path")
    }
    $textByPath[$path] = $body
    foreach ($match in [regex]::Matches($body, '(?<!!)\[[^\]\r\n]+\]\((?<target><[^>\r\n]+>|[^)\r\n]+)\)')) {
        $target = $match.Groups['target'].Value.Trim().Trim('<', '>')
        if ($target -match '^(https?://|mailto:|app://|codex://)') { $remoteLinksSkipped++; continue }
        if ($target.StartsWith('#')) { continue }
        $target = [Uri]::UnescapeDataString(($target -split '#', 2)[0])
        if (-not $target) { continue }
        $resolved = if ([System.IO.Path]::IsPathRooted($target)) {
            [System.IO.Path]::GetFullPath($target)
        } else { [System.IO.Path]::GetFullPath((Join-Path (Split-Path $path -Parent) $target)) }
        $linkCount++
        if (-not (Test-Path -LiteralPath $resolved)) {
            $failures.Add("Broken local Markdown link: $path -> $target")
        }
    }
    $fileResults += [ordered]@{
        path = $path; bytes = $bytes.Length
        sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    }
}

$preservation = @()
foreach ($old in $baseline.files) {
    $path = [System.IO.Path]::GetFullPath($old.path)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $failures.Add("Baseline artifact missing: $path")
        continue
    }
    $currentHash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    $same = $currentHash -eq $old.sha256
    $allowed = $path -in $permittedChanges
    if (-not $same -and -not $allowed) { $failures.Add("Unexpected baseline change: $path") }
    $preservation += [ordered]@{
        path = $path; previous_sha256 = $old.sha256; current_sha256 = $currentHash
        status = $(if ($same) { 'UNCHANGED' } elseif ($allowed) { 'AUTHORIZED_DOCUMENT_UPDATE' } else { 'UNEXPECTED_CHANGE' })
    }
}

$phase1Path = [System.IO.Path]::GetFullPath((Join-Path $rcaDocs 'task-c-independent-research-shortlist.md'))
$phase1 = $textByPath[$phase1Path]
$noticePattern = '(?m)^> \*\*CURRENT DECISION — 2026-09-22:.*\r?\n\r?\n'
$restoredPhase1 = [regex]::Replace($phase1, $noticePattern, '')
$phase1Old = @($baseline.files | Where-Object { $_.path -eq $phase1Path })[0]
$phase1Restoration = Test-RestoredText $restoredPhase1 $phase1Old.sha256
if ($phase1Restoration -eq 'NO_MATCH') { $failures.Add('Phase 1 historical body failed original-hash reconstruction') }

$resumePath = [System.IO.Path]::GetFullPath((Join-Path $ResearchRoot 'task-c/task-c-resume-state.md'))
$resume = $textByPath[$resumePath]
$oldStart = $resume.IndexOf('## Completion 2026-09-21 — CURRENT AUTHORITY')
$restoredResume = "# Task C resume state`n`n" + $resume.Substring($oldStart)
$resumeOld = @($baseline.files | Where-Object { $_.path -eq $resumePath })[0]
$resumeRestoration = Test-RestoredText $restoredResume $resumeOld.sha256
if ($resumeRestoration -eq 'NO_MATCH') { $failures.Add('Resume historical body failed original-hash reconstruction') }

$reviewPath = Join-Path $reviewRoot 'independent-workflow-review.md'
$reviewBytes = [System.IO.File]::ReadAllBytes($reviewPath)
$shaPrefix = [System.Security.Cryptography.SHA256]::Create()
try { $step1Hash = [Convert]::ToHexString($shaPrefix.ComputeHash($reviewBytes, 0, 30673)) }
finally { $shaPrefix.Dispose() }
if ($step1Hash -ne '080F92C12E8CD8B5D5E3648C5EBC82E81A3D7FADEE16F8AB547D9E3B30E065BC') {
    $failures.Add('Independent STEP 1 prefix changed')
}

$master = $textByPath[[System.IO.Path]::GetFullPath((Join-Path $rcaDocs 'MASTER-RESEARCH-PROGRAM.md'))]
$tasks = [regex]::Matches($master, '(?m)^### Task ([A-K]) —') | ForEach-Object { $_.Groups[1].Value }
if (($tasks -join ',') -ne 'A,B,C,D,E,F,G,H,I,J,K') { $failures.Add('Task A-K contract headings incomplete or duplicated') }
$contractRows = @('Purpose / RQ', 'Inputs / dependencies', 'Outputs / artifacts', 'Mandatory / entry', 'Exit', 'Scientific checks', 'Reproducibility / evidence', 'Out of scope', 'Fallback', 'Models / scripts / review', 'Next handoff')
foreach ($row in $contractRows) {
    $count = [regex]::Matches($master, '(?m)^\| ' + [regex]::Escape($row) + ' \|').Count
    if ($count -ne 11) { $failures.Add("Contract row count $row : $count instead of 11") }
}
$decisions = $textByPath[[System.IO.Path]::GetFullPath((Join-Path $rcaDocs 'RESEARCH-DECISIONS.md'))]
$decisionIds = [regex]::Matches($decisions, '(?m)^\| (RCA-\d{3}) \|') | ForEach-Object { $_.Groups[1].Value }
if ($decisionIds.Count -ne 17 -or @($decisionIds | Select-Object -Unique).Count -ne 17) {
    $failures.Add('Decision IDs incomplete or duplicated')
}
$state = $textByPath[[System.IO.Path]::GetFullPath((Join-Path $rcaDocs 'CURRENT-STATE.md'))]
$lock = $textByPath[[System.IO.Path]::GetFullPath((Join-Path $rcaDocs 'task-c-research-decision-lock.md'))]
if (-not $state.Contains('TASK C PHASE 2: COMPLETE') -or -not $state.Contains('chờ lệnh bắt đầu D') -or -not $lock.Contains('NOT STARTED')) {
    $failures.Add('Current continuation/authorization boundary inconsistent')
}
if ($lock.Contains('C2-lock-v1')) { $failures.Add('Ambiguous C2 version alias remains') }

$result = [ordered]@{
    checked_at = [DateTimeOffset]::Now.ToString('o')
    status = $(if ($failures.Count -eq 0) { 'PASS' } else { 'FAIL' })
    scope = 'Documentation package only. No raw corpus rehash, experiment, installation, download, or approval of future methods.'
    validator = [ordered]@{ path = $PSCommandPath; sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash }
    files = $fileResults
    checks = [ordered]@{
        strict_utf8_files = $fileResults.Count; local_markdown_links = $linkCount
        remote_urls_not_refetched = $remoteLinksSkipped
        link_limit = 'Local Markdown destinations only; labels mentioning sections are not machine-validated anchors. Future inline-code output paths are contracts, not existing-file claims.'
        baseline_files = $baseline.files.Count
        unchanged = @($preservation | Where-Object status -eq 'UNCHANGED').Count
        authorized_updates = @($preservation | Where-Object status -eq 'AUTHORIZED_DOCUMENT_UPDATE').Count
        phase1_original_hash_reconstruction = $phase1Restoration
        resume_original_hash_reconstruction = $resumeRestoration
        independent_step1_prefix_sha256 = $step1Hash
        task_contracts = $tasks; decision_ids = $decisionIds
        algorithmic_validation_limit = 'Structure, identity and navigation checks do not prove methodological validity; independent review and main adjudication are separate evidence.'
    }
    preservation = $preservation
    failures = @($failures)
}
$result | ConvertTo-Json -Depth 9
if ($failures.Count -gt 0) { exit 1 }
