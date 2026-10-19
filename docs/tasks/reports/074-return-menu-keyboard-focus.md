# 074 帰還メニューのキーボード選択 — 実装・ローカル検証報告

## 結果と範囲

方向キーと決定キーだけで帰還メニューを開いたとき、フォーカスが失われて使用者を選べない不具合を実描画で再現し、UI内の2箇所を修正した。使用者を選び直す・戻る・再表示・訪問済み目的地の選択・通常の帰還実行を検証した。正式保存・提出SHAのCI・親検収は未実施であり、リポジトリの完了定義を満たしたとは扱わない。

全変更は次の3ファイルだけ。

- `scripts/ui/first_region_screen.gd`：初期focus対象にtravelを追加。travelで無効なボタンをfocus対象から外す。
- `docs/tasks/074-return-menu-keyboard-focus.md`：状態行だけを「報告済み」へ変更。
- `docs/tasks/reports/074-return-menu-keyboard-focus.md`：本報告。

main基点は `8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`、正式依頼は `438209fbbb469379a1405a937cea8408b8ad37be`。この間の差分は074依頼書1件だけと確認した。指定branch `codex/task-074-return-menu-keyboard-focus` を別worktreeに作成し、初期差分0から開始。073の未push差分・素材登録を取り込んでいない。検査コピー・一時ハーネス・画像・原ログは `/workspace/task074-return-menu-focus-evidence/` 内に隔離した。コードを担当する子エージェントは起動していない。

## 契約・環境

AGENTS.md、.scope-lock、依頼書全4節、伝言板、依存記録、素材規約、職業・魔物化企画、優先する体験仕様の帰還・船の決定、既存帰還仕様と検査を確認した。指定の godot-dev-director / godot-game-verification / godot は、実配置と公開されているスキル一覧に見つからず、導入していない。同梱コード、新Autoload、新テスト基盤の追加なし。

既存のGodot 4.7.2 ZIPを公式配布URLに対応する依存記録の固定SHA `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` と照合し、ZIP内実行ファイルとの全バイト一致と `4.7.2.stable.official.ed1daf0bf` を再確認した。新しい版へ置換していない。クラウド内のXorg dummy / Mesa llvmpipeで実描画し、画像1024×576（内部512×288の2倍）を保存した。MSI・利用者PCは使っていない。

## 再現と最小修正

診断用の有効な保存状態を本番GameSessionへ読み込んだ後、Escape→Down→Enterで通常メニューから帰還画面へ進み、Down→Enter→Rightを入力した。マウス入力、Button.pressedの直接呼出し、ハーネスからのControl.grab_focusは使用していない。3人/4人・正順/逆順の全4ケースで、帰還画面には入れるがfocus ownerがnullになり、使用者は空のまま。実画像にも選択枠がない。基点と最終修正に同じ24キー入力を行い、修正前12失敗→修正後0失敗（64項目）を確認した。

既存 `_button` は有効な最初のボタンを `_first_button` に保持していたが、`_ready` の自動focus対象にtravelがなかった。既存の遅延grab_focus処理の対象へtravelを加えた。これにより使用者選択による画面再構築後も有効ボタンを選べる。

追加の境界検査で、Godotの方向キー移動が無効なButtonへもfocusを移すことを実測した。travelの無効ボタンだけ `FOCUS_NONE` とし、初期選択と方向移動の双方で無効な仲間・未選択時の目的地を選択対象から外した。ほかの画面のfocus・入力処理は変更していない。

## 前後・境界・状態の検証

3人/4人 × 正順/逆順 × 通常/先頭戦闘不能/先頭MP1/全員MP1の16ケースを実行した。3人の後半地点状態などは診断注入であり、通常プレイ到達の証明と混同しない。

- キー入力246件、ヘッドレス542項目、実描画606項目が成功。両方のキー・focus遷移記録は一致。実画像64枚を保全した。
- 初回表示、使用者選択後の再構築、別の使用者への選び直し、Escape取消、戻るボタン、再表示を検証。各キーの後に無効ボタンへfocusしていないことを確認。
- 先頭不可では次の有効な仲間へfocus。全員不可でも既存 `can_return` は習得・場所を判定するためメニュー自体は開き、「戻る」だけがfocus対象になる。この判定規則は変更していない。
- 訪問済み3か所だけを表示し、未訪問先を追加しない。選択・取消のみでは `GameSession.export_state()` 全体が一致する。
- 帰還できる12ケースで、選んだ生存者だけMP2を消費し、指定入口の前へ徒歩で移動、船は既存港位置へ移動する。独立に作った期待状態と実状態全体が一致し、他の仲間・所持品・進行フラグ等も不変。
- 全ボタンの矩形が内部512×288に収まることを独立照合。実画像を表示して日本語の文字・選択枠・灰色の無効表示を確認した。

検査ハーネスの初期調整では、無効な3人fixtureと、左右移動が必ず最上段目的地へ着くという誤った仮定があった。原ログを残し、有効なfixtureと「右で目的地列へ移り、上で指定目的地へ移る」入力へ修正した。製品の期待値・既存検査を変更していない。最終検査は全16ケースを省略せず実行した。

## 通常到達からの追加確認

無変更の基点の既存 `prepare_port_departure.gd` により、新規開始から通常操作で村・洞窟・城・森の塔を通り、4人で山道へ到達した保存を新規作成した。初回ではR-07の14項目と通常到達68項目のPASSを得て、GameSession.save_gameがuser領域へ原保存を作成した。ただし、その後の複製でエラーが出たため準備全体の成功とは扱わない。この隔離user領域に作成された原保存（37,216 bytes、SHA-256 `123d9b9c571554b4c0c180f10f4042434f1d63bb9b3066fbb20f94dc3083f8d9`）を内容未編集で回収し、出典とエラーを併記した照合記録に従って変更後の本番へ通常ロードした。

checkout外の一時ハーネスで、通常歩行→宿→祠の会話で習得→荷受け所の会話で船借用→乗船・航行を行った。帰還メニューを開いて以降は方向キー・決定だけで2人目と港町を選び、MP2・徒歩帰還・船帰港・保存復元を確認した。通常到達の開始・経路は診断fixtureから分離し、原入力、前後状態、4枚の実画面を保存した。

初回の準備実行は作業コピーに `.tools/` がなかったため、通常保存の複製先を開けずエラーになった。生成先ディレクトリをcheckout外に用意し、既存スクリプトを変更せず同じ180秒上限で再実行した。再実行は180秒上限でtimeout（exit124）となったため、上限を延ばしていない。終了0だけの初回を成功扱いせず、初回エラーと再実行timeoutを両方残した。回収した原保存からの後続経路確認と、この準備スクリプト全体の未成功を区別する。

## 実行コマンドと実測

パスはすべてクラウド内の隔離コピー。一時ハーネスのみ絶対パスを用いる。既存verifyの300秒、importの600秒、該当検査の既存上限を延ばしていない。

| 原ログ名 | コマンド | exit | 実測時間 |
| --- | --- | ---: | ---: |
| `before-import` | `timeout 600 godot --headless --editor --import --quit` | 0 | 66.09秒 |
| `before-final-probe` | `timeout 60 godot --headless --path /workspace/task074-return-menu-focus-evidence/.baseline-project --script /workspace/task074-return-menu-focus-evidence/focus_probe.gd -- --probe-only` | 1 | 17.13秒 |
| `after-final-probe` | `timeout 60 godot --headless --path . --script /workspace/task074-return-menu-focus-evidence/focus_probe.gd -- --probe-only` | 0 | 8.68秒 |
| `after-focus-headless` | `timeout 180 godot --headless --path . --script /workspace/task074-return-menu-focus-evidence/focus_probe.gd` | 0 | 44.66秒 |
| `after-focus-rendered` | `timeout 180 godot --display-driver x11 --audio-driver Dummy --path . --script /workspace/task074-return-menu-focus-evidence/focus_probe.gd` | 0 | 126.28秒 |
| `after-final-editor-import` | `timeout 600 godot --headless --editor --import --quit` | 0 | 11.87秒 |
| `after-prescribed-import` | `timeout 600 godot --headless --import` | 0 | 5.93秒 |
| `after-strict` | `python3 tools/validate_assets.py --strict` | 0 | 8.32秒 |
| `after-second-coast` | `timeout 180 godot --headless --path . --script res://tools/check_second_region_coast.gd` | 0 | 18.49秒 |
| `after-region-ui` | `timeout 180 godot --headless --path . --script res://tools/check_first_region_screen.gd` | 0 | 9.51秒 |
| `after-region2-port` | `timeout 180 godot --headless --path . --script res://tools/check_region2_port.gd` | 0 | 5.89秒 |
| `after-village-regression` | `timeout 180 godot --headless --path . --script res://tools/check_region2_village_regression.gd` | 0 | 33.29秒 |
| `after-saved-position` | `timeout 120 godot --headless --path . --script res://tools/check_saved_position_relocation.gd` | 0 | 2.54秒 |
| `after-locked-checks` | `python3 tools/run_locked_checks.py` | 0 | 153.45秒 |
| `after-frozen` | `python3 tools/check_frozen_files.py` | 0 | 0.05秒 |
| `normal-departure-prepare-initial` | `timeout 180 godot --headless --path /workspace/task074-return-menu-focus-evidence/.baseline-project --script res://tools/prepare_port_departure.gd` | 0 | 172.04秒 |
| `normal-departure-prepare` | `timeout 180 godot --headless --path /workspace/task074-return-menu-focus-evidence/.baseline-project --script res://tools/prepare_port_departure.gd` | 124 | 180.01秒 |
| `normal-route` | `timeout 180 godot --display-driver x11 --audio-driver Dummy --path . --script /workspace/task074-return-menu-focus-evidence/normal_route.gd` | 0 | 74.97秒 |
| `baseline-coastal-boundary` | `timeout 180 godot --headless --path /workspace/task074-return-menu-focus-evidence/.baseline-project --script res://tools/check_coastal_travel.gd` | 124 | 180.02秒 |
| `after-coastal-boundary` | `timeout 180 godot --headless --path . --script res://tools/check_coastal_travel.gd` | 124 | 180.04秒 |

R-01〜R-08全PASS。R-07はA01〜A14と最終PASS行を監査。R-08は25テスト・3046 assertion、failed/pendingなし。素材1154・音15・字体2・パレット3正常、凍結26/26一致。現行の航路91、第2港935、村の継続回帰7631、保存位置31部屋199、通常画面10項目成功。

ヘッドレスの最終検査とR全原ログではSCRIPT ERROR・ERROR・WARNING・Parse Error・リーク・FAILマーカーなし。実描画では環境由来の `WARNING: Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver.` が出る。隠しておらず、画面確認成功と警告なしは区別する。これ以外の実描画エラーはない。

## 残る失敗・未検証と保存方式

古い `tools/check_coastal_travel.gd` は、正式基点と修正後で全く同じ原ログのスクリプトエラーになる。原fixtureの `GameSession.import_state` がfalseとなり、空のtravelの `return_learned` を34行目で参照する。既定180秒の外側timeoutで両方exit124。検査器を修正・弱化していない。この旧検査は現行CIに直接登録された `check_second_region_coast.gd` 等とは別で、成功済みの現行検査で旧検査の失敗を成功へ置き換えない。修正する場合は `tools/check_coastal_travel.gd` のfixture範囲について、074とは別の許可が必要。

AGENTS.mdの通常方式はcommit/pushとリポジトリ内の確認画像保存だが、今回の明示依頼は「3ファイルのみ・原証拠はcheckout外・親が公式GitHub保存」。この個別指示に従い、commit/push/PR作成/CI起動/mergeは行わない。decision-log、伝言板、registry、CI、project.godot、保護検査、066を変更していない。main取込みなし。実測の使用量は不明。

正式提出SHAの全CI、親の保存・検収は残る。新しい通常プレイ全体の人間評価を行ったとは扱わない。戻す場合は今回の3ファイルパッチを逆適用する（新規報告書は削除され、UIの元の不具合も戻る）。素材やゲームルールを戻す必要はない。

原bytesの3ファイル、差分、原ログ、画像、診断と通常到達の入力・前後状態、SHA manifestをLibrary ZIPへ保全する。ZIP全件をCRC/bytes/SHAで検証し、Library ID・ZIPのbytes/SHA・読戻し結果は自己参照を避け納品返答へ記録する。転送失敗と実装修正の失敗は区別する。

通常経路の実測：31項目・4画像・162歩・186入力。
実装ファイルSHA-256：`4ff6defb38547400b3ec7294d529d06b11e94ae7f7b4704c0f5e010d815cf9d8`。
