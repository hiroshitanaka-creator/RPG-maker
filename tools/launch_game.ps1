param([switch]$HumanPlaytest)
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$engineDirectory = Join-Path $repoRoot '.tools\godot\4.7.2'
$consoleEngine = Join-Path $engineDirectory 'Godot_v4.7.2-stable_win64_console.exe'
$windowEngine = Join-Path $engineDirectory 'Godot_v4.7.2-stable_win64.exe'
if (-not (Test-Path -LiteralPath $consoleEngine)) {
    & (Join-Path $PSScriptRoot 'get_godot.ps1')
}
$version = & $consoleEngine --version
if ($LASTEXITCODE -ne 0 -or $version -notmatch '^4\.7\.2\.stable\.') {
    throw 'Godot 4.7.2-stableが必要です。'
}
$importLog = & $consoleEngine --headless --path $repoRoot --import 2>&1
if ($LASTEXITCODE -ne 0 -or ($importLog -join "`n") -match '(?m)^(SCRIPT ERROR|ERROR:|WARNING:)') {
    $importLog | Write-Output
    throw 'インポート検査に失敗したため起動しません。'
}
# このスクリプトは利用者が操作するゲーム画面を開く。
$gameArguments = @('--path', ('"' + $repoRoot + '"'))
if ($HumanPlaytest) { $gameArguments += @('--', '--human-playtest') }
Start-Process -FilePath $windowEngine -ArgumentList $gameArguments -WorkingDirectory $repoRoot -WindowStyle Normal
