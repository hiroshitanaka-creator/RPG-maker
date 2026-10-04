# 005 Grokの原画18枚・用途記録の報告

## 作業前の確認と計画

- 取り込んだ最新main：`2b522b23c6a46dab7eb53b59a9433b89a9714dfa`。専用ブランチ`codex/task-005-record-grok-region3-images`をこのSHAから作成した。
- 004は「確認済み（技術確認完了・2026-10-04 04:56 UTCに依頼者が見た目を採用）」であり、前提を満たす。開始時の未コミット変更・未pushコミットは0件。
- `assets/_incoming/owner-2026-10-04-grok-region3/`の実体18枚と依頼書の18行を照合した。不足0件、余分0件。変更前にファイル名・場所・SHA-256を記録した。
- `AGENTS.md`、伝言板README、今回の依頼書、素材規約、職業・魔物化企画書、素材台帳（全体JSON解析）、付録Bと既存追記、固定検査実行器とCI定義を読んだ。
- 付録Bの末尾（既存表・説明の直後、2026年9月27日の決定の前）へ指定の節を追加する。対応表は依頼書からそのまま転記し、注意書き4項目を保持する。原画・コード・データ・検査・保護ファイルは変更しない。
- ローカル既定Godotは4.6.3だったため、CIに固定された4.7.2-stableを一時領域へ取得し、ZIPの固定SHA-256を照合して使用する。固定コミットから作る一時QAコピーでR検査を実行し、検査が生成する担当外の記録を提出ツリーへ書き戻さない。

## 追記した場所と変更ファイル

- `docs/roadmap-v2.md`の付録B末尾、既存の「職業の衣装」「魔物化」の説明直後に「付録B追記：Grok の原画（owner-2026-10-04-grok-region3）」を追加した。対応表18行は依頼書から無変更で転記し、注意書き4項目を記載した。付録Bの追加節を取り除いた既存本文は開始mainと全バイト一致する。
- `docs/tasks/005-record-grok-region3-images.md`は状態行だけを変更する。
- `docs/tasks/reports/005-record-grok-region3-images.md`は本報告書。許可3文書以外の差分は0件。
- 原画18枚の一覧を一時領域の確認用画像で目視照合した。依頼書の対応表との食い違いは認めなかった。確認用画像は原画の変更ではなく、一時領域にだけ作成した。ゲーム素材の生成・加工・登録は行っていない。

## 原画の不変確認

保管先は開始時・終了時とも`assets/_incoming/owner-2026-10-04-grok-region3/`。次の各SHA-256は変更前、作業後の実ファイル、開始mainのGit blob、提出コミットのGit blobですべて一致した。ファイル名・場所・件数も18件で一致し、不足・余分0件、変更・移動・改名0件。

| ファイル名 | 開始時・作業後共通のSHA-256 |
| --- | --- |
| `region3-fairy-enemies-4.png` | `873a63fe1a44b3fa0ac265158f5f2afc348001b3284e7cc3e275811444a74e70` |
| `region3-ice-lava-enemies-4.png` | `064792773d3e743404fec7f10d48fb44cc8e952d4e4c9dba599b1940ec3e211f` |
| `region3-ice-lava-enemies-alt.png` | `7bf092fb70cff5b3ee45f3cfb7538e0e18274deac62da060b5c441d137c91f64` |
| `region3-insect-enemies-4.png` | `becfdfa897102cf32b94093c72153a0605a4d5aa50aa1b7b056f762e98862a98` |
| `region3-killer-machine-spear.png` | `cdabe5ad8b43b94d16bd90cf9f23d34c0a2c03fa83edc3bedabd6bb8cfc35e94` |
| `region3-killer-machines-4.png` | `e718dbaa4ff542590791a062e0dfb28e3f9da2e05bf103f54af8524f29628f44` |
| `region3-killer-machines-extra-4.png` | `acecbb2dbf32349575ff003a35fe5e9e582f311954c1d649800278f1c5b27721` |
| `region3-port-exterior.png` | `36b93f2d68d5239ac503ff62d6c59c0a22a9667bcdc3b6dbeffbb1594bfa0bcd` |
| `region3-robot-enemies-4.png` | `c5169d23eb126b81ecf50a209187b26b075b19ce84774cb31cb2c938ab733c97` |
| `region3-snow-enemies-4.png` | `d1b1a9101148723abf17dbfffcbab1645c134563312e708ca8f96edb2d875a3e` |
| `region3-snow-enemies-extra-4.png` | `3750f62182eb12750e915b5397c2a22c94f3434daddae68ad426ca502e47f427` |
| `region3-volcano-enemies-4.png` | `8e787b0190f4eab4eeb26e013944ba4691aaf165360418a7875c4530b0ca4fba` |
| `region3-volcano-enemies-extra-4.png` | `efe60f419063dbb2d70f29787f2737a35234947b5e598eb781d6caac67a10634` |
| `region3-world-map-alt-a.png` | `495769b171adf3ba88fd5ba5fc4749dd67c0454d8606e248dad065d8645365c8` |
| `region3-world-map-alt-b.png` | `30d812e28f8dad699359f489aec0f61e9924dc65dd3288a085f7d2046fa5b454` |
| `region3-world-map-alt-c.png` | `36fc67837e3778ad45184477c46f82ed57ccec1f6b0c5d43acc8065d4e47c05b` |
| `region3-world-map-alt-d.png` | `0d740b0785fdb34663e48817971edf2508d9b8e63552e7e9b05228c211e83a4e` |
| `region3-world-map.png` | `2b4ad1ee3913d58b4fcad9cb82681a3518d50faeffe29b68292844993dbfce66` |

## 実行した検査

固定検査対象コミットは`1b408ef7a5bf9c97ac14cb2ffc87ba49053b1b10`。このコミットの`git archive`から一時QAコピーを作り、固定版Godotのimportを先に行ってからR検査を実行した。生成された`docs/verification/scope-lock-current.json`等は提出repoへ書き戻していない。比較用文書検査は開始mainと固定コミットを比較し、作業ツリーを比較対象にしていない。

| コマンド | 実結果 |
| --- | --- |
| `godot --version`（取得した固定版） | 終了0、`4.7.2.stable.official.ed1daf0bf`。ZIPのSHA-256はCI指定の`cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`と一致 |
| `godot --headless --editor --import --quit`（提出repo・一時QA） | 固定版・一時XDGディレクトリ指定で両方終了0。SCRIPT ERROR／ERROR／WARNING／Parse Errorは0行 |
| `python tools/run_locked_checks.py`（一時QA） | 終了0、R-01〜R-08全PASS。R-07個別A01〜A14と最終`FIRST_REGION_PASS: checks=14`が一致。R-08は17テスト・2302 assertions、failed/pending0 |
| `python tools/check_frozen_files.py`（提出repo・R後の一時QA） | 終了0、保護対象26件すべて一致 |
| `python tools/validate_assets.py --strict` | 終了0、画像1134件・音15件・字体2件・パレット3件。問題なし、不足素材なし |
| `python tools/check_progress_docs.py` | 終了0、`PROGRESS_DOCS: history=26 errors=0` |
| `python /tmp/grok005-verify.py 1b408ef7a5bf9c97ac14cb2ffc87ba49053b1b10` | 終了0、`GROK005_DOCS_PASS: rows=18 warnings=4 original_hashes=18 preserved=18 changed_files=3 out_of_scope=0`。表原文・注意書き・付録B以外の既存本文・状態行以外の依頼本文・原画の名前と全バイト・全ツリー変更範囲を検査 |
| `git diff --check`／`git diff --stat 2b522b2 1b408ef` | 終了0、許可3文書のみ。原画・ゲーム・検査・保護対象・CI・時間上限の差分0件 |

今回のR検査記録日時は`2026-10-04T06:17:46.441065+00:00`、契約SHA-256は`601a7452fe13be169d28327dfce1946b5a2ee2e7a1b1d8f92924d77dc95dedb3`。原ログとJSONは一時QAの`.tools/verification/current-20261004T061612Z/`と`docs/verification/scope-lock-current.json`に存在する。

環境調整と初回試行：既定Godotは4.6.3で、ユーザー用ディレクトリへの書込みも失敗した。この実行を成功証拠にしていない。4.7.2取得後の初回importもXDG_CONFIG_HOME未指定による設定保存エラーがあったため、XDG_CONFIG_HOME・XDG_CACHE_HOME・XDG_DATA_HOMEをすべて一時領域に指定して再実行し、エラー0を確認した。検査条件・時間上限・合否判定は変更していない。

専用リモートブランチには発注コミット`819efd2`が既にあった。初回pushのdry-runはfetch firstで拒否されたため、既存履歴を取得し、通常merge `e0336af`で保持した（開始mainとの実内容差分0）。強制push・削除・履歴変更はしていない。`gh auth status`はトークン無効、`gh api`はForbiddenだったため、CIの照会は接続済みGitHubコネクターの読み取りで行った。Gitの通常pushは成功した。

## CI・main反映

- 開始main：`2b522b23c6a46dab7eb53b59a9433b89a9714dfa`。本文・表の提出SHAと初回main統合SHAは`1b408ef7a5bf9c97ac14cb2ffc87ba49053b1b10`。
- 提出ブランチの[CI 37182278826](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37182278826)は、対象SHA・ブランチをAPIで照合し、全3ジョブの終了と成功を確認した（素材検査、Godot・凍結受入テスト、試遊前の通常戦闘・案内・画面・復帰検査、すべてcompleted/success）。
- 自走の許可の5条件（提出CI全3成功、今回のR全8成功、保護26件一致、検査の弱化・省略・時間延長0、依頼範囲内の3文書だけ）をすべて確認し、通常pushでmainを提出SHAへfast-forwardした。反映直前に最新mainが開始SHAのままであることと、mainが提出SHAの祖先であることを確認した。main統合済みであり、未統合の案として提出するものではない。
- main反映後に固定版Godotの`--headless --editor --import --quit`を先に実行して終了0・エラー警告0行、その後`check_frozen_files.py`で保護26件一致を確認した。
- 本報告書の最終記録と「報告済み」状態は、文書本文のコミットとは別の最終登録コミットにする。ゲーム・素材・契約・検査のGit blobがR検査対象と同一であることを確認し、固定SHAの文書・原画検査も最終コミットへ再実行する。最終登録も提出CI全ジョブ成功を確認してからmainへ反映し、mainのCI全ジョブの終了まで確認する。最終登録コミット自身のSHAと提出・mainのCI URL・結果は、この本文へ自己参照するSHAを埋めず、Git履歴と親タスクへの最終通知で識別する。開始mainの過去の成功を今回の成功に置き換えない。

## 自己点検

| 項目 | 確認結果 |
| --- | --- |
| 1. 対応表と注意書き | 表18行の全テキストは依頼書と完全一致、注意書き4項目を保持。第2地方2枚・機械敵2枚の未決事項を明記 |
| 2. 原画の不変 | 原画18件の名前・場所・実体とGit blobのSHA-256が開始時と一致。変更・移動・改名0件 |
| 3. 担当外の不変 | 開始mainと提出SHAの全パス比較は許可3文書だけ。付録B以外のロードマップ全文と状態行以外の依頼本文は全バイト一致。コード・データ・素材・検査・保護・CIの差分0件 |
| 4. 検査とCI | 今回のR-01〜R-08すべてPASS、保護26件一致、提出SHAのCI全3ジョブcompleted/success。最終登録とmainのCIは上記の最終通知で対象SHAごとに記録する |

## 未達・未検証・判断事項

この文書作業の原画対応表・注意書きについて未達はない。建物の中4部屋の描き方の採否、機械の敵のゲーム内の名前と配置は依頼書どおり未決として残した。今回それらを決めず、原画の取り込み・人物や敵の実装・本番素材化には進んでいない。新しい判断や追加承認はこの作業には不要。指揮役による実物確認は別であり、依頼書は「確認済み」にせず「報告済み」とする。
