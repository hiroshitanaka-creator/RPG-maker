$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$engineRoot = Join-Path $repoRoot '.tools\godot\4.7.2'
$archivePath = Join-Path $engineRoot 'Godot_v4.7.2-stable_win64.exe.zip'
$enginePath = Join-Path $engineRoot 'Godot_v4.7.2-stable_win64_console.exe'
$expectedHash = '731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953'
$downloadUrl = 'https://github.com/godotengine/godot-builds/releases/download/4.7.2-stable/Godot_v4.7.2-stable_win64.exe.zip'

$null = New-Item -ItemType Directory -Path $engineRoot -Force
if (-not (Test-Path -LiteralPath $archivePath)) {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $archivePath -TimeoutSec 300
}
if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
    throw 'GodotのZIPが公式配布のSHA-256と一致しません。展開・起動は行いません。'
}
if (-not (Test-Path -LiteralPath $enginePath)) {
    Expand-Archive -LiteralPath $archivePath -DestinationPath $engineRoot
}
$portableMarker = Join-Path $engineRoot '_sc_'
if (-not (Test-Path -LiteralPath $portableMarker)) {
    $null = New-Item -ItemType File -Path $portableMarker
}
$actualVersion = & $enginePath --version
if ($LASTEXITCODE -ne 0 -or $actualVersion -notmatch '^4\.7\.2\.stable\.') {
    throw ('Godotのバージョンが固定条件と一致しません: ' + $actualVersion)
}
Write-Output $actualVersion
Write-Output ('Godot: ' + $enginePath)
