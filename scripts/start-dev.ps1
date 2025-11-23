<#
Start-dev.ps1 - Build and start CortAI with docker-compose, wait for services.
Usage: .\scripts\start-dev.ps1 [-NoBuild] [-TimeoutSeconds 300] [-FollowLogs]
#>

param(
  [switch]$NoBuild,
  [int]$TimeoutSeconds = 300,
  [switch]$FollowLogs
)

Set-StrictMode -Version Latest

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
Write-Host "Working directory: $PWD"

if (-not $NoBuild) {
  Write-Host "Building images..."
  docker-compose build
}

Write-Host "Starting services..."
docker-compose up -d

function Get-HealthStatus($containerName) {
  try {
    $fmt = '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}'
    $out = docker inspect --format $fmt $containerName 2>$null
    return $out.Trim()
  } catch {
    return $null
  }
}

$servicesToCheck = @(
  @{ name='cortai-postgres'; desired='healthy' },
  @{ name='cortai-redis'; desired='healthy' },
  @{ name='cortai-rabbitmq'; desired='healthy' }
)

$start = Get-Date
Write-Host "Waiting for services to become healthy (timeout: $TimeoutSeconds s)..."
$allOk = $false
while ((Get-Date) - $start).TotalSeconds -lt $TimeoutSeconds {
  $allOk = $true
  foreach ($s in $servicesToCheck) {
    $status = Get-HealthStatus $s.name
    if (-not $status) { $status = 'unknown' }
    Write-Host ("{0}: {1}" -f $s.name, $status)
    if ($status -ne $s.desired) { $allOk = $false }
  }

  $running = docker ps --filter "name=cortai-" --format "{{.Names}}" 2>$null
  if (-not $running) { Write-Host "No cortai containers running yet..." ; $allOk = $false }

  if ($allOk) { break }
  Start-Sleep -Seconds 3
}

if (-not $allOk) {
  Write-Warning "Timeout waiting for services to be healthy. Showing status and last logs..."
  docker-compose ps
  docker-compose logs --tail=200
  exit 1
}

Write-Host "All required services healthy."
docker-compose ps

if ($FollowLogs) {
  Write-Host "Tailing backend logs. Press Ctrl+C to exit."
  docker-compose logs -f backend
} else {
  $ans = Read-Host "Deseja acompanhar os logs do backend agora? (Y/n)"
  if ($ans -eq '' -or $ans -match '^[Yy]') {
    docker-compose logs -f backend
  } else {
    Write-Host "Pronto. Para ver logs depois: docker-compose logs -f backend"
  }
}
