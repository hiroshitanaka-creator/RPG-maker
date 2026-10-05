# 024 栞と原画記録の独立照合

## 対象と結論

- 照合日：2026-10-05 UTC。
- 008最終対象：`9c77969506510d95883bd7f8525637311bd09c45`。
- 差分の基準main：`86698d0c8992cfbb3720bdbc4fe3ce8fe9371d3c`。動くmainではなく、この完全SHAに固定して比較した。
- 024登録：`990c689866967208cdfe2a0fec56a6b97bf5d710`、ブランチ `codex/task-024-review-recorded-art`。登録コミットは008対象に024依頼書を追加しただけ。
- 判定：PASS。指定文・表・注意、変更4文書限定、原画・台帳・本番・検査・保護不変、対象SHAの全CI成功を確認。不備と本文修正要求は0件。

008依頼書・報告書・対象4文書の差分を読み、008担当の自己申告とは別に、Gitの実blob、作業場所の原画、GitHubのrun/jobsと実行ログから照合した。新しい仕様・名前・原画の解釈や採用は決めていない。main統合と008の「確認済み」への更新は親担当へ引き継ぐ。

## 文書と変更範囲

| 照合項目 | 結果と根拠 |
| --- | --- |
| 道具文書3節の見出し | PASS。「3. 桜封の栞（集める物）」と一致。 |
| 既存の決定3行 | PASS。基準mainの3行に対し「メダル」→「桜封の栞」の置換だけで、対象の3行と全文一致。調べる場所を宝箱と別種類にする決定と、交換してくれる人がいる決定も不変。 |
| 2026-10-04の決定2行 | PASS。名前「桜封の栞」と、指定パスの左から2番目の透明な候補、花びら3枚・細い金色の枠・深い紅色の房を、依頼書の指定文どおり記録。行末の句点を含む文書形式を確認。 |
| 未決 | PASS。総数・配置・交換枚数と内容・交換する人の名前と場所を指定どおり未決のまま保持。 |
| 変更履歴・未実装注意 | PASS。指定の2026-10-04履歴1行を追記。冒頭の未実装・指示待ちの注意は全バイト不変。3節を旧内容へ戻し、指定履歴1行を除いた文字列が基準文書と一致。 |
| 付録B | PASS。「付録B追記：Grok の原画（owner-2026-10-05-grok-batch3）」の表は、ヘッダー2行とデータ11行が依頼書原文と全文一致。注意3項目も箇条書きの字下げだけを除き全文一致。 |
| 注意の保持 | PASS。1階外入口の組込み時確認、暗い床での暗色敵の視認性確認と必要時の依頼者判断、不採用3候補を使わないことを保持。 |
| 付録B以外の計画 | PASS。追加節（原画の保管先・文書記録だけという説明、指定表・注意）を取り除くと、計画書全体が基準mainと一致。既存表・既存注意も不変。 |
| 008依頼書 | PASS。「未着手」→「報告済み」の状態1行だけ。仕様本文は不変。 |
| 008報告書 | PASS。変更前後の3節、main SHA、原画11枚とhash、台帳未登録の区別、自己点検・CI出典・未実装事項を確認。本文コミット5458768のCIと最終9c77969を混同せず、後者を下記で直接取得した。 |

`git diff --name-status 86698d0c8992cfbb3720bdbc4fe3ce8fe9371d3c 9c77969506510d95883bd7f8525637311bd09c45` の全件は次の4文書のみ（155追加・4削除）。

```text
M docs/design/items-and-equipment.md
M docs/roadmap-v2.md
M docs/tasks/008-record-bookmark-and-batch3.md
A docs/tasks/reports/008-record-bookmark-and-batch3.md
```

道具文書の表題・導入・全回復薬の欄など、3節以外の既存の古いメダル表記は依頼範囲外であり、不備・修正要求に含めない。

## 原画・台帳・本番・検査の不変

保管場所は `assets/_incoming/owner-2026-10-05-grok-batch3/`。表から抽出した11ファイルと、基準SHA・対象SHAのGitツリーおよび作業場所のファイル一覧が一致し、不足0・余分0・移動0・改名0。Git blobを読み出して基準と対象と実ファイルの全バイト一致を確認し、SHA-256を独立計算した。次の値は008報告書の全11件とも一致。

| ファイル名 | SHA-256（基準・対象・実ファイル一致） |
| --- | --- |
| `region3-village-exterior.png` | `a024fd4bbaa0855133224505685284e89c3456a69d2295e16b58fc8f87dcebc2` |
| `region3-village-room-inn.png` | `12e496ec60206222f6a30a0611d92e70fd4360a2092769451dbfab2f9b5ef3c5` |
| `region3-village-room-item-shop.png` | `f09c53d8a2564333ed0610c6c078a9f3481bf2ca234c3c6be73e8378a465306d` |
| `region3-village-room-weapon-shop.png` | `5a03fb0ebf04526f5cfe5b4fa04fa6d76341c0b866449786b078a5fbc9eea250` |
| `region3-village-room-shrine.png` | `851ec005215abaa9c6f030972e0da22c051288c54f545472d10c2e834740e312` |
| `region3-volcano-cave-1f.png` | `1af5b2b63fa1155f18af66c9caa53a5d5f7f2fb2aa8251e1a811525af2e055ec` |
| `region3-volcano-cave-2f.png` | `8ee38537fc9693bce3d88ec89e3c260c580d74f429ea7a20f4fb25c9cf53a2f6` |
| `region3-volcano-cave-boss-floor.png` | `dcb4819dfb897567d4786a0c9000888ec3d520c98639ae8ede72b55686355e09` |
| `region3-volcano-cave-boss.png` | `3f04032b80fc5dba64da30df644310248bd8b6246b09564dffecbf644db4f30c` |
| `region3-volcano-cave-battle.png` | `70e931340241589d3af1f77975932f2e85fef895c5a5792deeec980b61db03ac` |
| `bookmark-design-candidates-4.png` | `6e1c8dad4e7a2b495b8a478c6db053d2feafdce5c73508c2b20aed71f94f9a36` |

`assets/registry.json` の全JSON（assets 1140件）を読み、保管先と11ファイル名の登録は0件と確認した。台帳自体は基準・対象・実ファイルで全バイト一致。これは `_incoming` に保管済みの原画であり、登録済みのゲーム素材ではない。`docs/asset-spec.md` の外部素材の取り込み手順でも `_incoming` は検査対象外の保管場所とされている。今回の許可外の台帳登録・加工・実装は不要。

全パス差分に加えて、`assets/`（原画・台帳・素材全体）、`scripts/`、`scenes/`、`data/`、`world/`、`tools/`、`test/`、`.scope-lock/`、`.github/`、`project.godot`、`addons/`、`AGENTS.md` のGit tree/blob IDが基準と対象で同一であることを照合した。本番、保護、検査条件・期待値・時間上限・警告検出に変更なし。原画の新しい目視解釈や採用の判定はしていない。

## 対象SHAのCIを直接確認

GitHub API `GET /repos/hiroshitanaka-creator/RPG-maker/actions/runs?head_sha=9c77969506510d95883bd7f8525637311bd09c45&per_page=100` と各runの `/jobs?per_page=100` を取得し、返却total_countと全件数、head_sha、event、branch、各jobの終了状態と結果を照合した。CLIの `gh auth status` はGH_TOKEN無効と表示されたため、利用可能なGitHub接続のread-only APIで取得に成功した。

対象SHAに紐づく6 run・全60ジョブが `completed / success`。失敗・cancelled・skipped・未終了ジョブは0件（2026-10-05 03:11 UTC確認）。008のpush/PRに加えて、024ブランチ作成時に同じ対象SHAで起動したpushも含めて全件確認した。

| ブランチ・契機 | workflow | run | 全ジョブ結果 |
| --- | --- | --- | --- |
| 024 / push | 006 固定受入と最新回帰 | [37257453002](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37257453002) | 17/17成功 |
| 024 / push | CI | [37257452980](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37257452980) | 3/3成功 |
| 008 / pull_request | 006 固定受入と最新回帰 | [37256276865](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37256276865) | 17/17成功 |
| 008 / pull_request | CI | [37256276912](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37256276912) | 3/3成功 |
| 008 / push | 006 固定受入と最新回帰 | [37256274037](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37256274037) | 17/17成功 |
| 008 / push | CI | [37256274046](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37256274046) | 3/3成功 |

通常CIの3ジョブは「素材検査」「試遊前の通常戦闘・案内・画面・復帰検査」「Godot・凍結受入テスト」。006の17ジョブは `lifecycle-audit`、`acceptance-and-regression (fixed/latest)` の2件、`normal-input-and-rendering (fixed/latest, journey/details/restart-0〜4)` の14件。各runで一覧の欠落がないことを確認。

008 pushの [Godot・凍結受入テスト job 111593932218](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37256274046/job/111593932218) の実ログを直接取得した。checkout SHAは対象9c779695…、Godotは `4.7.2.stable.official.ed1daf0bf`。全verify実行stepがsuccessで、以下の8行と検査前後の保護一致を確認。

```text
2026-10-05T02:40:27Z 保護対象26件、一致26件。
2026-10-05T02:41:32Z PASS R-01 (exit=0, tests_ran=True, parser_failed=False)
2026-10-05T02:41:40Z PASS R-02 (exit=0, tests_ran=True, parser_failed=False)
2026-10-05T02:41:42Z PASS R-03 (exit=0, tests_ran=True, parser_failed=False)
2026-10-05T02:41:45Z PASS R-04 (exit=0, tests_ran=True, parser_failed=False)
2026-10-05T02:41:47Z PASS R-05 (exit=0, tests_ran=True, parser_failed=False)
2026-10-05T02:41:49Z PASS R-06 (exit=0, tests_ran=True, parser_failed=False)
2026-10-05T02:42:49Z PASS R-07 (exit=0, tests_ran=True, parser_failed=False)
2026-10-05T02:43:01Z PASS R-08 (exit=0, tests_ran=True, parser_failed=False)
2026-10-05T02:52:40Z 保護対象26件、一致26件。
```

PR #14の [job 111593941222](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37256276912/job/111593941222) の実ログでもR-01〜R-08の8件PASSと検査前後26件一致を確認。PR側のcheckoutは `e8042e639a32428b177d11b8eded9d3767f5a3a7`（対象9c779695…を基準main86698d0…へ合わせたGitHubのmerge ref）であり、対象SHAそのもののcheckoutとは区別した。上記pushログが対象そのものの直接証拠。

追加の024ブランチ作成時pushについても [job 111597474357](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37257452980/job/111597474357) の実ログを取得し、R-01〜R-08の8件PASS（exit=0、tests_ran=True、parser_failed=False）と検査前02:58:49 UTC・検査後03:11:13 UTCの保護26件一致を直接確認した。

この節は008対象9c779695…の結果であり、024報告提出によって生じる別SHAのCI結果を先取りして成功とするものではない。

## 実行した照合と024の変更

- `git fetch origin codex/task-024-review-recorded-art` と `git switch -c codex/task-024-review-recorded-art FETCH_HEAD`：登録990c689…を取得して使用。開始時の未コミット変更0件、登録先端に対する未pushコミット0件。mainの追加統合は行っていない。
- `git diff --stat/--name-status` と4文書の全文差分：指定4文書だけ。
- Pythonによる固定SHAの `git show`・`git ls-tree`・`git rev-parse`、文字列比較、`hashlib.sha256`、台帳JSON照合：全項目PASS。既存決定3行の置換比較、指定決定2行・未決・履歴・注意、表13行（見出し込み）と注意3項目、対象外全文不変、11原画と報告hash、台帳未登録、各tree/blob不変をassertで検査した。照合スクリプトは `/tmp/review024.py` から実行（終了0）し、成果物は指定の報告内に集約した。
- `python tools/check_frozen_files.py`：終了0、保護対象26件、一致26件。
- `git diff --check 86698d0 9c77969`：終了0。
- `git diff --exit-code 9c77969506510d95883bd7f8525637311bd09c45 -- assets scripts scenes data world tools test .scope-lock .github project.godot addons AGENTS.md`：終了0。024作業場所も対象SHAと同一。
- 文書限定で本番・検査が同一のため、依頼どおりGodotのimportや全受入・回帰検査をローカルで重複実行していない。R-01〜R-08は上記対象SHAの実CIを証拠とし、今回のローカル実行と偽っていない。CIの再実行も要求していない。

024の成果物は、本報告 `docs/tasks/reports/024-review-recorded-art.md` と `docs/tasks/024-review-recorded-art.md` の状態行だけ。008依頼書・報告・設計文書・計画書を変更しない。追加委譲・後続発注・main統合は行っていない。

## 未確認と引継ぎ

- 栞の実装・総数・配置・交換内容・人物は今回の対象外。文書には未決・未実装注意が残っている。
- 1階の外入口とゲーム内接続、暗色敵を置いた戦闘画面の見えやすさは組込み段階の確認事項。今回、実装済み・検証済み・新たに採用済みとはしない。
- 008のmain統合と確認済み化は親担当が実施する。今回の照合に基づく本文修正要求、新規の仕様判断要求はない。
