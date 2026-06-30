param(
    [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $ProjectRoot ".conda\gmap\python.exe"
$CondaLibraryBin = Join-Path $ProjectRoot ".conda\gmap\Library\bin"
$SpecFile = Join-Path $ProjectRoot "GoogleMaps_LeadForge.spec"
$DistDir = Join-Path $ProjectRoot "dist"
$PackageName = "GoogleMaps_LeadForge-v$Version-windows-x64"
$PackageDir = Join-Path $DistDir $PackageName
$BuildOutputDir = Join-Path $DistDir "GoogleMaps_LeadForge"
$ZipPath = Join-Path $DistDir "$PackageName.zip"

if (-not (Test-Path $Python)) {
    throw "未找到项目本地 Python 环境：$Python"
}

Push-Location $ProjectRoot
try {
    & $Python -m PyInstaller --clean --noconfirm $SpecFile
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller 打包失败，退出码：$LASTEXITCODE"
    }

    foreach ($dllName in @("libcrypto-3-x64.dll", "libssl-3-x64.dll")) {
        $sourceDll = Join-Path $CondaLibraryBin $dllName
        if (-not (Test-Path $sourceDll)) {
            throw "未找到 Conda OpenSSL 运行库：$sourceDll"
        }
        Copy-Item -Path $sourceDll -Destination (Join-Path $BuildOutputDir "_internal") -Force
    }

    if (Test-Path $PackageDir) {
        Remove-Item -LiteralPath $PackageDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $PackageDir | Out-Null

    Copy-Item -Path (Join-Path $BuildOutputDir "*") -Destination $PackageDir -Recurse -Force
    Copy-Item -Path (Join-Path $ProjectRoot "config") -Destination $PackageDir -Recurse -Force

    foreach ($relativeDir in @("data", "exports", "logs", "drivers")) {
        New-Item -ItemType Directory -Path (Join-Path $PackageDir $relativeDir) -Force | Out-Null
    }
    New-Item -ItemType Directory -Path (Join-Path $PackageDir "drivers\selenium-cache") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $PackageDir "drivers\playwright-browsers") -Force | Out-Null
    foreach ($relativeDir in @("data", "exports", "logs", "drivers\selenium-cache", "drivers\playwright-browsers")) {
        New-Item -ItemType File -Path (Join-Path $PackageDir "$relativeDir\.gitkeep") -Force | Out-Null
    }

    Copy-Item -Path (Join-Path $ProjectRoot "README.md") -Destination $PackageDir -Force
    Copy-Item -Path (Join-Path $ProjectRoot "LICENSE") -Destination $PackageDir -Force
    Copy-Item -Path (Join-Path $ProjectRoot "CHANGELOG.md") -Destination $PackageDir -Force

    if (Test-Path $ZipPath) {
        Remove-Item -LiteralPath $ZipPath -Force
    }
    Compress-Archive -Path (Join-Path $PackageDir "*") -DestinationPath $ZipPath -Force

    Write-Host "发布目录：$PackageDir"
    Write-Host "发布压缩包：$ZipPath"
}
finally {
    Pop-Location
}
