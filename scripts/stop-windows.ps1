# Stop and remove the Prelegal app container (Windows).
$ErrorActionPreference = "Stop"

$ContainerName = "prelegal-app"

$existing = docker ps -aq -f "name=^$ContainerName`$"
if ($existing) {
    Write-Host "Stopping and removing container ($ContainerName)..."
    docker rm -f $ContainerName | Out-Null
    Write-Host "Stopped."
} else {
    Write-Host "Container ($ContainerName) is not running."
}
