$ErrorActionPreference = 'Stop'
# Official Eclipse Temurin portable runtime; no global PATH or registry changes.
$javaDir = Join-Path $PSScriptRoot '../backend/.runtime/java'
New-Item -ItemType Directory -Path $javaDir -Force | Out-Null
$release = Invoke-RestMethod 'https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture=x64&image_type=jre&os=windows&vendor=eclipse'
$asset = $release[0].binary.package
$archive = Join-Path $javaDir 'temurin-jre.zip'
curl.exe -sSL --fail --max-time 180 --output $archive $asset.link
if ($LASTEXITCODE -ne 0) { throw 'Java download failed; retry or install Java 21 from adoptium.net' }
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $asset.checksum) { throw 'Java download checksum mismatch' }
Expand-Archive -LiteralPath $archive -DestinationPath $javaDir -Force
Write-Host 'Portable Java installed in backend/.runtime/java. Firebase will use it for this project only.'
