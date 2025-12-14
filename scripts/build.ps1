# Build Script for ArteCore Desktop (ArcVision)

param(
    [string]$Version = $null
)

# 1. Determine Version
if ([string]::IsNullOrWhiteSpace($Version)) {
    # Fallback: Generate Calendar Version (CalVer) with Time to prevent conflicts
    Write-Host "No version provided, generating CalVer..." -ForegroundColor Yellow
    $Date = Get-Date

    # Calculate numeric values to fit MSI constraints (Major <= 255, Minor <= 255, Build <= 65535)
    # Major: Year - 2000 (e.g., 25 for 2025)
    # Minor: Month (e.g., 12)
    # Patch: Total minutes in the current month (Day * 1440 + Hour * 60 + Minute)
    # Max Patch: 31 * 1440 + 23 * 60 + 59 = 44640 + 1380 + 59 ~ 46079 < 65535

    $Major = $Date.Year - 2000
    $Minor = $Date.Month
    $Patch = ($Date.Day * 1440) + ($Date.Hour * 60) + $Date.Minute

    $Version = "$Major.$Minor.$Patch"
}

$TauriConfigPath = "src/ArcVision/src-tauri/tauri.conf.json"

# Update Tauri Config
$TauriConfigJson = Get-Content $TauriConfigPath -Raw | ConvertFrom-Json
$TauriConfigJson.version = $Version
$TauriConfigJson | ConvertTo-Json -Depth 10 | Set-Content $TauriConfigPath

$ProductName = $TauriConfigJson.productName

Write-Host "Set Version to $Version" -ForegroundColor Cyan
Write-Host "Building $ProductName v$Version..." -ForegroundColor Cyan

# Export version to GitHub Env if available
if ($env:GITHUB_ENV) {
    "BUILD_VERSION=$Version" | Out-File -FilePath $env:GITHUB_ENV -Append -Encoding utf8
}

# 2. Build Sidecar
Write-Host "Rebuilding Sidecar..." -ForegroundColor Cyan
uv run python scripts/build_sidecar.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Sidecar build failed!"
    exit $LASTEXITCODE
}

# 3. Build Tauri App
Push-Location src/ArcVision

Write-Host "Building Tauri App..." -ForegroundColor Cyan
if (!(Test-Path node_modules)) {
    Write-Host "Installing NPM dependencies..." -ForegroundColor Yellow
    npm install
}

npm run tauri build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Tauri build failed!"
    Pop-Location
    exit $LASTEXITCODE
}

Pop-Location

# 4. Bundle Output
$OutputDir = "build/v$Version"
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}

# Define source paths for NSIS and MSI (adjust based on actual output)
$TargetDir = "src/ArcVision/src-tauri/target/release/bundle"

# Copy NSIS installer
$NsisSource = "$TargetDir/nsis/*.exe"
if (Test-Path $NsisSource) {
    Copy-Item $NsisSource -Destination $OutputDir -Force
    Write-Host "Copied NSIS installer to $OutputDir" -ForegroundColor Green
}

# Copy MSI installer
$MsiSource = "$TargetDir/msi/*.msi"
if (Test-Path $MsiSource) {
    Copy-Item $MsiSource -Destination $OutputDir -Force
    Write-Host "Copied MSI installer to $OutputDir" -ForegroundColor Green
}

Write-Host "Build Complete! Artifacts in $OutputDir" -ForegroundColor Green
