while ($true) {
    $containers = docker ps --format '{{.Names}} {{.Status}}'
    foreach ($line in $containers) {
        if ($line -match 'Exited' -or $line -match 'Paused') {
            $name = $line.Split(' ')[0]
            Write-Host "Restarting $name... ()" -ForegroundColor Yellow
            docker restart $name
        }
    }
    Start-Sleep -Seconds 60
}
