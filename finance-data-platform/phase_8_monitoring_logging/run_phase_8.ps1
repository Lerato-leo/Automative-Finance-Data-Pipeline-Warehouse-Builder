$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "[Phase 8] Applying monitoring schema and dashboard views..."
python monitoring_collector.py setup

Write-Host "[Phase 8] Collecting monitoring metrics..."
python monitoring_collector.py collect-all --days-back 7

Write-Host "[Phase 8] Running alert checks..."
python alert_manager.py run-alerts --failure-rate-threshold 95 --p95-threshold-seconds 300

Write-Host "[Phase 8] Completed"
