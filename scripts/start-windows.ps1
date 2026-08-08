# Build and start the Prelegal app container (Windows).
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ImageName = "prelegal-app"
$ContainerName = "prelegal-app"
$Port = 8000

Set-Location $RepoRoot

if (-not (Test-Path ".env")) {
    Write-Warning ".env not found at repo root. Copy .env.example to .env and fill in secrets before starting."
}

Write-Host "Building Docker image ($ImageName)..."
docker build -t $ImageName .
if ($LASTEXITCODE -ne 0) { throw "docker build failed" }

$existing = docker ps -aq -f "name=^$ContainerName`$"
if ($existing) {
    Write-Host "Removing existing container ($ContainerName)..."
    docker rm -f $ContainerName | Out-Null
}

Write-Host "Starting container ($ContainerName) on port $Port..."
docker run -d `
    --name $ContainerName `
    --env-file .env `
    -p "${Port}:8000" `
    $ImageName | Out-Null
if ($LASTEXITCODE -ne 0) { throw "docker run failed" }

Write-Host "Prelegal backend available at http://localhost:$Port"
