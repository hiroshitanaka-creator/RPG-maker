# 084 採用済み遺跡の入口と帰路接続 実装計画

- 状態：発注準備。実行受付は別記録。
- 担当：Codex GPT-6.1 Sol / High。ルッカは採否・依頼書・親受入・親記録・通常マージ。
- 依頼日：2026-10-29 JST。
- 基点：RPG-maker main f9169ac4048e98229d34692bc1e9efb6a0a3efaf。082/083は正式完了、最終38CI/R01〜08/保護26前後一致確認済み。
- 作業ブランチ：codex/task-084-region2-ruins-connection-20261029。main直接書込み・マージは担当範囲外。draft PRまで。
- 084番号はmain docs/tasks、README、STATUS、枝一覧に未使用を2026-10-28 20:50UTC確認。今回は1本のみ。共有の移動系と生成器に関わるため他実装と並列にしない。

## Goal / Architecture / Tech Stack / Spec
Goal：既存の採用済み4階の場所へ、主要会話完了後に世界から入場し、通常操作で元の島へ戻れるようにする。
Architecture：既存FirstRegion移動・Region2Ruins階段・GameSession保存/会話排他を再利用。新フラグ・保存形式・イベント本文は作らない。入口判定はRegion2ShrineStory.COMPLETE_FLAG（region2_shrine_seen）のみ。
Tech Stack：Godot 4.7.2-stable / GDScript / 既存Python生成器。内部512×288、32pxタイル。
Spec：本人I-20261028-011（1.A改行2.A）とI-20261028-012（進めて下さい）。既存島内で往復可能な入口位置をルッカが選び、主要会話終了後のみ入場、まず入口/帰路だけ。未決台詞・鍵・戦闘内容は追加しない。
実装担当は superpowers:executing-plans、test-driven-development、verification-before-completion を利用できれば本文を読み、計画を順に実施する。スキル不在ならその事実を報告し既存検証手順を守る。

## 読むもの
AGENTS.md、docs/experience-spec-v2.md、docs/asset-spec.md、assets/registry.json、.scope-lock/spec.lock.json（読取のみ）、011正式依頼/報告と固定・最新回帰、082/083正式報告、S10会話完了フラグ、今回の対象ソース。
親の準備資料：lucca-workspace / lucca/rpg-handoff-080-20261027 / projects/rpg-maker/drafts/region2-story-connection-preparation-2026-10-14.md の最新追記。準備中の旧「未採用」は今回I011採用で解消。旧互換Aは082が充足済みで、追加移行しない。

## 技術配置
- 世界入口 [176,91]、世界帰着 [176,92]、帰着向き下。
- 1階入場着地 [18,19]、向き北。出口接触 [18,20]。
- これらは現mainの歩行床。内部 [17,21]/[18,21]/[19,21] は壁なので使わない。壁・床・上層・既存階段・旧保存補正spawn[18,5]を変更しない。
- 世界の村169,88・港169,98・浅瀬156,109と非重複。帰着から入口/既存村港入口を避けた歩行帰路があることを独立BFSで検証する。
- 未完了時も入口座標の世界床は通常通行可。region2_shrine_seen未完了なら内部へ遷移しない。完了後の通常移動で入場。monster_jobs_unlockedや職業権は代用しない。
- 旧内部保存はS10未完了でも従来どおり読めて退場できる。入場制限を内部保存のvalid拒否へ拡張しない。
- 内部階段4階往復、既存world遭遇率0.025を保持。内部encounters_enabled/boss_enabledはfalseのまま。無遭遇の世界帰路とは報告しない。
- FirstRegionAtlasで内部を第1村へ誤表示しないよう既存siteへの対応を加える。名称は既存データのみ、新名称なし。
- 採用済み画像・既存入口表現を再利用し、新しい場所の外観や画像を創作しない。素材が適合しない場合は実画素と理由を親へ報告し、見た目を勝手に採用しない。

## 変更予定全ファイル
本番/生成器：
1. scripts/world/first_region.gd
2. scripts/world/region2_ruins.gd
3. scripts/world/first_region_view.gd
4. scripts/ui/first_region_atlas.gd
5. world/region2_ruins.json
6. tools/task011_ruins_defs.py
7. tools/build_task011_ruins.py
新規集中検証/撮影：
8. tools/check_region2_ruins_connection.gd
9. tools/check_region2_ruins_connection.gd.uid
10. tools/check_region2_ruins_connection.py
11. tools/capture_region2_ruins_connection.gd
12. tools/capture_region2_ruins_connection.gd.uid
依頼・報告：
13. docs/tasks/084-region2-ruins-connection.md（この全文の写し、状態以外の意味変更なし）
14. docs/tasks/reports/084-report.md
証拠：
15. docs/verification/task-084/commands.json
16. docs/verification/task-084/checks.json
17. docs/verification/task-084/manifest.json
18. docs/verification/task-084/input-trace.json
19. docs/verification/task-084/before-complete.png
20. docs/verification/task-084/after-complete-entry.png
21. docs/verification/task-084/interior-return.png
22. docs/verification/task-084/loaded-return.png
23. docs/verification/task-084/logs/（実行コマンドごとの原ログ。開始前に具体名を報告へ列挙）
検証証拠の追加画像/logは同フォルダに限る。予定外の本番・検査既存pathが必要なら理由を親へ報告して照合する。
Codexは docs/tasks/README.md と docs/decision-log.md を変更しない。親が受入後に逐次記録する。

## 禁止・保持
.scope-lock/、test/、保護検査、CI設定、project.godot、assets/registry.json、原画/パレット/画像、保存形式、082本文と採用人物配置は変更禁止。
GameSession/FirstRegionTravel/terrain/沿岸dataは変更不要の見込み。必要性が判明したら親へ照合する。
別site breakwater_ruins[242,39]は流用しない。旧011のMAPS/LINKS/部屋/階段/画像生成算法を保持。defs/builder/JSONは後続接続メタデータの整合だけ。
削除・force push・履歴改変・検査の省略/弱体化/上限延長なし。既存の段階固定assertionは当時完成SHAで全保持、最新継続条件と新正負例を分ける。

## Task 1：入口・帰路と保存の集中検証
- [ ] 新規検証を先に作り、現mainで入口未接続の失敗を確認して原ログ保存。
- [ ] 未完了/会話途中は入口床を歩けるが内部へ入らない。S10完了後のみ通常移動で内部着地し、セル・向きが上記と一致。
- [ ] 入口上の旧世界保存は拒否/消失しない。完了状態のロード直後に勝手な二重入場を起こさない。
- [ ] 内部出口を通常移動で踏むと世界帰着へ戻り、連打・入力保持で即再入場/二重遷移しない。
- [ ] S10未完了の旧内部保存もロード・退場可。旧spawn補正と内部階段往復を保持。
- [ ] 世界/内部/帰着前後の通常保存・ロード・checkpointで位置/向き/entry_lock・所持品/編成/職業/進行を照合。新しい完了・報酬フラグを補完しない。
- [ ] 既存FirstRegion/Region2Ruins経路に最小接続を実装し、新規検証を成功させる。既存会話排他をバイパスしない。

## Task 2：生成再現と描画
- [ ] defs/builderから接続メタデータが再生成されるよう整合し、一時出力で2回生成して全bytes一致を確認。
- [ ] 旧MAPS/LINKSと画像生成コード・原画像/既存派生/台帳は不変を確認。検査のために生成した無関係差分をcommitしない。
- [ ] 採用済み1階背景を担当環境で実際に閲覧し、内部着地/出口が足元として成立するか確認。親のJSON床確認を画像実見の代用にしない。
- [ ] 512×288実Godotで未完了入口通過、完了後入場、内部から世界帰着、保存復帰を実キー操作で撮影しinput traceを保存。静的合成を実ゲーム証拠にしない。
- [ ] Atlas現在地が実siteと一致することを検査し、既存村/港/第1地方表示を回帰確認。

## Task 3：回帰・正式保存
- [ ] main取り込み後に godot --headless --editor --import --quit を実行し、実コマンド/exitを保存。
- [ ] python tools/check_frozen_files.py を作業前後で実行。保護26の不変、python tools/validate_assets.py --strict、011最新回帰、082/083関連回帰、新規084検査、R01〜R08を実行。
- [ ] 011固定完成版検査は既存CI方式の完全SHAを保持。新接続に影響する旧assertionを当時限定/最新継続/後続置換に分類し、元assertionを削除せず対応表へ記録。保護/CI変更が必要なら依存部分だけ止めて証拠を報告。
- [ ] 全変更pathを予定一覧と比較、未commit/未pushを前後列挙。日本語commit/push、draft PRを作成し、最終HEADの全CIジョブ終了まで確認。
- [ ] 正式084報告にSHA/PR/原ログ/実行した条件数/失敗と未実行/画像参照/判断と戻し方を保存。mainマージしない。

## Review Focus
- S10未完了の旧世界入口座標/旧内部保存を壊さない。
- 同じ入口に連続入力して二重遷移しない。
- 会話中の移動・古い画面の入力で入場条件を飛ばさない。
- 再生成で接続を消さず、既存画像や階段へ副作用を出さない。
- 内部の現在地表示と保存復帰が第1村へ混線しない。
各項目を上の集中検証で正負例として検証する。主観の手触りは機械合格と分離し、未実施を明記する。

## 完了条件
依頼範囲の往復接続、前後の保存互換、既存全条件と新規正負例、実Godot画面、最終HEAD全CI/R8/保護不変、正式commit/push/draft PR/報告が揃う。083再実装やゲーム全体完成とは報告しない。
