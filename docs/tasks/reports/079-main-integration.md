# 079 main統合候補・再検証報告

日付：2026-10-20 UTC。同じ保存済みクラウド環境で統合候補を検証し、元ハーネスによる追加検証まで実行した。正式commit/push/全GitHub CI/main反映は親担当のため未実施。旧coastal検査の失敗を保持し、全検査成功とは扱わない。

## 統合候補

- 第1親：`7e3129af91f1b2ba818cb352e622086a35e2c24a`。
- 第2親：`f83e39e1e38174b4beaace908fc46a3823f8e60e`。
- 共通基点：`8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`。
- 検査したコードtree：`2c20cc7385e76ad0f611cfc661246e838d61816b`。最終報告を含むtreeはZIP内candidate.json。
- 作業領域：`/workspace/task079-candidate`。HEADとMERGE_HEADを指定両親とした未commit候補。

GitHubへの読取専用ls-remoteでmain・079枝・PR #55 headを実確認した。最初の照合はruns/remote-before、包装前の照合はruns/remote-finalに記録する。GitHub書込み・新commit・push・PR変更・main mergeは実行していない。利用者PC・ローカルCodex・別環境は使用していない。

親台帳の作業ファイルへ競合マーカーを書かないため、隔離cloneでgit merge-tree --write-treeを使用した。初回exit1は親台帳2件の競合。競合tree・原文を保存し、独立indexで第1親blobを選んでから、列挙済み16差分だけを作業木へ展開した。docs/decision-log.mdとdocs/tasks/README.mdは一度も編集せず、第1親のbytesを保持した。第2親の全文が第1親の先頭部分として保持されることも照合した。これを正式merge commitの作成とは扱わない。

game_root.gdは自動統合され、079のcheckpoint.focus_mode同期1行を除けば第2親全文とbytes一致する。first_region_screen.gdも第2親と一致する。074〜078を保持し、disabled条件・保存/拒否/復旧規則・物語・仕様を追加変更していない。両親・共通基点の全パスから片側だけの変更を落としていないことをaudit.pyで照合した。

第1親からの変更予定・最終変更は以下17件。上流16件と本報告であり、新しいゲーム実装の修正はない。

- `docs/tasks/074-return-menu-keyboard-focus.md`
- `docs/tasks/075-items-keyboard-focus.md`
- `docs/tasks/076-party-focus-scroll.md`
- `docs/tasks/077-party-disabled-focus.md`
- `docs/tasks/078-party-action-focus.md`
- `docs/tasks/reports/074-return-menu-keyboard-focus.md`
- `docs/tasks/reports/075-items-keyboard-focus.md`
- `docs/tasks/reports/075-main-integration.md`
- `docs/tasks/reports/076-main-integration.md`
- `docs/tasks/reports/076-party-focus-scroll.md`
- `docs/tasks/reports/077-main-integration.md`
- `docs/tasks/reports/077-party-disabled-focus.md`
- `docs/tasks/reports/078-main-integration.md`
- `docs/tasks/reports/078-party-action-focus.md`
- `scripts/ui/first_region_screen.gd`
- `scripts/ui/game_root.gd`
- `docs/tasks/reports/079-main-integration.md`

.scope-lock/test/保護検査/CI/assets/registry.json/project.godot/契約/原画は変更していない。066と073以前は変更対象外。削除・履歴改変・検査弱体化・省略による成功化・時間延長は行っていない。未実施検査は下記の未達として残す。

## 実行環境と検査

Godot 4.7.2.stable.official.ed1daf0bf固定。binary SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`、archive SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`。実行binaryとarchive内binaryもbytes一致。

候補検査コピー7737ファイル、基点7721ファイルを全Git blob/bytes/SHA256照合してから実行した。候補と基点は別ディレクトリで、保存先XDGとRPG_QA_SAVE_PREFIXも各実行ごとに分離した。最初のGodot実行はそれぞれeditor import。候補の他の検査はimport成功後に開始した。既存検査器・保護テストを変更していない。

| 実行 | コマンド | exit | 秒 |
| --- | --- | ---: | ---: |
| editor-import | `timeout 600 godot --headless --editor --import --quit` | 0 | 103.40 |
| headless-import | `timeout 600 godot --headless --import` | 0 | 5.13 |
| assets-strict | `python3 tools/validate_assets.py --strict` | 0 | 6.25 |
| frozen | `python3 tools/check_frozen_files.py` | 0 | 0.03 |
| locked | `python3 tools/run_locked_checks.py` | 0 | 91.56 |
| battle-recovery | `timeout 180 godot --headless --path . --script res://tools/check_battle_recovery.gd` | 0 | 31.69 |
| first-region-screen | `timeout 180 godot --headless --path . --script res://tools/check_first_region_screen.gd` | 0 | 2.69 |
| second-region-coast | `timeout 180 godot --headless --path . --script res://tools/check_second_region_coast.gd` | 0 | 1.47 |
| region2-port | `timeout 180 godot --headless --path . --script res://tools/check_region2_port.gd` | 0 | 2.40 |
| village-regression | `timeout 180 godot --headless --path . --script res://tools/check_region2_village_regression.gd` | 0 | 19.52 |
| saved-position | `timeout 120 godot --headless --path . --script res://tools/check_saved_position_relocation.gd` | 0 | 2.26 |
| integrated-ui | `timeout 240 godot --headless --path . --script res://tools/check_integrated_ui.gd` | 0 | 5.22 |
| coastal-legacy | `timeout 180 godot --headless --path . --script res://tools/check_coastal_travel.gd` | 124 | 180.01 |
| baseline-editor-import | `timeout 600 godot --headless --editor --import --quit` | 0 | 97.23 |
| baseline-coastal-legacy | `timeout 180 godot --headless --path . --script res://tools/check_coastal_travel.gd` | 124 | 180.01 |

R別結果：R-01 PASS、R-02 PASS、R-03 PASS、R-04 PASS、R-05 PASS、R-06 PASS、R-07 PASS、R-08 PASS

各実行のstart/result.jsonに開始・終了・実コマンド・exitを記録し、stdout/stderr全文を保存した。R別原ログとscope-lock-current.json、生成された原JSON等も保存する。生成検証文書は検査コピーにだけ出力し、候補のtreeへ混入させていない。generatedは最終snapshotであり、各run専用の一次生成物であるという主張はしない。全ソースを再照合し、検査コピーのdocs/verification生成以外は不変。

旧check_coastal_travel.gdは、今回の候補と共通基点で同じDictionaryのreturn_learned参照エラー後exit124。両stdout全文のbytes一致を確認した。旧結果の引用だけで済ませず、今回実ログを保持した。成功へ変更せず、全検査成功とは扱わない。詳細な警告/エラーはaudit.jsonに全文を列挙する。

## 元ハーネスの受領と実行

初回はLibrary配信先のCONNECTが403となり、子は元079/078 ZIP全体を取得できなかった。配信ホストへの再試行・設定変更・迂回はしていない。親が正規prepare_materializeでworkspace_pathを得て両ZIPを直接取得し、bytes/SHA/CRCとmanifest523件・740件を独立照合したと報告した。親は元画像・過去ログを保持している。これは親の照合記録であり、子が元ZIP全体を取得・検収したという主張ではない。

親が原ZIPから抽出したハーネス・fixture・runner参照17ファイルを本文のgzip/base64で渡した。子の初回転記は不完全でbase64 padding errorとなった。元ZIPの破損ではなく子の転記失敗であり、transfer-attempt-01.b64/logを保持した。その後の11断片は各3500文字（最後3168）、合計38168文字で一致した。展開前にgzip28624 bytes/SHA256 `dfedceacd6fd14ed3b781265859450f5515217d587cfad54c7b95c5a6e0663c2`、JSON135002 bytes/SHA256 `b5a06376645309b453414dfb51d84ea5eda22a90b93e10cb485ad0d048530e81`を実照合した。17件各bytes/SHAも一致し、安全なworkspace内へ保存した。元fixture絶対パスを再現した。元17ファイルは実行後も全bytes不変。

元runnerは過去環境パス・display IDの参照資料として読み、直接実行していない。別adapterで現候補検査コピー、各実行専用XDG、出力先、仮想画面:87だけを指定した。GDScriptハーネス・assertion・180秒上限は変更していない。原079のreproduction/behavior、078統合版のboundary/reproduction/follow/items/travel/combinedをそのまま使用した。

元079再現は共通基点で10ケース中focus除外条件10件が失敗しexit1、現候補は同じ入力列で10ケース成功。通常ニューゲーム/保存なしと、原R07保存fixtureの隔離複製・破損/無効/全滅診断を区別した。正常8、拒否12、遷移4をheadlessとX11描画の両方で実施。新規ノード再起動相当、手動/自動/backup/tmpの不変、計測回数/履歴、連続入力、再表示、取消を元assertで検証した。正常復帰の期待全状態と実状態、拒否前後の全状態/ファイル/計測もPythonで独立照合した。

074/075は道具・帰還と相互遷移、076〜078は編成の焦点スクロール・無効装着/転職/清めるの非選択を同じ候補で確認した。078の主32・追加8・祠3診断と描画反復12、通常再現、076通常到達を元078統合時と同じ24実行で再検証した。3/4人、仲間正逆順、職解放/未解放、侵蝕10/不可逆90/健常0/魔物化89、祠内外、職候補往復/PopupMenu取消/転職/清める確認取消確定を含む。診断注入を通常到達と同一視しない。状態結果の注入やfocus強制は行っていない。

候補カスタム32実行、42223判定、失敗0。共通基点の意図した失敗1実行は成功数に含めない。新規原PNG 333枚のデコード/bytes/SHAを検証。原JSONと各実行stdout/start/resultに入力・全状態・開始終了UTC・exit・コマンドを保存した。

| 実行 | ケース | 判定 | 失敗 | exit | 秒 | PNG |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 078-actions-3-forward-locked-headless | 4 | 2645 | 0 | 0 | 45.03 | 0 |
| 078-actions-3-forward-open-headless | 4 | 2667 | 0 | 0 | 50.54 | 0 |
| 078-actions-3-forward-render | 4 | 2683 | 0 | 0 | 61.73 | 16 |
| 078-actions-3-reverse-locked-headless | 4 | 2649 | 0 | 0 | 46.27 | 0 |
| 078-actions-3-reverse-open-headless | 4 | 2673 | 0 | 0 | 51.51 | 0 |
| 078-actions-4-forward-locked-headless | 4 | 2645 | 0 | 0 | 45.29 | 0 |
| 078-actions-4-forward-open-headless | 4 | 2667 | 0 | 0 | 52.70 | 0 |
| 078-actions-4-reverse-locked-headless | 4 | 2649 | 0 | 0 | 46.58 | 0 |
| 078-actions-4-reverse-open-headless | 4 | 2673 | 0 | 0 | 52.42 | 0 |
| 078-actions-4-reverse-render | 4 | 2685 | 0 | 0 | 61.90 | 12 |
| 078-actions-extra-3-forward-headless | 2 | 1322 | 0 | 0 | 26.39 | 0 |
| 078-actions-extra-3-forward-render | 2 | 1330 | 0 | 0 | 35.81 | 8 |
| 078-actions-extra-3-reverse-headless | 2 | 1327 | 0 | 0 | 26.37 | 0 |
| 078-actions-extra-4-forward-headless | 2 | 1322 | 0 | 0 | 27.32 | 0 |
| 078-actions-extra-4-reverse-headless | 2 | 1327 | 0 | 0 | 27.09 | 0 |
| 078-actions-extra-4-reverse-render | 2 | 1332 | 0 | 0 | 39.42 | 5 |
| 078-actions-locations-3-forward-headless | 3 | 2019 | 0 | 0 | 45.44 | 0 |
| 078-actions-reproduction-render | 4 | 38 | 0 | 0 | 18.44 | 12 |
| 078-combined-3-render | 8 | 668 | 0 | 0 | 35.40 | 46 |
| 078-combined-4-render | 8 | 722 | 0 | 0 | 38.75 | 46 |
| 078-follow-normal-render | 1 | 52 | 0 | 0 | 14.79 | 17 |
| 078-items-boundaries-render | 8 | 394 | 0 | 0 | 37.09 | 16 |
| 078-items-normal-render | 5 | 44 | 0 | 0 | 18.00 | 15 |
| 078-travel-render | 16 | 606 | 0 | 0 | 47.79 | 64 |
| 079-rejected-headless | 12 | 728 | 0 | 0 | 46.04 | 0 |
| 079-rejected-render | 12 | 746 | 0 | 0 | 57.57 | 18 |
| 079-reproduction-headless | 10 | 84 | 0 | 0 | 8.28 | 0 |
| 079-reproduction-render | 10 | 104 | 0 | 0 | 20.07 | 20 |
| 079-transitions-headless | 4 | 206 | 0 | 0 | 11.11 | 0 |
| 079-transitions-render | 4 | 214 | 0 | 0 | 21.16 | 8 |
| 079-valid-headless | 8 | 486 | 0 | 0 | 22.82 | 0 |
| 079-valid-render | 8 | 516 | 0 | 0 | 37.53 | 30 |
| baseline-079-reproduction | 10 | 84 | 10 | 1 | 7.90 | 0 |

初回のPython集計は、清める確認画面にもスクロール用follow_focusフィールドがあると誤って仮定しKeyErrorとなった。原JSONの当該画面がスクロールなしの取消/確定ボタンであることを照合し、v2で確認画面の有効/全体可視と編成画面のfollow_focusを別々に検査した。初回scriptと失敗ログを保持し、元Godotハーネスや検査結果は変更していない。Xorg停止の初回補助コマンドはargv0を短名で比較して該当PIDを見つけずAssertionError。signalは送られていなかった。実argv0を読取確認して当該:87プロセスだけにSIGTERMし、サーバexit0を確認した。これらも原ログを保持する。

実表示した未加工PNGはvisual-verification.jsonにファイル/SHA/所見を記録した。全PNGを目視したとは扱わない。X11ではV-Sync変更非対応WARNINGがあり、Xorg通知を含め全文保持する。その他の警告/エラーはaudit.json。実入力はGodotへ投入したキー/マウスイベントで、利用者実機・物理controller・仮想joypad・初見操作感は未検証。

## 原証拠の保存・未達・引渡し

初回部分ZIP `libfile_3a0fcdb8a8748191ae0c94085ae549cb`（3439509 bytes、SHA256 `fb7b213272a13fbab77a7f87071008b1331b00c38d1f157340a3f6f43ace59e7`）を上書きせず、新ZIPに原bytesのまま内包する。初回merge競合、Library取得失敗、全標準検査、coastal基点/候補exit124、初回報告・当時のpatch/tree/manifestはこの内包ZIPに保持した。初回5ダウンロードの正確な開始終了UTCは欠損しており、tool出力/exit/wall timeでしか残っていない。この欠損を補完したと偽らない。

追加分は11断片・verified gzip/JSON・17原ファイル・adapter・初回転記失敗・全新規原JSON/PNG/ログ・保存fixture/隔離保存を収録。最終tree全ファイルのblob/mode/bytes/SHA、両親/共通基点からのbinary patch、全変更payload全文、両親の該当原文、commit情報も収録する。各固定親/基点から独立indexにpatch適用して同一最終treeとなること、全ZIP CRC/manifest bytes/SHAを照合した。xauthority認証値・署名URL・runtime cache/configは配布しない。原17ファイルとその実行証拠は含むが、元079/078 ZIP全体・過去PNG/ログ全体は親保持であり本ZIPには含めない。

21:23と21:41 UTCの環境切断通知を記録した。21:23のexec-server transport disconnected原文は初回ZIP内、21:41通知後の21:43:26に同workspace・全入力SHA一致・追加検証未起動を確認した。内部原因は不明。環境切替・重複タスク作成・利用者PC使用はない。初回と今回の原証拠を保持したまま同環境で続行した。

未達・残件：親による候補検収、commit/push/PR/全GitHub CIとmain統合。既知coastal失敗の範囲外対応。利用者実機/物理controller/人間評価。子が元ZIP全体や過去全PNGと照合することは未実施。親から提供された17入力の今回検証は完了し、入力不足で停止している検査はない。新しいLibrary ID・作成UTC・bytes・SHAと最終treeはタスク最終応答と外部receiptに記録する。

親台帳2件は079 head bytesを保持し、今回の再開で編集したrepoファイルは本報告だけ。最初に列挙した上流16差分も保持。GitHubへの書込み・新commit・push・PR更新・main mergeは行っていない。AGENTSの一般commit/push/台帳追記規定より、今回の親担当指定を優先した。使用量への影響は不明。
