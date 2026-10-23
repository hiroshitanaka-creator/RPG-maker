# 073 採用済み室内5枚をゲーム素材へ登録

- 状態：報告済み（クラウド登録・ローカル検証済み。親のGitHub保存・CI未実施）
- 担当：Codex（クラウド）
- 依頼日：2026-10-18
- 前提：2026-10-17の室内5枚の正式採用。親検収記録の固定commitは `d921bfff1339554eb4fe06930a9dc170ecaac98d`。
- ブランチ：`codex/task-073-register-adopted-room-images`
- 担当の場所：下記11ファイルだけ。
- 変えてはいけない場所：原画・既存素材・パレット・ゲームコード・地図・NPC・通行・物語・音楽・保護ファイル・その他の検査器・CI。`docs/decision-log.md` と `docs/tasks/README.md` は親担当。

## 目的

採用済みの宿・道具屋・武器屋・祠・防具屋の5PNGを、原バイトのまま素材として登録する。ゲームへの接続、荷受け所と城の登録は含めない。

## 背景

採用ZIPは `adopted-room5-2026-10-17.zip`、Library `libfile_7d30c41f2a60819198bf567516bde485`、851055 bytes、SHA-256 `25cab1603a081415699b87722d6211ce0b56da6932c02034c0f3dbb988b4aabf`。既に別工程で縮小・減色された5枚を扱い、今回再加工しない。詳細の期待値は `assets/source_records/region3-room-adoption-2026-10-17.json`。

読む契約は `AGENTS.md`、`.scope-lock/`、本フォルダREADMEとテンプレート、`docs/asset-spec.md`、`assets/registry.json`、関連原画記録。指定された `godot-dev-director` と `godot-game-verification` は実際の `.agents/skills` を探し、不在ならその事実を報告する。汎用スキルからGDScript・GUT・Autoloadを追加しない。

## 作業内容

1. 最新mainと番号競合、作業前の差分・未pushコミットを確認する。
2. 現在のLibrary手順で採用ZIPを取得し、ZIP・adoption.json・5PNGの原バイトと実表示を確認する。取得失敗時はconsumer-localの保存先で1回だけ再試行する。既往のLibrary取得失敗後、親が原ZIPをDrive `1FT2or3SgzWWZrazAEmjlEQME2rt74we-` に原バイト保全した。同じ公式Drive接続のinclude_base64を、既存callerがこの851055bytesの1件だけ明示選択したため、その標準読取りを使う。認証・共有・ネットワーク制限を変更しない。
3. Grokの実際の生成記録を照合する。生成日時・取得日時・ライセンス・指示を推測しない。2026-10-18 10:19 JSTの依頼者「Aで良いよ」に基づき、生成情報を捏造せず依頼者提供素材として扱う。
4. 次の11ファイル以内で登録する。
   - `assets/interiors/region3_room_inn.png`
   - `assets/interiors/region3_room_item_shop.png`
   - `assets/interiors/region3_room_weapon_shop.png`
   - `assets/interiors/region3_room_shrine.png`
   - `assets/interiors/region3_room_armor_shop.png`
   - `assets/registry.json`
   - `assets/source_records/region3-room-adoption-2026-10-17.json`
   - `tools/import_region3_adopted_rooms.py`
   - `tools/validate_assets.py`（承認された出所照合の限定拡張だけ）
   - 本依頼書
   - `docs/tasks/reports/073-register-adopted-room-images.md`
5. checkout外で5件の正例、対象外パス、正しいパスでhash不一致、欠落原画、既存必須欄と9月26日素材の保持を確認する。規定検証と独立照合を行い、差分・payload・manifest・生ログ・機械証拠をLibraryへ引き渡す。

## 守ること

PNGは448×384・RGBA8・alpha255、固定84色パレットの部分集合64色以下。再保存、生成、減色、拡大はしない。台帳既存1154件、audio、fonts、defaultsを保つ。従来の9月26日素材の扱いを維持し、`source=owner` に今回の原画5枚のoriginal_file完全パスと実ファイルSHA-256だけを追加許可する。10月4日フォルダ全体を許可しない。author・license・provided_at・modified・存在確認などの既存条件を維持する。生成日時・プロンプトは未確認のまま残し、取得日と取り違えない。

R-01〜R-08、3人・4人、順方向・逆方向を維持し、全ゲームの受入条件を縮小しない。066、MSI、認証変更、GitHub/Drive書込み、push、PR、mainマージは行わない。親が公式接続でGitHub保存を行い、その後のCIは別確認とする。この明示依頼に基づき、契約の通常のcommit/push手順は今回は行わない。

## 作業の前にしてほしいこと（計画）

報告書冒頭にmain完全SHA、競合検索、開始差分、台帳件数、スキル所在、入力取得・照合・出所確認・登録・検証の順を記録する。

## 作業の後にしてほしいこと（自己点検）

5PNGのhash・寸法・色・alpha、既存台帳項目の一致、原画不変、11ファイル以内、固定GodotのURL/hash/版、取り込み2方式、strict素材検査、R全件、凍結検査を確認する。終了コードに加え成功マーカーとSCRIPT ERROR・parse・leak・警告を監査する。入力不在時の既存main検査を登録後の成功と書かない。

## 報告

変更一覧、実行コマンド・結果、未達・未検証、入力阻害の原文、出所の不足欄、Libraryの確定ID/bytes/SHAと読戻し結果を報告する。採用ZIPを得られない場合は代替原画から再生成せず、そのままの入力を取得できる条件を具体的に残す。

## 完了の条件

5PNGが採用ZIPと完全一致し、台帳に5件だけ増え、出所が事実に基づき、規定検証・原画/既存台帳/変更範囲照合が成功すること。親の正式保存後にCIを確認する。クラウド作業での登録・検証成功と、親によるGitHub保存・CI・main反映を区別する。
