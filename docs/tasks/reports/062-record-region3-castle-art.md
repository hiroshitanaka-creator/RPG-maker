# 062 第3地方の城と飛行船の採用原画保管・記録 報告

## 変更したファイル（全8件）

- `assets/_incoming/owner-2026-10-10-grok-region3-castle/region3-castle-exterior.png`
- `assets/_incoming/owner-2026-10-10-grok-region3-castle/region3-castle-great-hall.png`
- `assets/_incoming/owner-2026-10-10-grok-region3-castle/region3-castle-throne-room.png`
- `assets/_incoming/owner-2026-10-10-grok-region3-castle/airship-views-3.png`
- `assets/_incoming/owner-2026-10-10-grok-region3-castle/region3-castle-airship-dock.png`
- `docs/roadmap-v2.md`
- `docs/tasks/062-record-region3-castle-art.md`
- `docs/tasks/reports/062-record-region3-castle-art.md`

## 対象と実施範囲

- 基点main：`87f4e66ed64f2ae9a92538acb9716c6a01f5cb27`。依頼登録：`973fbede6a2e98dda8e22b0687ede28f0c226e63`。
- 作業branch：`codex/task-062-record-region3-castle-art`。開始時は登録commitと一致し、未コミット変更・未pushコミットなし。
- MSIのローカルWindows Codexワークスペースで実施。指定モデルはGPT-6 Astra／Highだが、実行モデル設定をこの作業のツールから独立確認してはいない。
- `AGENTS.md`、`docs/asset-spec.md`、062依頼書、`docs/tasks/README.md`、既存の付録B「4体の主の原画」を確認した。チェックアウトに `.agents/skills` は存在しない。
- 5枚のPNG原bytesを固定Git blobから同一パスへ保管。画像加工・本番組込み・部屋data・通行map・registry・CI・保護・OS設定の変更なし。保存系列060/061の変更なし。
- 親担当の `docs/tasks/README.md` と `docs/decision-log.md` は編集していない。mainのマージは親が行う。

## 原画の実測と閲覧

下表の5枚は、依頼書のSHA-256・bytesと全件一致。実画素を各PNGから表示して確認し、指定の内容・配置・向きと矛盾なし。原画の再保存はしていない。

| 原画 | SHA-256実測 | bytes実測 | 幅×高さ | 閲覧結果 |
| --- | --- | ---: | --- | --- |
| 城の外観 | `d3f08bd5e3433848fe2d606175646605b083ac3e521c123a74fa45d566e2dcef` | 3659721 | 1712×1152 | 下中央の出口、中央の火鉢、本館大扉、右の修理場、左上の噴煙を確認 |
| 大広間 | `ff94696daeab01d2b39a9d5a8151942c9bd933017e2e5596ef43bc8c58765c7a` | 1224589 | 1168×784 | 上下中央の扉、赤い敷物、左右3本ずつの柱、四隅の火鉢を確認 |
| 謁見の間（描き直し版） | `5f91e573956a5b4a60346e5635447657768f3eec829428a2c616e5aec8aa0bb2` | 2150096 | 1712×1152 | 下中央の扉、段上の空の玉座、敷物、左右2本ずつの柱、窓の火山と雪山を確認 |
| 飛行船3姿 | `a639308b9bc604c57a0c93b3f110fb27c63c8ddabe728e71f033cdf75193e1dc` | 724105 | 1168×784 | 左から修理後側面（船首右）、修理後上面（船首上）、修理前上面（船首上）を確認 |
| 飛行船の修理場 | `5a25389151fb579ad667cdd4e8bbaea269daaa8c293198a521ba185eda3157bf` | 1367119 | 1168×784 | 船なし、下中央の大扉、空いた床・台座4本、天窓、左の炉・金床・作業台、右の資材・道具を確認 |

## 6 incomingの出典照合

全6本のorigin refを取得し、各完全SHAの単一親が基点mainで、親との差分が指定PNG1枚の追加だけであることを確認した。

| branch | 完全commit SHA | blob SHA | 採否 |
| --- | --- | --- | --- |
| `incoming/owner-2026-10-10-grok-region3-castle` | `7cacdc724d776e9ee5365a5a7eb201c70e4f00d8` | `c1c84fa3bcd3bf2ad73ba0a7ee123875310dcdd2` | 採用・原bytes保管 |
| `incoming/owner-2026-10-10-grok-region3-great-hall` | `753290739362a4b97a5fc34d0788ab838f74bb1c` | `341c72df74b0bb5af70b0115bfb5d2602c9870ad` | 採用・原bytes保管 |
| `incoming/owner-2026-10-10-grok-region3-throne-room-redo` | `6e029a22facc3262e4525ffcc52e269eb7962bfa` | `25df4859d4a58ef7af5fb633cb5b32cdbf0d5820` | 採用・原bytes保管 |
| `incoming/owner-2026-10-10-grok-region3-airship` | `a90cf6522f00f1589f19c8cd583c591718f48b34` | `e296f6168c464492fe9d04dbeb3ff09ba9390de1` | 採用・原bytes保管 |
| `incoming/owner-2026-10-10-grok-region3-airship-dock` | `da43302bcb6d23f2780ce9ff53f46cdd35546e02` | `ed50848fa2ac633e6dbdcfe35572581dc871508d` | 採用・原bytes保管 |
| `incoming/owner-2026-10-10-grok-region3-throne-room` | `570fb9854509335f28235d74519bd9511c4a684d` | `cf1b1221a6ee276be968df381b7e291d479feb5f` | 不採用・未取り込み |

旧謁見のblobもbytesを読み取り、SHA-256 `dbb82458d251907eb83f842660013cbef57ea01c4db50f146a902208ad863b4a`、1,097,588 bytes、1168×784を実測した。旧画像は作業ツリーへ取り込んでいない。採用謁見は `5f91e573956a5b4a60346e5635447657768f3eec829428a2c616e5aec8aa0bb2` であり、旧版と異なる。旧branchは元の完全SHAを保持する。

## 記録した内容

`docs/roadmap-v2.md` の新付録B節に、5パス・branch・完全SHA・SHA-256・bytes・内容・用途を記録した。外観/大広間/謁見/修理場は一枚絵背景の原画、飛行船3姿は世界マップと修理場に重ねる動く絵の元。修理場に船を描かず別絵を重ねる前提を保持した。

外観本館→大広間→謁見、外観右→修理場と上下の壁の扉は「原画依頼時の接続想定」と明記し、実装済みと扱っていない。2026-10-10採用、謁見redo採用/旧版不採用、城の人々の役割・見た目と修理場面の細部が未決であることを記録した。

## 実行コマンドと検証

ローカル実測（2026-10-10）：

| コマンド・照合 | 結果 |
| --- | --- |
| `git fetch origin 'refs/heads/incoming/owner-2026-10-10-grok-region3-*:refs/remotes/origin/incoming/owner-2026-10-10-grok-region3-*'` | 6 refと指定完全SHA一致 |
| `git show -s --format=%P <SHA>` / `git diff-tree --no-commit-id --name-status -r <SHA>` | 全6本が基点mainを単一親とし、指定PNG1枚追加のみ |
| `git cat-file blob <blob>`、SHA-256・サイズ・PNG寸法の読み取り | 採用5枚と不採用1枚を実測。採用5枚は保管後・ステージblobも一致 |
| `git ls-files assets/_incoming/owner-2026-10-10-grok-region3-castle/` | 指定5枚だけ |
| `godot --version` | `4.7.2.stable.official.ed1daf0bf` |
| `godot --headless --editor --import --quit` | exit 0、SCRIPT ERROR / ERROR / WARNING / Parse Errorなし |
| `python tools/validate_assets.py --strict` | exit 0、画像1154件・音15件・字体2件、問題なし |
| `python tools/check_frozen_files.py`（検証前後） | exit 0、26/26一致 |
| `git diff --check` | exit 0 |
| 既存roadmapと追加節以外のbytes比較 | 完全一致 |

Godotは既存ローカル4.7.2の実行体2本をこのタスクの `.tools/godot/4.7.2/` へコピーして使用した。実行体SHA-256は `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`。ユーザーの既存作業・実行体・保存は変更せず、プロセスの保存先をタスク内へ分離した。importが生成した追跡外UID2本は、この作業で生成したものだけを除去した。

R-01〜R-08は `.scope-lock/spec.lock.json` の各verify文字列を変更せず、各300秒上限で順次実行した。追跡対象の既存検証JSONを書き換えないよう、出力だけタスク内へ保存し、既存 `tools/run_locked_checks.py` の `judge_output` で同じ判定を適用した。契約・検査器・時間上限は不変。

| 要件 | 実行対象 | 結果 |
| --- | --- | --- |
| R-01 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_job_data.gd -gexit` | PASS、exit 0、2 tests / 765 assertions |
| R-02 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_job_actions.gd -gexit` | PASS、exit 0、5 tests / 946 assertions |
| R-03 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_ability_slots.gd -gexit` | PASS、exit 0、2 tests / 73 assertions |
| R-04 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_monster_form.gd -gexit` | PASS、exit 0、1 test / 293 assertions |
| R-05 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_battle_loop.gd -gexit` | PASS、exit 0、2 tests / 79 assertions |
| R-06 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_save_roundtrip.gd -gexit` | PASS、exit 0、2 tests / 87 assertions |
| R-07 | `godot --headless --path . --script res://tools/smoke_first_region.gd` | PASS、exit 0、A01〜A14全14件PASS |
| R-08 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://test/unit -gprefix=test_ -gexit` | PASS、exit 0、17 tests / 2302 assertions |

全GUT結果は failed_assertions=0 / pending=0 / invalid=false。実行なし・構文エラー・タイムアウト・警告を成功扱いしていない。

GitHubの従来型branch protection APIは `Branch not protected (404)`。mainは有効な `protect-main` ruleset（ID `24491681`）で deletion / non_fast_forward を禁止している。取得した設定を終了時にも照合する。

この報告の初回commit時点ではCI未実行。最終headのpush/PR全CI全job終了と結果、原CI参照、完全commit SHA、PR URLはPR本文と親への引継ぎに記録し、過去headの成功で代用しない。報告文書を含む最終headが確定する前に、そのheadのCI成功を先取りして記載しない。

## 未達・未検証と引継ぎ

main取込み、親担当の記録更新、マージ後の原画・folder件数・全CI・旧branchの最終照合は親担当。本番への画像組込みは今回の対象外。城の人々と修理場面の細部は未決のまま残す。
