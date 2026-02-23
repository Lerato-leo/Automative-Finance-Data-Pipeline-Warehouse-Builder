# PowerShell Notification Script for Slack, Teams, Email
param(
    [string]$Status,
    [string]$Message
)

# Load config from script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $scriptDir 'notification_config_example.txt'
$config = Get-Content $configPath | Where-Object {$_ -match "="}
foreach ($line in $config) {
    $parts = $line -split "="
    Set-Variable -Name $parts[0].Trim() -Value $parts[1].Trim()
}



# Teams notification
if ($TEAMS_WEBHOOK) {
    $payload = @{text = "[$Status] $Message"} | ConvertTo-Json
    Invoke-RestMethod -Uri $TEAMS_WEBHOOK -Method Post -Body $payload -ContentType 'application/json'
}

# Email notification
if ($EMAIL_TO) {
    Send-MailMessage -From $EMAIL_FROM -To $EMAIL_TO -Subject "Phase 3 Ingestion [$Status]" -Body $Message -SmtpServer $SMTP_SERVER -Port $SMTP_PORT -Credential (New-Object System.Management.Automation.PSCredential($SMTP_USER,(ConvertTo-SecureString $SMTP_PASS -AsPlainText -Force))) -UseSsl
}
