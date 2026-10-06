# 014 4体の主：原画保管と文書記録の作業報告

## 作業前に確認した3点

1. 最新mainは `3078f061926f5e74eae7d08a8807d3bff92666b6`。作業ブランチの開始SHAは `450a449291954a2d0bd376f8d5dcfd2b375493ab`。履歴を保った通常mergeでmainを取り込み、mergeコミットは `8639651b330776ae6304fc778f3d6c57b0592983`（親は開始SHAと最新main）。競合した015の状態行はmainの「確認済み」を採用。取り込み直後のツリーは最新mainと完全一致。古い文書へ戻していない。
2. 指定4ブランチを個別にfetchし、各ブランチの対象ファイルを `git show <ref>:<path>` で実バイトとして取得。4枚とも014記載のSHA-256と一致。作業前と保管後の両方で照合した。取得元の完全SHA・パス・SHA-256は次表に記録する。
3. mainの `docs/design/monster-job-unlock.md` は存在する。015・030はともに「確認済み」。014開始前に「状態：作業中」の他依頼書はない。作業前の未コミット変更なし、作業前から存在した固有2コミットは014/015依頼書の過去の登録だけ。

## 原画4枚の取得元と保管結果

依頼者がGrokで作成・採用した原画を同じパスへ無加工保管。鳥の主がつかむ凍った岩、竜の主が立つ宙に浮いた岩は原画の採用形のまま保持した。ゲーム用画像への変換は行わない。`assets/_incoming/` は既存規約で検査対象外の原画保管先であり、素材台帳・パレットは変更しない。

| 原画 | 取得ブランチ | 取得元SHA | 保管パス | SHA-256 | バイト数 | 結果 |
| --- | --- | --- | --- | --- | --- | --- |
| 不死の主（ジーク） | `assets/owner-2026-10-05-grok-batch4-undead` | `fcd32182011d03bcb44e81f586325d48d95c8250` | `assets/_incoming/owner-2026-10-05-grok-batch4/optional-boss-undead.png` | `30e4cee201f6391241afe505b7a522f3c890040ab1bfaa1eb68a9a41954a9a9a` | 1572477 | 一致 |
| 鳥の主 | `assets/owner-2026-10-05-grok-batch4-bird` | `0e0cf94271b639811ae27a3844e9a03c210737c1` | `assets/_incoming/owner-2026-10-05-grok-batch4/optional-boss-bird.png` | `e25df4ce5bb7879ed58786671b853a4bbf1b7c8df61254b1ab0db258ba04e8cd` | 1747452 | 一致 |
| 精霊の主 | `assets/owner-2026-10-05-grok-batch4-spirit` | `53b98f0f97a81408a59b47972e9678adbcaab808` | `assets/_incoming/owner-2026-10-05-grok-batch4/optional-boss-spirit.png` | `02b05a0888df699489b1ebc8bf61a89c8a565721622ad65974ce83c154c16339` | 1739572 | 一致 |
| 竜の主 | `assets/owner-2026-10-05-grok-batch4-dragon` | `151919f57041fb70d193e394518df731e22dcbe8` | `assets/_incoming/owner-2026-10-05-grok-batch4/optional-boss-dragon.png` | `11139fec646f6a75d233e2f188a25306656a3fea6281dcee953a6b60f40ff562` | 1830645 | 一致 |

## 変更したファイルと箇所

- 上表の `assets/_incoming/owner-2026-10-05-grok-batch4/optional-boss-{undead,bird,spirit,dragon}.png`：4枚を `git add -f` で追加。
- `docs/design/monster-job-unlock.md`：主の節へ依頼者の「主の呼び名の決め方」「不死の主『ジーク』」を見出しと本文とも原文のまま追加。Claudeの呼び名を「Claude の仮の案（未決）」と明記し、4原画のパス・SHA-256を記録。015登録時の未決一覧を削らず、014で決まった事項と現在の未決を追記で区別した。
- `docs/roadmap-v2.md`：付録Bの末尾に指定見出し「付録B追記：4体の主の原画（owner-2026-10-05-grok-batch4）」を追加。4原画の取得ブランチ・パス・SHA-256、岩を含む採用形を記録。
- `docs/experience-spec-v2.md`：変更は「未決事項」の物語・世界だけ。「主の名前、見た目、強さ」を居場所の呼び名と強さへ整理し、本当の名前と採用原画は決定済みと記録。名前が分かる場面の流れ・台詞・腕輪か巻物かを未決に追加。既存の主との戦いの実装時期は重複させず保持。
- `docs/tasks/014-record-four-lords.md`：状態行だけを変更。本文はmainと完全一致。
- `docs/tasks/reports/014-record-four-lords.md`：本報告。変更は合計9ファイル。

## 実行した検査と結果

- Godot公式4.7.2-stableをCIと同じURLから `/tmp/task014-godot/` へ取得。zip SHA-256は `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` で既存CIと一致。実行版は `4.7.2.stable.official.ed1daf0bf`。既定の4.6.3は本検証には使用していない。
- `timeout 600 godot --headless --editor --import --quit`：main取り込み後・原画追加後・隔離checkoutの3回とも終了0。各ログに `SCRIPT ERROR|ERROR:|WARNING:|Parse Error` なし。XDGのcache/data/configを `/tmp/task014-xdg/` に置き、環境の書込み可能な場所へ一時状態を分離。
- `python tools/validate_assets.py --strict`：終了0、画像1154件・音15件・パレット3件・字体2件、問題なし。
- `python tools/check_frozen_files.py`：終了0、保護対象26件・一致26件。
- Pythonによる原文照合：依頼書の決定2節が主の文書に完全一致。014依頼書は状態行以外が最新mainと完全一致。4原画の実バイト・両文書のパスとSHA-256を照合して一致。
- `git diff --exit-code origin/main -- <担当外のパス>`：終了0。既存原画347件、ゲーム・データ・素材・検査・契約・旧進捗文書・015/030の状態は不変。R-01〜R-08を実行する隔離checkout `/tmp/task014-check` と、担当外の関連追跡ファイル2280件を全バイト照合して一致。
- `git diff --check`：終了0。検査・条件・時間上限は変更しない。原画のブランチ自体はmergeせず、指定ファイルの実バイトだけを取得した。
- `PATH=/tmp/task014-godot/bin:$PATH python tools/run_locked_checks.py`：隔離checkoutで既存のverifyと判定をそのまま実行。各300秒上限を保持。結果は下表。原記録のSHA-256は `a77b8e543b56061c731beeaec149b38c06c34257eb3c2be1dc2ea9776a92ad0d`。原記録・生ログは隔離checkoutに保持し、許可外の文書へ追加しない。

| 要件 | 結果・終了コード | 実行証拠 |
| --- | --- | --- |
| R-01 | PASS・0 | 2テスト・765assertion、失敗0・pending 0・invalid false |
| R-02 | PASS・0 | 5テスト・946assertion、失敗0・pending 0・invalid false |
| R-03 | PASS・0 | 2テスト・73assertion、失敗0・pending 0・invalid false |
| R-04 | PASS・0 | 1テスト・293assertion、失敗0・pending 0・invalid false |
| R-05 | PASS・0 | 2テスト・79assertion、失敗0・pending 0・invalid false |
| R-06 | PASS・0 | 2テスト・87assertion、失敗0・pending 0・invalid false |
| R-07 | PASS・0 | A01〜A14 PASS、FIRST_REGION_PASS: checks=14 |
| R-08 | PASS・0 | 17テスト・2302assertion、失敗0・pending 0・invalid false |

## CIと提出状態

- 最新mainを取り込んだ作業ブランチで独立レビューへ提出する。mainへの直接書込み・mainへのマージは行わない。
- CIはこれからpush・draft PRで起動し、全ジョブの終了後にURLと実際の結果を追記する。終了前の検査は成功とは扱わない。

## 自己点検と未達・未検証

1. 原画4枚：作業ブランチの実バイトは014のSHA-256と一致。mainへの保管は今回の指示により未実施。
2. 決定本文：呼び名の決め方と人物の記録は原文一致。Claudeの案は未決と明記。
3. 付録B：4枚の原画と岩を含む採用形の記録あり。
4. 未決事項：決定済みの本当の名前と原画を外し、居場所の呼び名・名前が分かる場面・強さ・戦いの時期を保持。戦いの時期の重複なし。
5. 範囲：指定9ファイルだけ。既存原画・コード・データ・台帳・パレット・検査・保護ファイル・他依頼書/報告書は不変。旧 `docs/STATUS.md` と `docs/director-next-preparation.md` は更新しない。031・PR #15の原画・追加委譲の作業なし。
6. R-01〜R-08・保護26件・CI：上の実測結果に従う。CI全ジョブの終了は待機中。

ゲームへの配置・戦闘・台詞・解放の実装は今回の対象外。依頼書の「mainに入り」の条件は、今回の独立レビュー提出・main未統合の指示により未達として明示する。新しい作品上の判断や追加の許可は求めない。
