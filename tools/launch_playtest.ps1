# 人間の試遊用。ゲームを起動した後、このPowerShell画面を保持する必要はない。
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'launch_game.ps1') -HumanPlaytest
Write-Output '試遊の記録を有効にしてゲームを開きました。探索中の「記録」で評価・JSON保存ができます。中断する場合はゲーム内のセーブも行ってください。'
