$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$binPath = Join-Path $repoRoot '.tools\bin'
$enginePath = Join-Path $repoRoot '.tools\godot\4.7.2\Godot_v4.7.2-stable_win64_console.exe'
if (-not (Test-Path -LiteralPath $enginePath)) {
    throw '先に tools/get_godot.ps1 を実行してください。'
}
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$pythonPath = if ($pythonCommand) { $pythonCommand.Source } else {
    Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
}
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Pythonが見つかりません。Pythonの実行ファイルをPATHへ追加してください。'
}
$null = New-Item -ItemType Directory -Path $binPath -Force
$utf8 = [System.Text.UTF8Encoding]::new($false)
$cmdShim = '@echo off' + "`r`n" + '@"%~dp0..\godot\4.7.2\Godot_v4.7.2-stable_win64_console.exe" %*' + "`r`n"
[System.IO.File]::WriteAllText((Join-Path $binPath 'godot.cmd'), $cmdShim, $utf8)
$shellShim = '#!/usr/bin/env bash' + "`n" + 'exec "' + $pythonPath.Replace('\', '/') + '" "$@"' + "`n"
[System.IO.File]::WriteAllText((Join-Path $binPath 'python3'), $shellShim, $utf8)
$env:PATH = $binPath + ';' + (Split-Path -Parent $pythonPath) + ';' + $env:PATH
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
Write-Output 'このプロセスのPATHにgodotとPythonを設定しました。検証コマンドの内容は変更していません。'
