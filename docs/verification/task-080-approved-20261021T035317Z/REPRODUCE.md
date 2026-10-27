# 080 限定承認後の再現手順

基点 e677896d3e61b8fe8136ef60c5c76f41ad76701d（tree db2d461e2c31b99f909056cf730c453823ab08ae）へZIPのchanges.patchを適用する。全ファイルとtree照合はreconstruction/に記録。PR49自体をmergeしない。

空の専用XDG_DATA_HOME/XDG_CONFIG_HOME/XDG_CACHE_HOMEとRPG_QA_SAVE_PREFIXを用意し、固定Godot4.7.2をPATHへ置く。まず `godot --headless --editor --import --quit` を600秒上限で実行。その後、以下を順に実行する。

```bash
python3 tools/check_adopted_room_provenance.py --output "$ADOPTED_ROOM_OUTPUT"
python3 tools/validate_assets.py --strict
# DISPLAYにX11を用意。各室180秒。
for ADOPTED_ROOM_INDEX in 0 1 2 3 4; do
  export ADOPTED_ROOM_INDEX
  timeout 180 godot --display-driver x11 --audio-driver Dummy --path . --script res://tools/check_adopted_room_foundation.gd
done
python3 tools/check_frozen_files.py
```

R-01〜R-08は.scope-lock/spec.lock.jsonのverifyを原文のまま各300秒で実行し、元tools/run_locked_checks.pyのjudge_outputを使用する。時刻付きrunner run_approved.pyを証拠に同梱。各実行の絶対cwd/環境/コマンド/timeout/start/end/exitは*.execution.json。別環境では作業先と出力先だけを対応させる。

旧tools/check_adopted_room_foundation.pyの「変更はregistryだけ」という段階限定条件は、前候補tree19f0ef9e08b546ad3b9d9143e5b6b97e59ba6d31で固定検証する。今回の限定validator変更後には新check_adopted_room_provenance.pyが承認差分の完全一致・旧候補bytes不変・継続条件と負例を検査する。旧検証器は変更していない。

元5PNG/registryや原画を複製・改変する手順はない。負例は読取観測のみ。原ログとPNGは新ディレクトリへ保存し、旧ZIPや旧失敗ログを上書きしない。
