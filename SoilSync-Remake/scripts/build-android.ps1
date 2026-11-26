param([string]$ApiBaseUrl = $env:VITE_API_BASE_URL, [switch]$Usb)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$frontendRoot = Join-Path $projectRoot 'frontend'
if (-not $Usb) {
    $apiUri = $null
    if (-not [Uri]::TryCreate($ApiBaseUrl, [UriKind]::Absolute, [ref]$apiUri) -or $apiUri.Scheme -ne 'https' -or $apiUri.IsLoopback -or $apiUri.UserInfo -or $apiUri.Query -or $apiUri.Fragment -or $apiUri.AbsolutePath -ne '/') {
        throw 'Pass -ApiBaseUrl https://your-hosted-soilsync-api (no credentials/path), or -Usb for laptop development.'
    }
}
if (-not $env:JAVA_HOME) {
    $bundledJdk = Join-Path $env:USERPROFILE '.jdks/jbr-21.0.11'
    if (Test-Path (Join-Path $bundledJdk 'bin/java.exe')) { $env:JAVA_HOME = $bundledJdk }
    else { throw 'Set JAVA_HOME to an installed Java 21 JDK.' }
}
$sdkRoot = $env:ANDROID_HOME
if (-not $sdkRoot) { $sdkRoot = Join-Path $env:LOCALAPPDATA 'Android/Sdk' }
if (-not (Test-Path (Join-Path $sdkRoot 'platforms/android-36'))) {
    throw 'Install Android SDK platform 36, or set ANDROID_HOME to its SDK folder.'
}
$sdkProperty = $sdkRoot.Replace('\', '/')
Set-Content -LiteralPath (Join-Path $frontendRoot 'android/local.properties') -Value "sdk.dir=$sdkProperty" -Encoding ascii
$configPath = Join-Path $frontendRoot 'capacitor.config.json'
$savedConfig = [IO.File]::ReadAllText($configPath)
$savedBaseUrl = $env:VITE_API_BASE_URL
Push-Location $frontendRoot
try {
    if ($Usb) {
        Copy-Item -LiteralPath (Join-Path $frontendRoot 'capacitor.usb.json') -Destination $configPath -Force
        $env:VITE_API_BASE_URL = ''
    }
    else { $env:VITE_API_BASE_URL = $ApiBaseUrl.TrimEnd('/') }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    & node node_modules/@capacitor/cli/bin/capacitor sync android
    if ($LASTEXITCODE -ne 0) { throw 'Capacitor sync failed.' }
    & ./android/gradlew.bat -p android :app:assembleDebug --console=plain
    if ($LASTEXITCODE -ne 0) { throw 'Android build failed.' }
    Write-Host 'APK: frontend/android/app/build/outputs/apk/debug/app-debug.apk'
}
finally {
    [IO.File]::WriteAllText($configPath, $savedConfig, [Text.UTF8Encoding]::new($false))
    $env:VITE_API_BASE_URL = $savedBaseUrl
    Pop-Location
}
