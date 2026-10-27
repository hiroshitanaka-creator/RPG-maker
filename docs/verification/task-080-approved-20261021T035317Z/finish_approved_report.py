from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,subprocess
w=Path('/workspace/task080');a=json.loads((w/'active-approved.json').read_text());run=Path(a['run']);out=Path(a['evidence']);repo=Path(a['repo']);source=Path('/workspace/RPG-maker')
chron=json.loads((out/'chronology.json').read_text());assert len(chron['records'])==19
assert chron['locked_all_pass'] and chron['import_first'] and chron['import_finished_before_every_verification'] and chron['sequential_no_overlap']
assert all(x['exit_code']==0 for x in chron['records'])
for x in chron['records']:assert hashlib.sha256((out/(x['name']+'.log')).read_bytes()).hexdigest()==x['log_sha256']
provenance=json.loads((out/'provenance.json').read_text());assert provenance['failed']==0
strict=(out/'02-assets-strict.log').read_text();assert '検査対象: 1159 件' in strict and 'NG ' not in strict
before=json.loads((out/'pretest-all-tracked-sha256.json').read_text());mismatch=[]
for name,entry in before.items():
 for location in [repo,source]:
  if hashlib.sha256((location/name).read_bytes()).hexdigest()!=entry['sha256']:mismatch.append({'path':name,'location':str(location)})
assert not mismatch,mismatch
rows=[]
for name in ['inn','item_shop','weapon_shop','shrine','armor_shop']:
 d=json.loads((out/('render-'+name+'.json')).read_text());assert d['failed']==0
 rows.append({'room':name,'checks':len(d['checks']),'inputs':len(d['inputs']),'failed':d['failed'],'occlusion':[c['detail'] for c in d['checks'] if c['label']=='家具の前後の遮蔽']})
summary={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'pretest_tree':a['pretest_tree'],'pretest_all_tracked_preserved':len(before),'mismatches':mismatch,'provenance_checks':len(provenance['checks']),'provenance_failures':provenance['failed'],'other_entries_compared':provenance['other_actual_entries_compared'],'legacy_owner_compared':provenance['legacy_owner_entries_compared'],'strict_images':1159,'strict_exit':0,'rooms':rows,'room_checks':sum(x['checks'] for x in rows),'room_inputs':sum(x['inputs'] for x in rows),'chronology_count':len(chron['records']),'locked':json.loads((out/'locked-results.json').read_text())}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
shutil.copyfile(run/'driver.log',out/'driver.log');shutil.copyfile(run/'prepare-driver.log',out/'prepare-driver.log')
for name in ['finish_approved_report.py','package_approved.py']:
 if (w/name).exists():shutil.copyfile(w/name,out/name)
(out/'engine.json').write_text(json.dumps({'version':'4.7.2.stable.official.ed1daf0bf','binary_sha256':hashlib.sha256((w/'bin/godot').read_bytes()).hexdigest()},indent=2)+'\n')
saves=out/'normal-saves';saves.mkdir()
for p in (run/'xdg/data').rglob('task080-normal-*.json'):shutil.copyfile(p,saves/p.name)
# 検証終了後の報告だけを追記。テストした実装・検査器は以後変更しない。
p=source/'docs/tasks/reports/080-adopted-room-walking-foundation.md';text=p.read_text()
text=text.replace('## 未達・引継ぎ', '## 初回時点の未達・引継ぎ（限定承認前の履歴）')
text=text.replace('## 最終実測', '## 初回候補の実測（限定承認前の履歴）')
text=text.replace('5室の歩行実装候補とローカル検証を用意した。全ゲーム完成・本番進行接続・正式保存完了とは扱わない。素材strictに未解消の依存があり、統合可能との判定ではない。','5室の歩行実装候補とローカル検証を用意した。初回の素材strict阻害は2026-10-21 03:49:55 UTCの限定承認に基づく変更で解消し、1159件成功を再実測した。詳細は末尾の限定承認・最終実測を参照。全ゲーム完成・本番進行接続・正式GitHub保存完了とは扱わない。')
text+='\n## 限定承認後の最終実測\n\n検証対象tree `'+a['pretest_tree']+'`。これは限定validator・追加検証器・承認記録までの候補。最終提出treeとの差は、この結果の報告と原証拠追加だけで、ゲーム・validator・検証器・台帳・画像のbytesは同一である。\n\n'
text+='editor import開始 '+chron['records'][0]['started_at_utc']+'、終了 '+chron['records'][0]['ended_at_utc']+'。次の検証開始 '+chron['records'][1]['started_at_utc']+'。全19実行にUTC ISO8601の開始/終了・コマンド・cwd・timeout・exit・原ログSHAを記録し、import先行・逐次・重複なしを照合。\n\n'
text+='| 検査 | 結果 |\n| --- | --- |\n| 素材strict | exit0、画像1159・音15・字体2・パレット3。問題なし |\n'
text+='| 限定出所の正負例・回帰・継続条件 | %d判定、失敗0 |\n'%summary['provenance_checks']
text+='| 5件以外の実出所項目 | %d項目、基点のcheck_provenanceと完全一致 |\n'%summary['other_entries_compared']
text+='| 既存owner | %d項目、実項目と必須項目欠落/作者・license不正/不正パスの回帰成功 |\n'%summary['legacy_owner_compared']
text+='| 5室入力・描画 | %d判定・%d入力イベント、失敗0 |\n'%(summary['room_checks'],summary['room_inputs'])
text+='| R-01〜R-08 | 原verify・原judge_output・300秒上限を維持、全PASS |\n| 保護ファイル | 26件すべて凍結SHA・基点SHA一致 |\n| 旧080 Python範囲検証 | 無変更の旧候補19f0ef9e08b546ad3b9d9143e5b6b97e59ba6d31でimport後に成功 |\n\n'
text+='原画5件の実ファイルを正例にし、同じフォルダにある未承認の荷受け所、traversal、非正規の二重slash、別日付のパスを拒否した。さらに各原画のread_bytesだけに1byte変更/別原画の内容を返す観測負例と、is_fileだけをfalseにする欠損負例を与え、すべて拒否。これらはメモリ上のファイル読取観測であり、原画の変更・削除・別フォルダ複製はしていない。正負例の前後で実原画5件SHAを照合した。author/provided_at/original_file/modified/licenseの欠落と不一致も拒否を維持。実装から期待するSHAを生成せず、承認固定SHAを新検証器へ明示した。\n\n'
text+='今回のvalidator差分は固定PR49の2箇所の差分と完全一致（20行追加・1行置換）。最新基点へpatchとして適用し、ファイル全体を旧版へ置換していない。台帳・採用PNG・原画・歩行実装・元080検証器・他の検査条件は前候補と同一bytes。前候補の初回strict失敗と旧coastal失敗は履歴証拠として保持し、後から成功へ書き換えない。旧coastalは今回再実行していない。\n\n'
text+='原証拠は `docs/verification/task-080-approved-'+a['stamp']+'/` に保存（.logは原bytesを可逆gzip、通常描画PNGは無加工）。新ZIPには全候補payload・binary patch・全変更SHA一覧、基点全tracked treeからの再構成・最終tree一致証拠・保護26 SHA一覧・再現コマンドを収録。旧ZIP2本は元bytesで保持し、Library ID `libfile_5494cd2d160c8191a6db103edeb95af2` と `libfile_7d337407ecd081919857cf57216a86e2` を変更しない。\n\n'
text+='今回の素材strict阻害は解消済み。残るのは親の正式commit/push/PR/全GitHub CI・検収と本番進行接続等の別段階。新世界接続や人物・販売・物語の追加はない。利用者実機/物理ゲームパッドの評価は未実施。PR49 main保留・066・親台帳は不変。\n'
p.write_text(text)
commands='# 080 限定承認後の再現手順\n\n基点 '+a['base']+'（tree db2d461e2c31b99f909056cf730c453823ab08ae）へZIPのchanges.patchを適用する。全ファイルとtree照合はreconstruction/に記録。PR49自体をmergeしない。\n\n'
commands+='空の専用XDG_DATA_HOME/XDG_CONFIG_HOME/XDG_CACHE_HOMEとRPG_QA_SAVE_PREFIXを用意し、固定Godot4.7.2をPATHへ置く。まず `godot --headless --editor --import --quit` を600秒上限で実行。その後、以下を順に実行する。\n\n```bash\npython3 tools/check_adopted_room_provenance.py --output "$ADOPTED_ROOM_OUTPUT"\npython3 tools/validate_assets.py --strict\n# DISPLAYにX11を用意。各室180秒。\nfor ADOPTED_ROOM_INDEX in 0 1 2 3 4; do\n  export ADOPTED_ROOM_INDEX\n  timeout 180 godot --display-driver x11 --audio-driver Dummy --path . --script res://tools/check_adopted_room_foundation.gd\ndone\npython3 tools/check_frozen_files.py\n```\n\nR-01〜R-08は.scope-lock/spec.lock.jsonのverifyを原文のまま各300秒で実行し、元tools/run_locked_checks.pyのjudge_outputを使用する。時刻付きrunner run_approved.pyを証拠に同梱。各実行の絶対cwd/環境/コマンド/timeout/start/end/exitは*.execution.json。別環境では作業先と出力先だけを対応させる。\n\n'
commands+='旧tools/check_adopted_room_foundation.pyの「変更はregistryだけ」という段階限定条件は、前候補tree19f0ef9e08b546ad3b9d9143e5b6b97e59ba6d31で固定検証する。今回の限定validator変更後には新check_adopted_room_provenance.pyが承認差分の完全一致・旧候補bytes不変・継続条件と負例を検査する。旧検証器は変更していない。\n\n元5PNG/registryや原画を複製・改変する手順はない。負例は読取観測のみ。原ログとPNGは新ディレクトリへ保存し、旧ZIPや旧失敗ログを上書きしない。\n'
(out/'REPRODUCE.md').write_text(commands)
print(json.dumps({k:v for k,v in summary.items() if k not in ['rows','locked']},ensure_ascii=False),flush=True)
