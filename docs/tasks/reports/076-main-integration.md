# 076 main取り込み候補の再検証

- 日付：2026-10-20 UTC/JST。
- 第1親：`fe7cf675d4b34037a604108596b4663bff343eff`（親による074/075検収記録を含む076枝）。
- 第2親：`cb7ca827f7368a2c636a9bf374a9598b3444069a`（指定main）。
- 共通祖先：`8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`。
- 元の076完成HEAD：`486a48442defe0edcac1c15c09cfc9334d8ca64b`。
- 未commitの通常merge候補。正式commit/push/PR/main登録・GitHub全CIは親担当であり、完了とは扱わない。

## 統合と原bytesの保持

隔離worktreeで `git merge --no-commit --no-ff` を実施。競合はdocs/decision-log.mdとdocs/tasks/README.mdの2件だけだった。第1親の各ファイルが第2親の全文を先頭に完全包含することを実bytesで確認し、第1親の原bytesをそのまま採用した。競合時の原文も保存した。親記録の意味内容を編集していない。

`game_root.gd` は第1親とblob/mode/bytes一致し、`_render_party` の `scroll.follow_focus = true` を保持する。`first_region_screen.gd` は第2親と一致し、074のtravel・075のitems無効選択除外と初期選択設定を保持する。元の076依頼書・完了報告の全文も第1親と一致する。新機能やゲームコードの追加変更はない。

第1親からの差分は上流6件と本報告の計7件：074依頼書、075依頼書、074報告、075報告、075-main-integration報告、first_region_screen.gd、本報告。親記録2件は差分に含まれない。両親全パスのblob/modeを照合し、それぞれの親および共通祖先から適用すると同じ候補treeになるbinary patchを同梱する。candidate.jsonのtreeはcommit SHAではない。

## 固定環境・入力証拠

Godot `4.7.2.stable.official.ed1daf0bf`。archive SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、binary SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。archive内binaryとの実bytes一致を照合した。

実行用候補7,728ファイルと共通祖先7,721ファイルの全blob・mode・SHA256を、最初の実行前に照合した。日本語パスはGitのNUL区切りで取得した。コード・設定・検査出力・保存先は専用コピーに分離し、変更しない素材バイナリのみ新しい専用worktreeと共有した。実行後も素材・保護・既存検査を含むソースを再照合する。実行対象コードtreeは `6ee55c098842f1c18c54d2251437facc50a89df3`。

各実行は専用の新規ディレクトリで開始し、既存ディレクトリ・ログへの上書きを拒否する。start/resultには実コマンド・対象tree・時刻・終了値・経過秒を記録し、stdout/stderrの全文と生成検証ファイルを保存した。候補の最初のGodot実行はeditor importであり、その成功後に他検査を開始した。既存上限600/300/240/180/120秒は変更していない。

## 実入力・実描画

無注入の通常ニューゲーム→Escape→方向キー→編成という実入力経路を再実行。Tab16回・Shift+Tab16回で焦点全体の可視性と全状態不変を確認した。Tab6回目の武器欄はscroll_vertical=103、焦点矩形と可視矩形が `[49,197,439,19]` で一致し、加工していないPNGで選択枠全体を確認した。

3/4人×正逆順×少/多の8条件は正規importによる診断状態と明記する。全仲間の切替、装着/解除、再生成後の追従、戻る・再表示、Escape、マウス・ホイールを元076の期待値で検査した。Tab/逆Tab、矢印、仮想十字キー、仮想Y軸について、焦点移動とスクロールが実際に変化した件数を別集計した。表示・取消で全状態不変、装着・解除は独立した全状態期待値と照合した。強制grab_focusやsignalの直接emitを正常到達の代用にしていない。

同一候補上で075の無注入通常操作、3/4人・正逆順・薬0/1・地図未所持境界、074の16診断条件、どうぐ使用→帰還→どうぐ再表示→帰還の16統合条件を実入力・実描画で再検証した。074/075の無効選択除外、初期選択、取消・再表示、薬の独立HP/所持数変化、帰還のMP2・徒歩移動・船帰港と他の全状態不変を確認した。075の元96ケース全数の再走は今回の検査に含めず、今回実行した範囲と元報告を区別する。

物理コントローラーは未接続。InputEventJoypadButton/Motionによる仮想入力であり、利用者PCや物理実機の操作成功とは扱わない。

| 実行 | ケース | 判定 | 失敗 |
|---|---:|---:|---:|
| combined-3-render | 8 | 668 | 0 |
| combined-4-render | 8 | 722 | 0 |
| items-boundaries-render | 8 | 394 | 0 |
| items-normal-render | 5 | 44 | 0 |
| party-3-forward-render | 2 | 643 | 0 |
| party-3-reverse-render | 2 | 643 | 0 |
| party-4-forward-render | 2 | 717 | 0 |
| party-4-reverse-render | 2 | 717 | 0 |
| party-axis-headless | 8 | 232 | 0 |
| party-normal-render | 1 | 52 | 0 |
| travel-render | 16 | 606 | 0 |

## コマンド結果

| 実行名（全文コマンドは各start/result.json） | exit | 経過 |
|---|---:|---:|
| assets-strict | `0` | 19.59秒 |
| baseline-coastal-legacy | `124` | 180.04秒 |
| baseline-editor-import | `0` | 147.20秒 |
| coastal-legacy | `124` | 180.21秒 |
| combined-3-render | `0` | 61.29秒 |
| combined-4-render | `0` | 58.68秒 |
| editor-import | `0` | 75.40秒 |
| first-region-screen | `0` | 4.53秒 |
| frozen | `0` | 0.13秒 |
| headless-import | `0` | 9.27秒 |
| integrated-ui | `0` | 9.10秒 |
| items-boundaries-render | `0` | 66.84秒 |
| items-normal-render | `0` | 52.03秒 |
| locked | `0` | 249.81秒 |
| party-3-forward-render | `0` | 90.92秒 |
| party-3-reverse-render | `0` | 104.59秒 |
| party-4-forward-render | `0` | 103.64秒 |
| party-4-reverse-render | `0` | 98.64秒 |
| party-axis-headless | `0` | 43.35秒 |
| party-normal-render | `0` | 38.53秒 |
| region2-port | `0` | 3.75秒 |
| saved-position | `0` | 7.50秒 |
| second-region-coast | `0` | 3.64秒 |
| travel-render | `0` | 77.32秒 |
| village-regression | `0` | 42.07秒 |

R-01〜R-08は全PASS、frozenは保護26件一致、assets strictは問題なし。各Rログとscope-lock-current.jsonを保存した。成功マーカーだけでなくSCRIPT ERROR・Parse Error・ERROR・WARNING・リークを監査する。実描画には環境のV-Sync未対応警告が各1件あり、原ログに残す。

旧 `check_coastal_travel.gd` は候補・共通祖先とも `return_learned` のSCRIPT ERRORの後、既存180秒上限でexit124となった。両者の全文生ログはbytes一致。これは既知の基点失敗をそのまま保持した結果であり、修正・成功化していない。全検査が緑とは報告しない。

## 引渡し・未検証

現在のAGENTS、素材規約、仕様、保護契約、素材台帳は既読契約とhash一致。ローカルstoryteller skillはゲーム実装を対象外とし、今回には適用していない。Godot関連skillは配置なし、導入なし。現在のLibrary skillに従って新ZIPとして保存する。

候補の正式commitは作成していない。旧076作業木のHEAD/status/全7,723ファイルと既存ZIP群は前後一致を検査し、そのまま保持する。親記録、保護・test・CI・既存検査器・assets・registry・project.godot・066への追加変更やremote書込みはない。

配布物は変更7件の全文payload、両親の原文、競合原文、両親と共通祖先からの適用検証patch、全パスのblob/mode/SHA、検証スクリプト、全生ログ、原PNG、入力/矩形/状態JSON、manifest。実行用コピー、キャッシュ、runtime保存データ、転送内部情報は除外する。ZIP全件のCRC・bytes・SHA256を検証する。

未達・未検証：旧coastal検査の既知失敗、親による正式保存・GitHub全CI・main登録、物理コントローラー/利用者PC。ローカル検証成功でこれらを代用しない。
