# 062 第3地方の城と飛行船の採用原画保管・記録

- 状態：未着手
- 依頼日：2026-10-10 JST
- 担当：Codexが原画保管・記録・検証・PR作成、ルッカが依頼/受入/最終マージ
- 基点：main 87f4e66ed64f2ae9a92538acb9716c6a01f5cb27
- ブランチ：codex/task-062-record-region3-castle-art
- 許可：ユーザーの2026-10-10 09:19 JSTの具体依頼 Sentinel_53ac59dad1ac8191a54a5c1ed62a9e44。採用5枚・記録・1PR・全条件成立後main取込。ゲームへの組込みなし。
- 実行場所：接続検証済みMSIのローカルCodex環境、GPT-6 Astra／High。使用量影響不明。
- 他作業：060終了、061は別branchのみ存在し未登録/未発注。現在他Codex稼働なし。保存修正系列を本branchに取り込まない。

## 目的・前提
第3地方の城（節目9「飛行手段」）を後で作るための採用原画5枚を1バイトも変えずに保存し、原画の場所・中身・用途・採否を記録する。依頼者がGrokで制作し、Claudeが内容を確認、依頼者が2026-10-10採用した。採否を再質問しない。AGENTS.md、docs/asset-spec.md、docs/tasks/README.md、docs/roadmap-v2.md付録B追記の既存形式を読む。_incomingは原画保管の検査対象外で、本番素材化・台帳追加は今回は行わない。

## 全変更予定ファイル
- assets/_incoming/owner-2026-10-10-grok-region3-castle/region3-castle-exterior.png
- assets/_incoming/owner-2026-10-10-grok-region3-castle/region3-castle-great-hall.png
- assets/_incoming/owner-2026-10-10-grok-region3-castle/region3-castle-throne-room.png
- assets/_incoming/owner-2026-10-10-grok-region3-castle/airship-views-3.png
- assets/_incoming/owner-2026-10-10-grok-region3-castle/region3-castle-airship-dock.png
- docs/roadmap-v2.md：既存付録B追記と同形式の新節のみ
- docs/tasks/062-record-region3-castle-art.md：状態行のみ
- docs/tasks/reports/062-record-region3-castle-art.md：新規報告
親だけが扱う記録：docs/tasks/README.md、docs/decision-log.md。Codexはこの2ファイルを編集しない。ほかの新規/既存ファイル、registry、CI、project.godot、保護検査は変更しない。検証ログは報告へコマンド/結果/原CI参照を記録し、未列挙の追跡ファイルは追加しない。

## 採用する原画
保管先：assets/_incoming/owner-2026-10-10-grok-region3-castle/

| branch | 指定commit接頭辞 | ファイル | SHA-256 | bytes | 内容 |
|---|---|---|---|---:|---|
| incoming/owner-2026-10-10-grok-region3-castle | 7cacdc7 | region3-castle-exterior.png | d3f08bd5e3433848fe2d606175646605b083ac3e521c123a74fa45d566e2dcef | 3659721 | 第3地方の城の外観。下の端の中央に石の門柱の出口、中央の前庭に火を灯した石の火鉢、上半分の中央に本館と両開きの大扉、右側に飛行船の修理場の建物と大きな両開きの扉、左上の遠くに煙を上げる火山 |
| incoming/owner-2026-10-10-grok-region3-great-hall | 7532907 | region3-castle-great-hall.png | ff94696daeab01d2b39a9d5a8151942c9bd933017e2e5596ef43bc8c58765c7a | 1224589 | 城の大広間。下の真ん中と上の真ん中に両開きの扉、中央に赤い敷物、左右に柱3本ずつ、四隅に火鉢 |
| incoming/owner-2026-10-10-grok-region3-throne-room-redo | 6e029a2 | region3-castle-throne-room.png | 5f91e573956a5b4a60346e5635447657768f3eec829428a2c616e5aec8aa0bb2 | 2150096 | 城の謁見の間（描き直し版）。下の真ん中に両開きの扉、奥の中央に段の上の空の玉座、扉から玉座へ赤い敷物、左右に柱2本ずつ、奥の窓に火山と雪の山 |
| incoming/owner-2026-10-10-grok-region3-airship | a90cf65 | airship-views-3.png | a639308b9bc604c57a0c93b3f110fb27c63c8ddabe728e71f033cdf75193e1dc | 724105 | 飛行船の3つの姿を1枚に並べた絵。左から、真横から見た修理後の姿（船首が右）、真上から見た修理後の姿（船首が上）、真上から見た修理前の壊れた姿（船首が上） |
| incoming/owner-2026-10-10-grok-region3-airship-dock | da43302 | region3-castle-airship-dock.png | 5a25389151fb579ad667cdd4e8bbaea269daaa8c293198a521ba185eda3157bf | 1367119 | 飛行船の修理場（船は描いていない）。下の真ん中に大きな両開きの扉、中央に船を置く空いた床と木の台座4本、奥に天窓、左に炉・金床・作業台、右に木材・布・ロープ・道具棚 |

## 不採用
incoming/owner-2026-10-10-grok-region3-throne-room、commit570fb98、同名region3-castle-throne-room.png、SHA-256 dbb82458d251907eb83f842660013cbef57ea01c4db50f146a902208ad863b4a。絶対に本branch/mainへ入れない。branch削除・上書き・改変もしない。報告に不採用・未取り込みと記す。

## 作業前の計画
1. 6incomingのorigin refを取得し、完全SHAと各親との差分を記録。親側読取りでは全6本とも上記mainを単一親とし、指定folderのPNG1枚追加のみと確認済み。作業環境でも照合し、不一致なら止まる。短いSHAだけで取り違えない。
2. 採用5枚と不採用1枚のbranch/完全commit/blobを列挙。PNG実bytesを取得してSHA256とbytes数を照合、採用5枚の実画素も閲覧して記述に矛盾がないか確認。未閲覧を閲覧済みとしない。差があれば原画は変更せず報告する。
3. docs/roadmap-v2.md の「付録B追記：4体の主の原画（owner-2026-10-05-grok-batch4）」を形式例として確認。
4. 変更予定全8ファイルを報告冒頭に列挙。未コミット/未pushの既存変更を確認し、無関係なファイルやコミットは触れず、pushしない。

## 実行
採用5枚だけを元Git blobそのままで保管する。5incomingは1枚追加だけなので、親差分確認済みcommitの取込みまたは固定commitから指定パスのみ取得する。原画の切抜き・縮小・色調整・再保存・改名なし。_incomingがgitignore対象のため必要ならgit add -fで指定5パスだけ追加する。旧版は同名のため、最後まで採用版hashで照合する。
roadmapの新付録B節に5パス・branch・完全SHA・SHA256・bytes・上記内容を記録。用途は外観/大広間/謁見/修理場が一枚絵背景の原画、飛行船3姿が世界マップの飛行船と修理場へ重ねる修理前/後の動く絵の元。修理場背景に船はなく別絵を重ねる前提。
部屋接続の原画依頼時想定は外観本館の扉→大広間、大広間奥の扉→謁見の間、外観右の大扉→修理場。扉は上/下の壁。これは将来実装ではなく原画依頼の想定記録。
依頼者2026-10-10採用、謁見redo採用/570fb98不採用、未決の城の人々の役割・見た目と飛行船修理場面の細部を記録。物語・人物・地名・新規則を新しく決めない。
1本のdraft PRをmainへ作成する。Codexはマージしない。親がPR最終確認・親担当記録を加え、最終全CI成功を確認して通常マージする。

## 検証・自己点検
- 5枚すべて指定SHA256/bytesと完全一致、謁見は5f91e573...a0bb2、旧dbb82458...863b4aでない。
- 指定folderの追跡ファイルは5枚だけ。他の5枚以外があれば勝手に削除せず報告。
- 記録の5枚内容/用途/接続想定/採否/未決を全件照合。
- Godot --headless --editor --import --quit、素材strict、R-01〜R-08、check_frozen_files.py等の既存手順を実行。予算・検査条件不変。既存Godot/許可済み実行体が使えなければ具体阻害点を報告、OS設定変更や無承認インストールをしない。
- push/PRの最新head全CI全job終了・成功を直接確認し、過去版成功で代用しない。CI失敗時は範囲内で原因調査し、範囲外修正/検査弱化/削除/強制pushなし。
- 旧謁見branchが元SHAのまま存在していることを確認。
- 画像未組込み、本番code/部屋data/通行map/registry/原画加工/保護変更なし。

## 報告・出口
5枚の各hash/bytes実測表、原画閲覧結果、変更一覧、roadmap節、実コマンド/CI結果、PR URL、最終commit、clean/未push、旧版branch保持、未達/未検証を日本語で報告。重大な物語詳細は書かない。作業branchへcommit/pushし、親の受入へ返す。main取込後の5枚hash/bytes・folder件数・記録・全CI・旧branchの最終点検は親が行う。
