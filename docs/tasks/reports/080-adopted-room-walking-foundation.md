# 080 採用済み5室の歩行基盤

## 作業前の範囲・依存・全変更予定

基点・確認した最新main：e677896d3e61b8fe8136ef60c5c76f41ad76701d。未commit変更0件。
073素材参照SHA：84f446e48cbaef2a199da1d464311992daf13938。PR49はmergeしない。
2026-10-21 02:58 UTCの制作承認に基づく実装・検証。正式Git保存・全CI・main操作は親担当。

変更予定（実装前に列挙）：
- assets/interiors/region3_room_inn.png
- assets/interiors/region3_room_item_shop.png
- assets/interiors/region3_room_weapon_shop.png
- assets/interiors/region3_room_shrine.png
- assets/interiors/region3_room_armor_shop.png
- assets/source_records/region3-room-adoption-2026-10-17.json
- assets/registry.json（上の5件だけ073から登録）
- world/adopted_room_foundation.json（5室の通行・既存overlay切出し座標）
- tools/adopted_room_foundation.gd（本番GameRoot継承の開発起動口）と対応.uid
- tools/adopted_room_foundation.tscn（直接起動scene）
- tools/check_adopted_room_foundation.gd（追加入力・描画検査）と対応.uid
- tools/check_adopted_room_foundation.py（独立データ・保全検査）
- docs/tasks/reports/080-adopted-room-walking-foundation.md（本書）
- docs/verification/task-080/ に今回のログ・JSON・通常描画PNG・再現記録を保存（全ファイル名は最終manifestで列挙）。

依存：既存GameRootの方向キー/WASD入力、WorldMovement、GameSession.move_first_region、FirstRegion.move/walkable/place、FirstRegionViewの背景・足元順overlayを再利用する。開発sceneを直接起動したプロセスだけに室内・入口往復データを登録し、通常main scene・保存schema・物語接続は変更しない。開発用入口確認領域は同じ採用画像の敷居だけを使い、新しい場所・施設・地名を創作しない。

保護/test/CI/既存検査・親台帳・原画は変更しない。PR49の出所検査変更なしでは登録5件のowner原画配置を現行strictが拒否する依存を確認した。その検査を変えず実測し、未解消事項として残す。独立実装を続ける。

005用途表の実内容（宿＝旧port-exterior、道具＝旧killer-machines-extra-4、武器＝旧world-map-alt-c、祠＝旧world-map-alt-d）と073出所記録を照合。防具屋は005の4室に含まれず、073の別原画・採用記録を出典とする。採用5PNGをそれぞれ原寸で表示し、宿のベッド3台・暖炉・右受付、道具屋の瓶/薬草棚・手前台、武器屋の炉/金床/武器棚・中央台、祠の祭壇/火皿/敷物、防具屋の盾/兜/鎧展示を確認した。448×384原bytesを保持する。

## 結果

5室の歩行実装候補とローカル検証を用意した。初回の素材strict阻害は2026-10-21 03:49:55 UTCの限定承認に基づく変更で解消し、1159件成功を再実測した。詳細は末尾の限定承認・最終実測を参照。全ゲーム完成・本番進行接続・正式GitHub保存完了とは扱わない。

## 実装した境界

追加sceneを `godot --path . tools/adopted_room_foundation.tscn -- --room=inn` で直接起動する。
`--room` は `inn`, `item_shop`, `weapon_shop`, `shrine`, `armor_shop`。1〜5で同じ順に室を選択、矢印/WASDで歩行、Escで終了。不明ID（荷受け所を含む）は終了2で拒否する。画面に「開発用・歩行基盤」を常時表示する。

本番GameRootを継承し、方向キーの `_input`、`submit_player_action`、`_first_region_action`、WorldMovementの時間進行、GameSession/FirstRegionの通行・隣接・door処理、FirstRegionViewをそのまま呼ぶ。開始位置の設定と各室の選択は開発用配置であり、世界から自然到達した証拠にはしない。歩行検査はその配置後にInputEventKeyを送り、直接座標書換えやmove APIで巡回を代替していない。

室内は14×12、32pxタイル。家具の地面側を通行禁止にし、上に立ち上がった部分を元PNGの矩形参照で足元順に再描画する。PNGの切出し素材・塗替え・生成・再保存はない。通行は足元、視覚は既存の32×48歩行スプライトと既存の補間表示を使用する。前壁の手前描画と入口の上梁も同じ元PNGを参照する。最下段の敷居を踏むと、同じ画像の敷居だけを歩ける開発用入口確認領域へ移る。上入力で既存door処理を通って同室へ戻る。これは外の町・世界・新しい物語上の場所ではない。

通常main scene・GameRoot・GameSession・FirstRegion・FirstRegionPresentation・FirstRegionView・world/interiors.json・既存世界定義は無変更。起動した開発sceneだけがstaticキャッシュへ5室を追加し、終了時に元のキャッシュを復元する。本番の保存妥当性検査は開発用node IDを拒否し続ける。開発起動はセーブ/会話/販売操作を提供せず、通常のゲーム記録も開始しない。独立した既存GameSessionの全状態が変わらないことと、その通常保存の全状態往復を各室で検査する。

地名・住人・台詞・商品・進行条件・世界接続・物語イベントは追加していない。表示する宿屋等の語は採用画像の用途ラベルであり、新しい地名ではない。荷受け所・城・他地方の制作は行っていない。

## 検証方法と失敗の扱い

- `check_adopted_room_foundation.py` は画像の固定SHA、5用途の識別、目視で選んだ床/家具の固定座標、全床と入口の連結を独立検査する。不足室・画像重複・家具通過・入口閉鎖・未承認接続を注入した負例を拒否する。既存台帳項目、基点に存在するコード/データ/文書/検査の不変も確認する。
- `check_adopted_room_foundation.gd` は各室の全床を通常入力で巡回して出発地点へ戻り、隣接壁/家具への方向入力が位置を変えないことを検査する。敷居への到達、退出、領域外の拒否、再入室、再歩行、5室の番号選択・背景識別を実測する。移動の期待座標と実状態をJSONに記録する。
- 5室とも描画を有効にしたX11/OpenGL（Mesa llvmpipe）で実施。通常画面の原PNGと、同じ状態・カメラで対象家具のoverlayだけを非表示にした診断画面、人物だけを非表示にした診断画面を別名で保存する。背後の画素差>0、手前の画素差=0、人物が全隠れしない画素差>0を要求する。診断表示の変更は移動状態に触れない。通常PNGと診断PNGを混同しない。
- 初回の防具屋では「すべての家具overlayを除く」比較が手前位置で34px差となり1失敗。上側の鎧の手前に立っていても下側の別の鎧の背後であるためだった。対象の上側の鎧だけを除く検査へ分離し、前後の同じ判定を維持した。元検査・画像・JSON・ログは `first-pass/` に保存。
- 既存screen/port検査が既存の記録JSONを生成したため、構造不変検査が2文書の差分を検出した。原生成JSONを `generated-regression-records/` に保存してから、開始時の元bytesを戻した。検査スクリプトや期待値を変更していない。失敗時のJSONとログも保存。
- 環境既定Godot 4.6.3を検証に使わず、CI固定4.7.2-stable ZIPを取得しSHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` を照合した。binaryは `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。XDG各領域とRPG_QA_SAVE_PREFIXを080専用にし、利用者保存に触れていない。
- X11のV-Sync非対応WARNINGとXorgのDBus接続通知は原ログに保持する。R検査は既存 `run_locked_checks.py` のjudge_outputで終了コードだけでなく実行数・エラー/警告・pendingを判定した。契約の各verifyをそのまま300秒上限で逐次実行する。既存runnerが親管理の記録へ書き込むのを避け、出力先だけ080証拠にした外部実行器を同梱する。

## 初回時点の未達・引継ぎ（限定承認前の履歴）

- **素材strictは未解消**：PR49の台帳5件はowner出所を正確に維持したまま取り込んだ。元画像5枚も存在し、出所記録のSHAに全件一致。しかしmainの既存 `validate_assets.py` はこの原画パスを許可していないため5件を拒否する。5件の出所をgenerated等へ偽装せず、原画を別の許可フォルダへ複製せず、PR49の検査変更・保護変更を取り込まず、strictを迂回していない。この依存の解決は今回の権限外。拒否を残した候補として引き渡す。
- **旧coastal検査**：基点と候補で実測し、`return_learned` のDictionary参照エラーを保持する。最新の航路検査の成功で旧失敗を成功に置き換えない。
- 正式commit/push/PR/main/全CIは未実行で親担当。066・073の保留は解除しない。ローカル歩行検証を正式検収や全ゲーム完成としない。
- 本番進行接続、住人、施設サービスは今回の基盤対象外で未実装。実機の物理キー・ゲームパッド・利用者による手触り評価は未検証。入力証拠はエンジンに送った通常InputEventであり、物理機器の実測とはしない。

## 初回候補の実測（限定承認前の履歴）

| 室 | 床数（敷居を含む） | 判定 | 入力イベント | 失敗 | 秒 | 背後/手前の画素差 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| inn | 53 | 218 | 332 | 0 | 53.956 | 31 / 0 |
| item_shop | 64 | 255 | 406 | 0 | 60.817 | 95 / 0 |
| weapon_shop | 63 | 250 | 396 | 0 | 61.526 | 364 / 0 |
| shrine | 58 | 231 | 358 | 0 | 53.848 | 437 / 0 |
| armor_shop | 59 | 237 | 370 | 0 | 58.283 | 9 / 0 |

合計1191判定・1862入力イベント、失敗0。押下/解放を別イベントとして記録。敷居を含む床は合計297マスで、全て通常入力で訪れた。番号選択/入口/背後/手前の固定画像は5室別に保存。最終通常描画PNGを5室とも実際に表示して原採用画像と照合した。

宿の受付と防具屋の奥の鎧は、既存rendererがoverlayの足元値から0.5を引くため、人物との同値を避けて実底面に奥行きを合わせた。通行・素材bytesを変えず、宿はその後に全巡回/描画を再測定、防具屋は修正後の定義で測定した。

| 既存検査 | exit / 結果 |
| --- | --- |
| R-01 | 0 / PASS |
| R-02 | 0 / PASS |
| R-03 | 0 / PASS |
| R-04 | 0 / PASS |
| R-05 | 0 / PASS |
| R-06 | 0 / PASS |
| R-07 | 0 / PASS |
| R-08 | 0 / PASS |
| final-editor-import | 0 / 7.644秒 |
| frozen-final | 0 / 0.066秒 |
| saved-value-types | 0 / 6.25秒 |
| saved-position-relocation | 0 / 8.173秒 |
| second-region-coast | 0 / 7.495秒 |
| region2-port | 0 / 6.549秒 |
| first-region-screen | 0 / 10.179秒 |
| battle-recovery | 0 / 50.096秒 |
| baseline-assets-strict | 0 / 7.792秒 |
| assets-strict | 1 / 7.949秒 |
| baseline-coastal-travel | 124 / 180.009秒 |
| coastal-travel | 124 / 180.007秒 |
| invalid-room | 2 / 1.424秒 |

R-08は25テスト・3046assertions、failed/pending/invalidなし。保護対象26件すべて一致。素材strictは基点1154件成功、候補1159件のうち出所エラー5件で失敗（画像仕様・音15件・字体2件・パレット3件の別エラーなし）。旧coastalは両方180秒・exit124で全文ログがバイト一致。invalid-roomは負例として期待したexit2であり、成功exit0ではない。

## 原証拠と引渡し形式

`docs/verification/task-080/` に原ログ/JSON/PNG・初回失敗・再現手順を収録。`.gdignore` はこの証拠フォルダだけをGodotの素材import対象から除外するもの（検査対象や検査コマンドは変更しない）。editorが新規生成した担当外のUID2件は証拠へ移し、提出差分に混ぜない。実装・素材・報告の15ファイルと証拠の全変更一覧・各bytes/SHAはZIPの `changed-files.json` / `SHA256SUMS.json` に記録。基点全trackedファイルのうち既存変更は台帳5項目の95行追加だけ。親台帳・保護・test・CI・既存検査・原画・本番コードの差分0件。

ZIPは未commitの全payload、適用再検証済みのbinary diff、独立indexから計算した候補tree、元registry、SHA256manifestを含む。候補treeはcommitではない。Library ID・ZIP bytes/SHA・候補treeは自己参照を避けて最終引渡しに記す。GitHub正式操作と全CIは未実行、親による保存・検収を残す。

梱包の初回 `git diff --cached --check` は原Rログ末尾の空行とXorgログの末尾空白を検出してexit2となった。全検査を維持し、原文は改変せず、提出ツリーの全.logをgzipで可逆保存する。ZIPのraw-logs/には未加工.logも収録し、展開bytesの一致を確認する。初回の差分検査原ログ・梱包コードも保持する。既存ファイルの削除や原画像変更はない。

## 2026-10-21 03:49:55 UTC 限定承認・追加作業前の記録

ユーザーの「お願いします」（Sentinel_036453b7e7c881918d9630e8b4e40f6b）は、PR49固定headの原画5件の完全パス/SHA照合だけを今回の歩行基盤へ適用する承認。PR49自体のmain保留解除ではない。最新mainは引き続きe677896d3e61b8fe8136ef60c5c76f41ad76701d。

前候補からの全変更予定：tools/validate_assets.pyの限定2箇所、追加非保護tools/check_adopted_room_provenance.py、本報告書、docs/verification/task-080-approved-20261021T035317Z/以下の新証拠。既存台帳・5採用PNG・原画・歩行実装・既存検証器のその他部分・保護26・CI・親台帳は変更しない。旧ZIP2本と失敗ログを保持する。

旧080 Python検証器は「基点の既存変更がregistryだけ」という前候補19f0ef9e08b546ad3b9d9143e5b6b97e59ba6d31の範囲条件を含むため、その元版を固定候補で再検証し続ける。元検証器は変更しない。今回追加の検証器で承認済みvalidator差分だけの例外を厳密照合し、床/画像/負例等の継続条件は旧検証器の関数を再利用して最新候補で検証する。範囲条件を無断で緩和した成功とは扱わない。

## 限定承認後の最終実測

検証対象tree `fe03481131519fba6cfb2e11ad5ac3e89feb828e`。これは限定validator・追加検証器・承認記録までの候補。最終提出treeとの差は、この結果の報告と原証拠追加だけで、ゲーム・validator・検証器・台帳・画像のbytesは同一である。

editor import開始 2026-10-21T03:57:42.270485+00:00、終了 2026-10-21T03:58:52.061296+00:00。次の検証開始 2026-10-21T03:58:52.064563+00:00。全19実行にUTC ISO8601の開始/終了・コマンド・cwd・timeout・exit・原ログSHAを記録し、import先行・逐次・重複なしを照合。

| 検査 | 結果 |
| --- | --- |
| 素材strict | exit0、画像1159・音15・字体2・パレット3。問題なし |
| 限定出所の正負例・回帰・継続条件 | 3737判定、失敗0 |
| 5件以外の実出所項目 | 1171項目、基点のcheck_provenanceと完全一致 |
| 既存owner | 274項目、実項目と必須項目欠落/作者・license不正/不正パスの回帰成功 |
| 5室入力・描画 | 1191判定・1862入力イベント、失敗0 |
| R-01〜R-08 | 原verify・原judge_output・300秒上限を維持、全PASS |
| 保護ファイル | 26件すべて凍結SHA・基点SHA一致 |
| 旧080 Python範囲検証 | 無変更の旧候補19f0ef9e08b546ad3b9d9143e5b6b97e59ba6d31でimport後に成功 |

原画5件の実ファイルを正例にし、同じフォルダにある未承認の荷受け所、traversal、非正規の二重slash、別日付のパスを拒否した。さらに各原画のread_bytesだけに1byte変更/別原画の内容を返す観測負例と、is_fileだけをfalseにする欠損負例を与え、すべて拒否。これらはメモリ上のファイル読取観測であり、原画の変更・削除・別フォルダ複製はしていない。正負例の前後で実原画5件SHAを照合した。author/provided_at/original_file/modified/licenseの欠落と不一致も拒否を維持。実装から期待するSHAを生成せず、承認固定SHAを新検証器へ明示した。

今回のvalidator差分は固定PR49の2箇所の差分と完全一致（20行追加・1行置換）。最新基点へpatchとして適用し、ファイル全体を旧版へ置換していない。台帳・採用PNG・原画・歩行実装・元080検証器・他の検査条件は前候補と同一bytes。前候補の初回strict失敗と旧coastal失敗は履歴証拠として保持し、後から成功へ書き換えない。旧coastalは今回再実行していない。

原証拠は `docs/verification/task-080-approved-20261021T035317Z/` に保存（.logは原bytesを可逆gzip、通常描画PNGは無加工）。新ZIPには全候補payload・binary patch・全変更SHA一覧、基点全tracked treeからの再構成・最終tree一致証拠・保護26 SHA一覧・再現コマンドを収録。旧ZIP2本は元bytesで保持し、Library ID `libfile_5494cd2d160c8191a6db103edeb95af2` と `libfile_7d337407ecd081919857cf57216a86e2` を変更しない。

今回の素材strict阻害は解消済み。残るのは親の正式commit/push/PR/全GitHub CI・検収と本番進行接続等の別段階。新世界接続や人物・販売・物語の追加はない。利用者実機/物理ゲームパッドの評価は未実施。PR49 main保留・066・親台帳は不変。

梱包の初回diff検査で、追加した証拠patchのcontext空白行がtrailing whitespaceとして検出された。失敗原ログをpackage-attempt-1.log.gzに保持し、証拠patchも原bytes可逆gzipへ変更した。検査条件や実装の変更ではなく、梱包形式だけの修正。
