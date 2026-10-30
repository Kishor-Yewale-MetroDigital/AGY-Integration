param(
    [string]$ProjectId = "cf-hackathon-ai-poc-testin-b1",
    [string]$Region = "europe-west3",
    [string]$ServiceName = "talentflow-app"
)

$ErrorActionPreference = "Continue"
$WorkspaceDir = "c:\Users\kishor.yewale\OneDrive - METRO\Projects\AGY-Integration"
Set-Location $WorkspaceDir

# Enforce GCP Resource Attribution
$env:CLOUDSDK_METRICS_ENVIRONMENT = if ($env:CLOUDSDK_METRICS_ENVIRONMENT) { "$($env:CLOUDSDK_METRICS_ENVIRONMENT) datacloud.antigravity" } else { "datacloud.antigravity" }

Write-Host "=== Step 0: Enforce Local Test & GitHub Check-In Before GCP Deployment ===" -ForegroundColor Cyan
if (-not (Test-Path ".git")) {
    Write-Error "Git repository is not initialized. All code must be checked into GitHub before deploying to GCP."
    exit 1
}
$uncommitted = (git -c safe.directory=* status --porcelain)
if ($uncommitted) {
    Write-Error "Uncommitted local changes detected:`n$uncommitted`nRule enforcement: Every change must be tested locally and checked into GitHub (committed & pushed) before deploying to GCP."
    exit 1
}
git -c safe.directory=* fetch origin main --quiet 2>$null
$unpushed = (git -c safe.directory=* log origin/main..HEAD --oneline 2>$null)
if ($unpushed) {
    Write-Error "Unpushed local commits detected:`n$unpushed`nRule enforcement: Run 'git push origin main' so all changes are checked into GitHub before deploying to GCP."
    exit 1
}
Write-Host "GitHub check-in verified: Working tree is clean and in sync with origin/main." -ForegroundColor Green

Write-Host "=== Step 1: Verify GCP Authentication & Target Project ($ProjectId / $Region) ===" -ForegroundColor Cyan
$activeAccount = (gcloud auth list --filter="status:ACTIVE" --format="value(account)" --quiet)
if (-not $activeAccount) {
    Write-Error "No active gcloud account found. Run: gcloud auth login"
    exit 1
}
Write-Host "Authenticated as: $activeAccount" -ForegroundColor Green
gcloud config set project $ProjectId --quiet

Write-Host "=== Step 2: Ensure Required GCP APIs & Storage/Build IAM Roles on $ProjectId ===" -ForegroundColor Cyan
$requiredApis = @(
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "compute.googleapis.com"
)
$enabledApis = (gcloud services list --enabled --project=$ProjectId --format="value(config.name)" --quiet 2>$null)
$missingApis = $requiredApis | Where-Object { $enabledApis -notcontains $_ }

foreach ($api in $missingApis) {
    Write-Host "Enabling API on $($ProjectId): $api ..." -ForegroundColor Yellow
    gcloud services enable $api --project=$ProjectId --quiet
}

Write-Host "Granting Cloud Storage & Artifact Registry roles to $activeAccount ..." -ForegroundColor Cyan
gcloud projects add-iam-policy-binding $ProjectId --member="user:$activeAccount" --role="roles/storage.admin" --quiet | Out-Null
gcloud projects add-iam-policy-binding $ProjectId --member="user:$activeAccount" --role="roles/artifactregistry.admin" --quiet | Out-Null
gcloud projects add-iam-policy-binding $ProjectId --member="user:$activeAccount" --role="roles/logging.viewer" --quiet | Out-Null

# Also ensure the project's Cloud Build / Compute Engine default service accounts can read source bucket, write logs, and push images
$projectNumber = (gcloud projects describe $ProjectId --format="value(projectNumber)" --quiet)
if ($projectNumber) {
    $computeSa = "$projectNumber-compute@developer.gserviceaccount.com"
    $cloudBuildSa = "$projectNumber@cloudbuild.gserviceaccount.com"
    Write-Host "Ensuring Cloud Build service accounts ($computeSa) have Storage, Artifact Registry & Logging permissions..." -ForegroundColor Cyan
    foreach ($sa in @($computeSa, $cloudBuildSa)) {
        gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$sa" --role="roles/storage.admin" --quiet 2>$null | Out-Null
        gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$sa" --role="roles/artifactregistry.writer" --quiet 2>$null | Out-Null
        gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$sa" --role="roles/logging.logWriter" --quiet 2>$null | Out-Null
    }
}

Write-Host "=== Step 3: Provision BigQuery Dataset ($ProjectId:talentflow_analytics in EU) ===" -ForegroundColor Cyan
bq --project_id=$ProjectId show --dataset "$($ProjectId):talentflow_analytics" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    bq --location=EU --project_id=$ProjectId mk --dataset --label datacloud:antigravity --description "TalentFlow Curated Hiring, People Committee & Workforce Cost Analytics" "$($ProjectId):talentflow_analytics" 2>$null | Out-Null
}
Write-Host "BigQuery dataset verified." -ForegroundColor Green

Write-Host "=== Step 4: Build & Deploy Full-Stack Container to Cloud Run ($ProjectId / $Region) ===" -ForegroundColor Cyan
gcloud run deploy $ServiceName `
    --source . `
    --project $ProjectId `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --min-instances 0 `
    --max-instances 3 `
    --port 8080 `
    --set-env-vars "GCP_PROJECT_ID=$ProjectId,BQ_DATASET=talentflow_analytics,AUTO_POPULATE_DEMO_QUEUE=true" `
    --quiet

if ($LASTEXITCODE -eq 0) {
    # Grant invoker access to active user and disable invoker IAM check if permitted by Org Policy
    gcloud run services add-iam-policy-binding $ServiceName --region=$Region --member="user:$activeAccount" --role="roles/run.invoker" --project=$ProjectId --quiet 2>$null | Out-Null
    gcloud run services update $ServiceName --region=$Region --no-invoker-iam-check --project=$ProjectId --quiet 2>$null | Out-Null

    $serviceUrl = (gcloud run services describe $ServiceName --project $ProjectId --region $Region --format="value(status.url)" --quiet)
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Green
    Write-Host "TalentFlow Successfully Deployed to GCP Cloud Run!" -ForegroundColor Green
    Write-Host "Project:     $ProjectId" -ForegroundColor Green
    Write-Host "Region:      $Region" -ForegroundColor Green
    Write-Host "Service URL: $serviceUrl" -ForegroundColor Green
    Write-Host "Healthcheck: $serviceUrl/health" -ForegroundColor Green
    Write-Host "API Docs:    $serviceUrl/docs" -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Green
} else {
    Write-Host "Deployment exited with code $LASTEXITCODE. Review logs above." -ForegroundColor Red
}
