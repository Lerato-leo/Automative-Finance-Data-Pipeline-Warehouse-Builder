$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "[Phase 7] Applying admin schema and optimization..."
python db_admin.py optimize

Write-Host "[Phase 7] Running health snapshot..."
python db_health_monitor.py snapshot

Write-Host "[Phase 7] Running daily backup..."
python backup_recovery.py backup --retention-days 14

Write-Host "[Phase 7] Testing restore procedure..."
python backup_recovery.py restore-test

Write-Host "[Phase 7] Capturing PITR readiness..."
python backup_recovery.py pitr-check

Write-Host "[Phase 7] Completed"
