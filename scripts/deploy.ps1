param(
  [string]$RepoDir = "$HOME/FCHR"
)

Set-Location $RepoDir
Write-Host "Pulling latest..."
git pull --ff-only | Out-Null

if (!(Test-Path .env)) {
  Copy-Item .env.example .env
  $secret = -join ((48..57 + 97..102) | Get-Random -Count 64 | ForEach-Object {[char]$_})
  Add-Content .env "SECRET_KEY=$secret"
}

Write-Host "Bringing up stack..."
docker compose -f infra/prod/docker-compose.yml up -d --build | Out-Null

Write-Host "Health:"
try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 -Uri 'http://localhost/healthz').Content } catch { Write-Host "healthz failed" }

