# 017 016提出の独立再レビュー

## 結論

**差し戻し1件（F3・優先度高）。013の元F1・元F2は解消を実証したが、新設された016自身の固定範囲監査に同種の自己一致が残る。** 親がF3の最小修正を判断することを推奨する。CI緑をもって007開始可能とは判定しない。コード修正・追加AI委譲・main統合・007以降の開始は行っていない。017は報告済みで終了する。

## 対象・開始条件

- 最新mainをfetch/ls-remoteで照合：`5be5aeecf1a3c73a5242d18f75975eb02fa55cda`。これは比較元であり、016レビューの対象として代用していない。
- 016提出：`184a40b295df07479d22eccec9cdf0e489f7d97d`。登録ブランチ `codex/task-017-review-audit-fixes` の登録commit `44cb95172b44d86926da29b6854b79399e8eedd2` が提出を含み、その差分は017依頼書追加だけ。
- 016機能完成：`6706397e2674ffa382852e0f33ce23edf5c76634`、tree `02105ab24ef39a2acf7405274e040d8cefaa399b`、完成記録commit `9f1a18892273ac06d9776d2ddf8dbcc1c6423453`。
- 固定006：`5f1c2ba231191b25b9b32a814b616a9f8d0a54ce`、固定009：`ce07fdada0466138260ab678c10fd78e61c0c63d`、固定012：`c327e7c439c9c8c8f1fd640e6cda6df7550fb26a`、012独立信頼記録：`9e647b3d6d0f91b061f7de974dbb5411937a2bb9`。
- 013元報告・016依頼/報告・実差分・workflow・assertion対応表を読んだ。開始時の未コミット変更0件。ローカル初期workは古いmainだったため、登録ブランチを取得してから実施した。登録時点のリモートとローカルHEADは一致し、今回由来の未push commitは0件。
- 実行・故障注入はクラウド `/workspace/review017/` 内の独立コピーのみ。元repoで変更するのは017状態行と本報告のみ。既定Godot 4.6.3は検証に使用せず、4.7.2-stable ZIPを取得しSHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、version `4.7.2.stable.official.ed1daf0bf`を照合した。
- 指定GPT-6 Astra/Mediumの実効設定を照合するAPIはなく、独立確認済みとは称さない。追加AI委譲・ローカルPC利用なし。今回は追加スキルを適用していない。

## F3：016の完成点は最新manifest・workflow・CLI・checkoutの自己一致で移動できる

**根拠：** `tools/check_task016_scope.py:50–65` は期待SHAをCLIの`completed`から、期待treeを`show(repo, latest, RECORD)`から取得する。CLIは最新workflowの`FIXED_016_SHA`が供給する。同じ最新入力をそろえて変更した場合、承認済み6706397とは独立に照合されない。`main:81–84`も渡されたSHAへの許可範囲監査のみ。状態行は正規化されるので、状態だけ違う子commitも範囲監査に通る。正常な後続編集で016を自動探索しない点は改善しているが、完成参照の誤更新を拒否する条件はない。

**実証：** 6706397から016依頼書の状態行だけを変更した子commit `b05cae08d9e2e2b5d8351dbed1269d7869657143` を一時Gitコピーで作成。184a40bを親に、016manifestのcompleted_sha/treeとworkflowのFIXED_016_SHA/別checkout参照を同時変更した `7f91ec5c780649d59a1a9a55b180403f8a0f0649` を作成した。監査器コードは1バイトも変えず、実際の別checkoutも子commitに合わせ、既存CLIを実行した。

- `check_task016_scope.py`：**終了0、PASS、6/6、3.943秒**。承認済み6706397ではない子commitを016完成点として受理。
- `check_task016_fixed_anchor.py`：終了0、PASS、0.075秒。012の基点のみを照合するため016の付替えは検出しない。
- 固定012当時の`test_task012_pinned_audit.py`：終了0、17/17 PASS。
- `test_task016_fixed_anchor.py`：終了0、14/14 PASS。

これはコード自体を改竄して検査を無効化する反証ではない。**元013 F1と同じ、参照と記録だけの同時付替え**で再現する。故障注入commitで全20jobを再起動したとは主張しないが、固定点を検査する上記4コマンドがすべて受理することは実行済み。

**影響：** 016の段階限定検査を承認済み完成commitに固定したという保証が成立しない。固定対象が動いた後も「完成差分PASS」と報告され得る。017作業内容2の「新しい監査自身が可変期待値・自己一致を持たない」、016作業内容7の完成時不変SHAの条件に未達。

**最小修正案：** 既存の016監査/独立照合器に、確定済み6706397の完全SHA/tree（または既存9f1a188の完成記録を読む固定の信頼基点）を独立定数として持たせ、最新manifest・workflow・CLI・実checkoutをそれと照合する。今回の同時付替え、単独誤SHA/tree、欠損を負例追加する。新しい固定用タスクを再帰的に要求せず、012の当時17件、012の既存独立基点、016の許可範囲、後続正常編集を保持する。レビュー担当は修正しない。

### F3を再現する最小手順

以下は使い捨てcloneのみで実行する。`repo`は184a40bを取得したコピー、`fixed`は同じコピーから別cloneした作業場所。元repoには適用しない。helperは提出の既存`tools/test_task012_pinned_audit.py`を使用する。

```python
import json
from pathlib import Path
import test_task012_pinned_audit as a
latest = '184a40b295df07479d22eccec9cdf0e489f7d97d'
original = '6706397e2674ffa382852e0f33ce23edf5c76634'
request = 'docs/tasks/016-fix-audit-review.md'
record = 'docs/verification/task-016/completed-audit.json'
state = a.normalized_request(a.show(repo, original, request)).replace(
    b'- state: excluded', '- 状態：017独立反証コピー限定'.encode())
moved = a.synthetic(repo, original, {request: state})
manifest = json.loads(a.show(repo, latest, record))
manifest['completed_sha'] = moved
manifest['completed_tree'] = a.run(repo, 'rev-parse', moved+'^{tree}').decode().strip()
workflow = a.show(repo, latest, a.WORKFLOW).replace(original.encode(), moved.encode())
current = a.synthetic(repo, latest, {record: json.dumps(manifest).encode(), a.WORKFLOW: workflow})
a.run(repo, 'clone', '--quiet', '--shared', str(repo), str(fixed))
a.run(fixed, 'checkout', '--quiet', '--detach', moved)
a.run(repo, 'checkout', '--quiet', '--detach', current)
```

```sh
# repo内。moved/currentは上で得た完全SHA。
timeout 180 python tools/check_task016_scope.py   --completed-sha "$moved" --fixed-path "$fixed" --latest-sha "$current"
```

commit時刻で合成SHAは変わるが、状態行だけ変えた子commitが終了0になる構造は同じ。

## 元F1：解消

013の中核手順をそのまま再実行した。固定012の状態だけ変えた子 `51b932cd9509a55077a55197f754962f880a7ed5` と、manifest/workflow/checkoutを同時付替えした最新 `2f8873fa9e96f55c47c518f95e90fc03881b096d` を作成。

- 子checkoutに残る無変更の当時012検査：終了0、17/17 PASS、1.719秒。元反証の前提を再確認。
- 新しい`check_task016_fixed_anchor.py --fixed012-path <子checkout> --latest-sha <同時付替え最新>`：**終了1、0.055秒、`012 manifestが独立信頼基点の記録と不一致`**。
- 正常184a40bの独立照合と14件正負例は全PASS。期待記録をハードコードされた9e647b3から読むこと、完全SHA/tree、記録全体、workflow、実checkoutを検証することをコードで確認。最新manifestから012期待値を作らず、可変git log探索・信頼記録欠損fallbackなし。

012に対する修正は有効。上記F3はその修正を否定するものではなく、新設016監査への同型の取りこぼしである。

## 元F2：解消

184a40bコピーの `world/region2_village.json` の `site.rooms[2].events` だけを元013と同じ次の値へ変更し、既存の最新回帰GDを直接実行した。地形・fixture・本番コード・検査器は無変更。dirtyコピーの故障注入なので、cleanを要求するPythonラッパーの成功とは呼ばない。

```json
[{"id":"task013_counter_copy","kind":"npc","cell":[8,4],"text":["コピー限定"]}]
```

`Godot_v4.7.2-stable_linux.x86_64 --headless --path <コピー> --script res://tools/check_region2_village_regression.gd`（各プロセス上限180秒）。出力JSONは実行前に削除し、stderrのパーサー/ERROR/WARNINGも検査した。

| 独立実行ケース | 終了 | checks | 秒 | 観測 |
| --- | ---: | ---: | ---: | --- |
| 元013カウンター裏[8,4] | 0 | 7661 | 17.830 | PASS、隣接[7,4]実到達、占有拒否・全状態保持、20保存後退出 |
| 追加NPCで客側目標[8,6]を占有 | 1 | 7658 | 16.613 | 必須目標閉塞assertion失敗 |
| 追加NPCで室外扉[8,11]を占有 | 1 | 7543 | 17.180 | 8扉リンク・実退出・保存後退出のassertion失敗 |
| NPC占有ガード無効化 | 1 | 7663 | 17.640 | 全セル通行・足元拒否・状態保持の3件失敗 |
| 占有拒否時に所持金を変える | 1 | 7661 | 16.796 | 拒否時全状態保持assertion失敗 |

すべてパーサー/ERROR/WARNINGなし。負例はtimeout等を成功扱いしていない。各改変をfinallyで元バイトへ復元し、本番ファイル差分なしを確認した。

`maps -> target_checks`は非占有目標への従来BFS/実歩行を保ち、家具裏占有目標では`reachable_adjacent -> walk`と足元拒否・全状態保持を検証する。単なるskipではない。必須front/アーチは占有でも不合格。固定006は全目標足元への旧到達を保持する。対応表S06/A082とhelper追記を確認、135箇所・未分類0。

撮影器の実在名は `tools/capture_task009_village_regression.gd`。016では無変更。家具裏の撮影点はnative fixtureから取り、[8,4]そのものを固定目標にしていない。提出CIの同NPC付き通常入力描画は終了0・132項目・28枚・108.503秒で、180秒/600移動/3000入力/300ターンを保持。今回クラウド手動環境にxvfb-runがないため手動描画は再実行せず、当該提出CIの直接ログを根拠とする。別のNPC配置が全て撮影に適合することまでは主張しない。

## 固定検査・最新回帰・正常な後続変更

- 固定012当時の検査器を別checkoutから184a40bへ実行：17/17 PASS。新規012独立照合14/14、016正常範囲監査6/6 PASS。F3は既存6件で網羅していない同時付替えを追加して発見したもの。
- 最新本番184a40bをcleanコピーで、固定版Godot import（600秒以内、終了0、検出対象エラーなし）後に`python tools/check_region2_village_regression.py --commit 184a40b295df07479d22eccec9cdf0e489f7d97d --godot <固定版>`で独立実行：runtime7662、17.357秒、20保存。別プロセスrestartは10/27/38/52/44、0.799/0.804/0.801/0.896/0.826秒、すべてPASS。固定版の成功で最新動作を代用していない。
- `python tools/check_task009_assertion_map.py`：135箇所・未分類0・fixture=fixed006。`python tools/check_frozen_files.py`：26/26一致。
- main→184a40bの `assets/scripts/world/data/test/.scope-lock/addons/project.godot/.github/workflows/ci.yml` はGit差分0。016開始→提出のtools差分は許可された5ファイルのみ（最新GD、独立照合、独立照合反証、016範囲監査、既存lifecycle反証への追加）。当時006/009/012検査器・固定記録・原画・保護テストを維持。
- 専用workflowの差分は追加のみ。旧全コマンド、matrix固定/最新×7mode、3job定義の15分、import600秒、実行/描画180秒、内部180000ms/600移動/3000入力/300ターンを維持。既存ci.ymlの35分/25分、Rverify300秒も無変更。削除、ALLOWED拡張、黙ったskip、continue-on-error、上限延長なし。matrix反対世代の条件付きstepは実行省略だが、対応する世代jobが実行している。
- 後続依頼書追加・状態行更新・別範囲コード変更を既存17件/6件で再実行し、正常変更を固定範囲監査で誤拒否しないことを確認。実017登録44cb951も012独立照合/016固定範囲監査PASS。さらに008/010/011関連文書への追記・017登録・新規原画パスへの同一バイト画像追加を同時に合成した後続commitでも同照合/範囲監査PASS。これは固定監査の非干渉検証であり、後続機能の実装成功ではない。
- 007は今回の[8,4]正例を受理。空events/受付無反応/祠不可/撮影無反応の段階限定4assertionは固定006に残り、最新007施設受入へ引継ぐ。007の6人・宿・祠の統合サービス正負例は未実装・未検証。配置決定後の撮影点衝突は再検証が必要。
- 008/010/011本文を読み、011に固定時点受入と最新継続条件の分離指示があることを確認。014は対象checkoutにないため、リモート登録branch `codex/task-014-record-four-lords` の `450a449291954a2d0bd376f8d5dcfd2b375493ab` から依頼書だけをread-only確認した（main/対象へmergeなし）。文書・原画追加を006/009/012/016の完成差分へ混ぜない構造である。015は対象repoに依頼書がなく、015の名のリモートbranchも見つからず、本文固有の条件は未確認。一般の文書/原画追加非干渉を015実物の受入済みとはしない。

## 提出184a40bの全CI実物

通常 `gh api` は403だったため、接続済みGitHubのread-only APIで両runの全job/stepと全20jobのログを直接取得した。016報告の過去9f1a188 CIを転載していない。全ログのcheckout SHAを184a40bと照合し、固定実行のSHAも結果JSONと区別した。

- [通常CI 37203162135](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162135)：3/3 completed/success。R-01〜R-08すべてexit=0/tests_ran=True/parser_failed=False、保護26/26、素材・既存回帰もsuccess。
- [専用CI 37203162140](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140)：17/17 completed/success。固定006 runtime7592/20保存/restart9,26,37,51,43、描画137/34/17×5・49枚。最新184a40b runtime7662/restart10,27,38,52,44、描画132/34/17×5・49枚。固定009範囲、固定012の17件、新独立照合14件、016範囲6件、NPC等13正負例が実行済み。
- NPC正負例は外観39×2と7656回帰も保持。元F2正例7661/20保存、占有無視/状態破壊/客側閉塞/出口閉塞、既存誤接続/不正保存受理が期待どおり。これらの13件PASSは「負例で実際の失敗を確認した」を含む。
- 時間はログ最初〜最後のtimestamp差（四捨五入）。課金時間・費用・過去版との同条件性能差は未計測。

| job（直接取得ログ） | 結果 | 秒 |
| --- | --- | ---: |
| [Godot・凍結受入テスト](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162135/job/111438805602) | success | 221 |
| [素材検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162135/job/111438805675) | success | 107 |
| [試遊前の通常戦闘・案内・画面・復帰検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162135/job/111438806039) | success | 267 |
| [acceptance-and-regression (latest)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438804806) | success | 124 |
| [lifecycle-audit](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438804807) | success | 419 |
| [acceptance-and-regression (fixed)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438804877) | success | 122 |
| [normal-input-and-rendering (latest, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438804884) | success | 158 |
| [normal-input-and-rendering (fixed, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438804923) | success | 163 |
| [normal-input-and-rendering (latest, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438804932) | success | 252 |
| [normal-input-and-rendering (fixed, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438804942) | success | 154 |
| [normal-input-and-rendering (latest, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438804972) | success | 150 |
| [normal-input-and-rendering (latest, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438804979) | success | 154 |
| [normal-input-and-rendering (latest, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438804981) | success | 178 |
| [normal-input-and-rendering (latest, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438804988) | success | 178 |
| [normal-input-and-rendering (latest, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438805002) | success | 193 |
| [normal-input-and-rendering (fixed, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438805011) | success | 225 |
| [normal-input-and-rendering (fixed, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438805031) | success | 161 |
| [normal-input-and-rendering (fixed, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438805045) | success | 177 |
| [normal-input-and-rendering (fixed, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438805053) | success | 257 |
| [normal-input-and-rendering (fixed, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37203162140/job/111438805269) | success | 147 |

## 変更・未確認・終了

- 変更ファイル：`docs/tasks/017-review-audit-fixes.md` の状態行、`docs/tasks/reports/017-review-audit-fixes.md`（本報告）だけ。反証用ソース・Git子commit・実行出力は使い捨てコピー内に限定し、再現手順・実測・全jobURLを本報告へ保存する。
- `git diff --check`と許可2ファイル以外の差分0を確認して通常commit/pushする。レビュー提出commit自身のCIは最終応答に結果または未確認を記載し、上記016対象CIと混同しない。
- 未達：F3の固定016独立基点（修正は本依頼範囲外）。未確認：015本文、将来007施設・011機能の統合実装、人間試遊、約60時間実測、任意NPC配置の全描画。今回の固定006全動作/全描画とR全8は提出CI直接ログによる確認であり、全てを手元で再実行したという意味ではない。
- 親の判断事項はF3修正発注の1件。009/012状態は変更せず、main未統合を保持し、007以降を開始せず**報告済み**で終了する。
