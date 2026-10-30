param(
    [string]$ProjectId = "cf-hackathon-ai-poc-testin-b1",
    [string]$Region = "europe-west3",
    [string]$ServiceName = "talentflow-app",
    [int]$ProxyPort = 8085
)

$ErrorActionPreference = "Continue"
$env:CLOUDSDK_METRICS_ENVIRONMENT = if ($env:CLOUDSDK_METRICS_ENVIRONMENT) { "$($env:CLOUDSDK_METRICS_ENVIRONMENT) datacloud.antigravity" } else { "datacloud.antigravity" }

$activeAccount = (gcloud auth list --filter="status:ACTIVE" --format="value(account)" --quiet)
$serviceUrl = (gcloud run services describe $ServiceName --project $ProjectId --region $Region --format="value(status.url)" --quiet)

Write-Host "=== Step 1: Grant Cloud Run Invoker Role ($activeAccount) ===" -ForegroundColor Cyan
gcloud run services add-iam-policy-binding $ServiceName `
    --region=$Region `
    --member="user:$activeAccount" `
    --role="roles/run.invoker" `
    --project=$ProjectId `
    --quiet

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "METRO Org Policy requires IAM-authenticated Cloud Run access." -ForegroundColor Yellow
Write-Host "Starting Authenticated Cloud Run Proxy -> $serviceUrl" -ForegroundColor Green
Write-Host "Browser URL: http://127.0.0.1:$ProxyPort" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green

Start-Job -ScriptBlock {
    Start-Sleep -Seconds 4
    Start-Process "http://127.0.0.1:$using:ProxyPort"
} | Out-Null

gcloud run services proxy $ServiceName --region=$Region --project=$ProjectId --port=$ProxyPort
