# =============================================================================
# SaleHSaaS - Windows Task Scheduler Manager
# Creates/removes/checks scheduled tasks for routine legal pipeline jobs.
# =============================================================================

param(
    [ValidateSet("install", "remove", "status")]
    [string]$Action = "install",

    [string]$DailyHealthTime = "08:00",
    [string]$WeeklyDiscoverTime = "03:00",

    [ValidateSet("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")]
    [string]$WeeklyDiscoverDay = "Monday"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\.." )).Path
$RunnerScript = Join-Path $ProjectRoot "scripts\windows\RUN_SALEH_PIPELINES_UTF8.ps1"

$TaskHealthName = "SaleH-Pipelines-Health-Daily"
$TaskDiscoverName = "SaleH-Pipelines-Discover-Weekly"

function Write-Info([string]$msg) {
    Write-Host $msg -ForegroundColor Cyan
}

function Write-Ok([string]$msg) {
    Write-Host $msg -ForegroundColor Green
}

function Write-Warn([string]$msg) {
    Write-Host $msg -ForegroundColor Yellow
}

function Write-Err([string]$msg) {
    Write-Host $msg -ForegroundColor Red
}

function New-RunnerAction([string]$taskKey) {
    if (-not (Test-Path $RunnerScript)) {
        throw "Runner script not found: $RunnerScript"
    }

    $runnerCliText = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -Task {1}' -f $RunnerScript, $taskKey
    return New-ScheduledTaskAction -Execute "powershell.exe" -Argument $runnerCliText -WorkingDirectory $ProjectRoot
}

function Register-OrUpdateTask(
    [string]$TaskName,
    [Microsoft.Management.Infrastructure.CimInstance]$Trigger,
    [Microsoft.Management.Infrastructure.CimInstance]$Action
) {
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

    Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Principal $principal -Settings $settings -Force | Out-Null
}

function Remove-TaskIfExists([string]$TaskName) {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Ok "Removed: $TaskName"
    } else {
        Write-Warn "Not found: $TaskName"
    }
}

function Show-Status {
    $tasks = Get-ScheduledTask -TaskName "SaleH-Pipelines-*" -ErrorAction SilentlyContinue
    if (-not $tasks) {
        Write-Warn "No SaleH scheduled tasks found."
        return
    }

    $tasks |
        Select-Object TaskName, State, @{N="NextRunTime";E={ (Get-ScheduledTaskInfo -TaskName $_.TaskName).NextRunTime }} |
        Format-Table -AutoSize
}

switch ($Action) {
    "install" {
        Write-Info "Installing scheduled tasks..."

        $healthTrigger = New-ScheduledTaskTrigger -Daily -At $DailyHealthTime
        $healthAction = New-RunnerAction -taskArg "health"
        Register-OrUpdateTask -TaskName $TaskHealthName -Trigger $healthTrigger -Action $healthAction
        Write-Ok "Installed/Updated: $TaskHealthName (Daily at $DailyHealthTime)"

        $discoverTrigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek $WeeklyDiscoverDay -At $WeeklyDiscoverTime
        $discoverAction = New-RunnerAction -taskArg "discover"
        Register-OrUpdateTask -TaskName $TaskDiscoverName -Trigger $discoverTrigger -Action $discoverAction
        Write-Ok "Installed/Updated: $TaskDiscoverName (Weekly $WeeklyDiscoverDay at $WeeklyDiscoverTime)"

        Write-Host ""
        Show-Status
    }

    "remove" {
        Write-Info "Removing SaleH scheduled tasks..."
        Remove-TaskIfExists -TaskName $TaskHealthName
        Remove-TaskIfExists -TaskName $TaskDiscoverName
    }

    "status" {
        Show-Status
    }
}
