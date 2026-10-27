$ErrorActionPreference = "SilentlyContinue"

function Test-Url {
    param(
        [string]$Url,
        [int]$Attempts = 12,
        [int]$DelaySeconds = 2
    )

    for ($i = 1; $i -le $Attempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            return $response.StatusCode
        } catch {
            Start-Sleep -Seconds $DelaySeconds
        }
    }

    return $null
}

Write-Host ""
Write-Host "Verifying demo services..."
Write-Host ""

$backendStatus = Test-Url -Url "http://127.0.0.1:5000/api/v1/health"
$frontendStatus = Test-Url -Url "http://127.0.0.1:3000/"

if ($backendStatus) {
    Write-Host "Backend: http://127.0.0.1:5000/api/v1/health -> $backendStatus"
} else {
    Write-Host "Backend: not reachable yet"
}

if ($frontendStatus) {
    Write-Host "Frontend: http://127.0.0.1:3000/ -> $frontendStatus"
} else {
    Write-Host "Frontend: not reachable yet"
}

Write-Host ""
Write-Host "Demo routes to try:"
Write-Host "  http://127.0.0.1:3000/research"
Write-Host "  http://127.0.0.1:3000/credit-officer"
Write-Host "  http://127.0.0.1:3000/risk-scoring"
Write-Host "  http://127.0.0.1:3000/cam-generator"
