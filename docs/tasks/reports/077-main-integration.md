# 077 main取り込み候補の再検証

- 検証日：2026-10-20 UTC/JST。
- 対象：hiroshitanaka-creator/RPG-maker、codex/task-077-party-disabled-focus、PR #53。
- 第1親：`6ac43a5116562434521e5ef8c8210c352c35d9a7`。
- 第2親（指定main）：`a7f20f203f6d383c5f3534a1fa26774f1e5f868a`。
- 共通祖先：`8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`。
- 元077完成HEAD：`dd5a1d87fa6e76fa191fa011ed4588dcf31a77e3`。
- 通常mergeの未commit候補。正式commit/push/PR/main登録・GitHub全CIは親担当であり、完了とは扱わない。

## 統合・保持範囲

`git merge --no-commit --no-ff` を隔離worktreeで実行した。競合はdocs/decision-log.mdとdocs/tasks/README.mdの2件だけ。第1親が第2親の全文を完全な先頭部分として包含することを実bytesで照合し、第1親の原bytesをそのまま保持して解消した。競合原文も保存した。親台帳への追記や意味内容の編集はない。

共有 `scripts/ui/game_root.gd` は自動統合され、076の `scroll.follow_focus = true` と077の `if equip.disabled:equip.focus_mode = Control.FOCUS_NONE` が両方残った。候補から076の1行だけを除くと第1親全文、077の1行だけを除くと第2親全文になることを照合した。074/075の `first_region_screen.gd` は第2親と完全一致。077依頼書・原報告・親台帳は第1親のbytes/modeを保持する。

第1親からの差分は上流10件と本報告の計11件：074/075/076依頼書3件、074/075/076原報告3件、075/076統合報告2件、first_region_screen.gd、game_root.gd、本報告。新しいゲーム機能や追加のコード修正はない。保護・test・既存checker・CI・assets/registry.json・project.godot・原画・仕様・物語・066は変更していない。

両親全パスのblob/modeを照合し、双方の変更を保持した。両親と共通祖先から同一候補treeへ適用できるbinary patchを同梱する。candidate.jsonのtreeはcommit SHAではない。

## 専用環境・実行順序

workspace空き容量が約344MBだったため、既存成果を削除せず、同じクラウドの `/tmp/task-077-main-integration` に新worktree、`/tmp/task077-main-integration-validation/` に今回だけのcandidate/baselineコピーを配置した。証拠は `/workspace/task077-main-integration-evidence/`。旧作業木や旧検証キャッシュは使い回していない。

候補7,731ファイル、共通祖先7,721ファイルについて、実行前に全blob・mode・SHA256を照合した。日本語パスはGitのNUL区切りで扱った。変更しない素材バイナリだけを新専用worktreeと共有し、コード・規約・ログ・保存先は分離した。実行後も全ソースを再照合し、検証コピー内の生成検証文書以外のbytes/mode不変を確認する。

固定Godot `4.7.2.stable.official.ed1daf0bf`。archive SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、binary SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。archive内binaryと実行ファイルを実bytes照合した。統合後の最初のGodot呼出しは `godot --headless --editor --import --quit` で、版表示もその原ログで確認した。

実行コードtreeは `524f6f9782f8cf4b6c4493b29bc52d75c8a65235`。全実行に専用の新規ディレクトリを用い、既存ディレクトリ/ログへの上書きを拒否する。start/resultにコマンド・対象tree・時刻・終了値・経過秒を記録し、stdout/stderr全文、原PNG、入力/矩形/全状態JSONを残した。最初のimport成功後に他検査を開始し、既存600/300/240/180/120秒の上限を変更していない。

## 077と076の同時成立

元077完成HEADの変更3ファイルは、保全したローカル原成果の全文と一致した。元077の通常入力と同じキー/撮影補助ホイール列を今回の候補へ送り、無注入ニューゲームから編成へ到達した。前進Tab9回は「探索へ戻る」、逆進Shift+Tab3回は説明用の空OptionButtonへ移り、無効な装着には入らなかった。装着はdisabled=true、focus_mode=0、focused=false。

ホイール補助を行う前の原PNGと矩形で同時成立を確認した。前進は焦点矩形と可視部分が `[16,219,480,19]`、逆進は `[16,197,436,19]` で一致。両方scroll_vertical=183、follow_focus=true。元077の装着除外と076の追従が同じ画面で成立しており、今回の可視性を撮影補助スクロールで代用していない。追加の076通常Tab16回/Shift+Tab16回も失敗0。

元077ハーネスには当時限定の `not scroll.follow_focus` があった。原文をoriginals/harnessに保存し、その1条件だけを今回承認された統合条件 `scroll.follow_focus=true` に置き換えた。装着条件・説明閲覧・独立全状態期待値など継続する全assertを維持し、各Tab/Shift+Tabで焦点全体可視のassertを追加した。移行表と全文差分を同梱する。既存repo内検査器や保護テストは変更していない。

3/4人×正逆順×候補0/1/2×未解放/解放×空枠/満枠の48条件を再検証した。診断状態は正規importによる注入であり、通常プレイ到達とは区別する。説明OptionButton/PopupMenu、仲間切替、装着/解除後の再生成、満枠での既存拒否、マウス操作、戻る再表示、全状態不変を元077の独立期待値で検証した。実描画では各人数/順序の未解放複数候補と有効1候補の8条件を再走。入力前後のfocus/矩形/scrollから、正逆の実移動・実スクロールと無効装着非選択を独立集計した。

078は未統合であり、change/release（転職・清める）側の既知未修正箇所を077の対象に含めない。元のFOCUS_ALL保持を確認する範囲に限定し、それらの無効選択除外も解消したとは報告しない。物理コントローラー/利用者PCは未検証。今回の077検査は仮想キー/マウス入力であり、仮想ジョイパッドの追加検査も行っていない。

## 074/075の保持と今回の結果

同一候補で075通常操作、薬0/1・地図未所持などの8境界条件、074の16診断条件、どうぐ→帰還→どうぐ→帰還の16連続条件を実入力・実描画で再検証した。有効な初期選択、無効項目除外、取消/再表示、薬のHP/所持数変化、帰還のMP2/徒歩帰還/船帰港と他の全状態不変を確認した。075の元96条件全数を今回再走したという意味ではない。

| 今回の実行 | ケース | 判定 | 失敗 |
|---|---:|---:|---:|
| combined-3-render | 8 | 668 | 0 |
| combined-4-render | 8 | 722 | 0 |
| equip-3-forward-headless | 12 | 2905 | 0 |
| equip-3-reverse-headless | 12 | 2905 | 0 |
| equip-4-forward-headless | 12 | 2905 | 0 |
| equip-4-reverse-headless | 12 | 2905 | 0 |
| equip-boundary-render | 8 | 2096 | 0 |
| equip-normal-render | 2 | 19 | 0 |
| follow-normal-render | 1 | 52 | 0 |
| items-boundaries-render | 8 | 394 | 0 |
| items-normal-render | 5 | 44 | 0 |
| travel-render | 16 | 606 | 0 |

| 実行名（全文コマンドはstart/result.json） | exit | 経過 |
|---|---:|---:|
| assets-strict | `0` | 33.58秒 |
| baseline-coastal-legacy | `124` | 180.03秒 |
| baseline-editor-import | `0` | 107.76秒 |
| coastal-legacy | `124` | 180.03秒 |
| combined-3-render | `0` | 61.34秒 |
| combined-4-render | `0` | 63.74秒 |
| editor-import | `0` | 81.76秒 |
| equip-3-forward-headless | `0` | 165.15秒 |
| equip-3-reverse-headless | `0` | 151.09秒 |
| equip-4-forward-headless | `0` | 157.52秒 |
| equip-4-reverse-headless | `0` | 152.49秒 |
| equip-boundary-render | `0` | 150.96秒 |
| equip-normal-render | `0` | 36.32秒 |
| first-region-screen | `0` | 9.38秒 |
| follow-normal-render | `0` | 30.01秒 |
| frozen | `0` | 0.10秒 |
| headless-import | `0` | 11.32秒 |
| integrated-ui | `0` | 15.49秒 |
| items-boundaries-render | `0` | 39.66秒 |
| items-normal-render | `0` | 34.09秒 |
| locked | `0` | 189.75秒 |
| region2-port | `0` | 7.32秒 |
| saved-position | `0` | 6.21秒 |
| second-region-coast | `0` | 5.49秒 |
| travel-render | `0` | 71.39秒 |
| village-regression | `0` | 46.43秒 |

R-01〜R-08は全PASS、frozenは保護26件一致、assets strictは問題なし。各Rの全文原ログとscope-lock-current.jsonを同梱する。成功マーカーだけでなくSCRIPT ERROR/Parse Error/ERROR/WARNING/リークを監査する。実描画の環境由来V-Sync非対応警告は各原ログに保持した。

旧 `check_coastal_travel.gd` は今回の候補・今回の共通祖先コピーとも `return_learned` のSCRIPT ERRORの後、既存180秒上限でexit124。全文生ログはbytes一致した。既知失敗を修正・成功化せず、全検査が緑とは扱わない。

親から示された過去077 PRのTASK027通知付き撮影失敗と同SHA再試行成功は過去履歴であり、今回の成功へ算入していない。今回の各runに今回の原ログと結果を用いた。

## 引渡し・未検証

既読のAGENTS・素材規約・仕様・保護契約・素材台帳はhash一致。local storytellerはゲーム実装対象外、Godot関連skillは配置なしで新規導入なし。今回の明示指示を優先し、親台帳編集やcommit/pushを行っていない。Libraryの現在skillに従い別名ZIPで保存する。

旧077作業木のHEAD/status/全7,723ファイル、既存ZIP群のbytes/SHAを前後照合し保持した。配布物は変更11件の全文payload、両親の原文、競合原文、両親/共通祖先からの適用検証patch、全パスblob/mode/SHA、実行ハーネスと移行差分、全生ログ・原PNG・入力/状態JSON、manifest。検証コピー、キャッシュ、runtime保存領域、転送情報は除外し、ZIP全件のCRC/bytes/SHA256を照合する。

未達・未検証は旧coastal既知失敗、078対象の未修正箇所、親の正式保存・GitHub全CI・main登録、物理コントローラー/利用者PC。今回の結果で代用しない。

## 最終監査の初回停止と環境継続確認

初回 `final-audit` はexit1。起動runnerから `GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE` を引き継いだため、監査のcwd指定より検証コピー/indexが優先され、生成検証文書の差分を作業木差分として検出した。原ログのAssertionErrorと、環境を引き継いだ場合/解除した場合の実際のGit差分一覧をaudit-environment-diagnosis.jsonに保存した。source worktree側には未解決競合も未stageの既存ファイル差分もなく、HEAD/MERGE_HEADは指定両親のままだった。

監査用子プロセスだけで上記3変数を解除するaudit-v2.pyを新規作成した。元監査・初回生ログ・結果・全文差分を保持し、source保持/patch適用/ゲーム検査のassertや時間上限は変えていない。初回監査を成功へ書き換えていない。新規run `final-audit-v2` で全条件を再照合し、結果はそのresult.jsonとaudit.jsonに記録する。ゲームの検証結果をこの監査起動不備で置き換えていない。

10:47 UTCの切断通知後、同じ `/tmp/task-077-main-integration` と `/workspace/task077-main-integration-evidence` へアクセスできることを確認した。確認時点の29実行結果、生ログ、12入力結果・16,221判定、原PNG230枚、コードtreeを照合してenvironment-continuity.jsonへ保存した。切断の内部原因は不明で、推測していない。新環境への移動、利用者PC使用、作業木や成果物の重複作成は行っていない。
