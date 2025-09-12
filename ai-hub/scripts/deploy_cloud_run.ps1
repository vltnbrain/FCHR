param(
  [Parameter(Mandatory = $true)] [string] $Project,
  [Parameter(Mandatory = $true)] [string] $Region,
  [string] $ServiceName = "aihub-backend",
  [string] $RepoName = "aihub",
  [string] $ImageTag = "latest",
  [string] $EnvFile = "ai-hub/infra/cloudrun.env.example.yaml",
  [switch] $AllowUnauthenticated
)

function Fail($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
  Fail "gcloud CLI not found. Install Google Cloud SDK and re-run."
}

Write-Host "Setting gcloud project/region..." -ForegroundColor Cyan
gcloud config set project $Project 1>$null
if ($LASTEXITCODE -ne 0) { Fail "Failed to set project $Project" }
gcloud config set run/region $Region 1>$null
if ($LASTEXITCODE -ne 0) { Fail "Failed to set region $Region" }

$ImageUri = "$Region-docker.pkg.dev/$Project/$RepoName/$ServiceName:$ImageTag"

Write-Host "Ensuring Artifact Registry repo '$RepoName' exists in $Region..." -ForegroundColor Cyan
$null = & gcloud artifacts repositories describe $RepoName --location=$Region 2>$null
if ($LASTEXITCODE -ne 0) {
  & gcloud artifacts repositories create $RepoName --repository-format=docker --location=$Region --description="AI Hub containers"
  if ($LASTEXITCODE -ne 0) { Fail "Failed to create Artifact Registry repo $RepoName" }
}

Write-Host "Building image with Cloud Build: $ImageUri" -ForegroundColor Cyan
& gcloud builds submit "ai-hub/backend" --tag $ImageUri
if ($LASTEXITCODE -ne 0) { Fail "Cloud Build failed" }

Write-Host "Deploying to Cloud Run service '$ServiceName' in $Region..." -ForegroundColor Cyan
$deployArgs = @('run','deploy', $ServiceName,
  '--image', $ImageUri,
  '--region', $Region,
  '--platform', 'managed',
  '--port', '8080'
)
if ($AllowUnauthenticated) { $deployArgs += '--allow-unauthenticated' }
if (Test-Path $EnvFile) { $deployArgs += @('--env-vars-file', $EnvFile) }

& gcloud @deployArgs
if ($LASTEXITCODE -ne 0) { Fail "Cloud Run deploy failed" }

$url = & gcloud run services describe $ServiceName --region $Region --format='value(status.url)'
Write-Host "Deployed successfully: $url" -ForegroundColor Green

Write-Host "Note: Ensure DATABASE_URI points to a reachable Postgres (e.g., Cloud SQL) and Redis is configured (e.g., Memorystore) if background tasks are required." -ForegroundColor Yellow

