# 076 編成画面のキーボード選択とスクロール・報告

- 検証日：2026-10-20 UTC/JST
- 基点main：`8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`
- 正式依頼HEAD：`269a4a11bf72ca26cc6ed587dad5c5534ac39cda`
- ブランチ：`codex/task-076-party-focus-scroll`
- ローカル修正・検証と成果引渡し。正式Git保存・GitHub全CIは親担当であり、その完了を主張しない。

## 実害と最小修正

現在の「新しくはじめる」→Escape→方向キーで「じょうたい・そうび・へんせい」→Enterで編成へ到達した。状態注入や旧フロー呼出しなしで、Tab移動時に選択項目が画面外へ隠れる実害を再現した。

変更前のTab 5回目は「町の噂・魔物図鑑」の高さ19px中3pxしか可視領域に入らず、6回目の武器選択欄は完全に画面外だった。6回目の焦点矩形は `[49,300,439,19]`、可視部分 `[0,0,0,0]`、scroll_vertical=0。ScrollContainerの表示矩形は `[16,16,480,200]`。座標は512×288内部画面、PNGは1024×576。原PNGで選択枠が消失していることを確認した。

`_render_party` のScrollContainer作成直後に、次の1行だけを追加した。

```gdscript
scroll.follow_focus = true
```

変更後の同じTab 6回目はscroll_vertical=103、焦点矩形と可視部分がともに `[49,197,439,19]` となり、武器欄の選択枠全体が表示された。前後の全入力列をJSONで照合。16回のTabと16回のShift+Tabを含む52判定は変更前11失敗、変更後0失敗。表示操作でゲーム状態全体は不変。

変更は以下3件だけ。

- `scripts/ui/game_root.gd`：追従設定1行。
- `docs/tasks/076-party-focus-scroll.md`：状態行だけ「報告済み」。
- `docs/tasks/reports/076-party-focus-scroll.md`：本報告。

074/075のUI差分は含まない。基点mainから依頼HEADまでの差分は076依頼書のみ。焦点の初期設定、装着・能力・HP/MP・保存・規則は変更しない。画面再生成後は次のTab入力で選択を再開する従来挙動を検証し、焦点位置の自動復元を追加したわけではない。

## 診断範囲と独立期待値

3人/4人×正順/逆順×項目少/多の8ケースを実描画で検査。人数・習得・解放フラグは正規GameSession.import_stateで受け入れる診断状態として投入し、その後は現行通常メニューからキー入力で編成へ入った。初回の無注入再現と区別し、後半の診断状態を通常プレイで到達したものとは扱わない。

- 少：習得1技、初期装着0、通常2枠。
- 多：習得4技、初期装着2、中盤3枠、侵蝕10。技の解除ボタンと清める項目も表示される。
- 全ケースでTab/Shift+Tab、上下左右、仮想十字キー、各仲間へのPopupMenu切替、装着後の再生成、解除、戻る・再表示、Escape、マウスの開閉・装着・解除・ホイールを検査。
- 仲間変更は全員へ実キー操作で切り替え、その都度追従と全状態不変を検査。
- 装着の独立期待値は、選択した末尾の仲間のequipped_abilitiesへ `power_strike` だけを追加した全状態。解除後は追加前の全状態と照合。多ケースでは3枠使用済み状態の追加装着が全状態を変えないことも確認した。
- 方向移動・表示・取消・ホイール・仲間表示変更ではゲーム状態全体を比較。JP・所持品・HP/MP・場所・進行などの変更を許容していない。

| 実描画診断 | ケース数 | 判定 | 失敗 |
|---|---:|---:|---:|
| 3人正順（入力アダプター修正後） | 2 | 643 | 0 |
| 3人逆順 | 2 | 643 | 0 |
| 4人正順 | 2 | 717 | 0 |
| 4人逆順 | 2 | 717 | 0 |
| 仮想アナログ入力の追加検査（headless） | 8 | 232 | 0 |

焦点所有者、全体矩形、可視部分、クリップする親、scroll_vertical/max/page、PopupMenuの選択番号を各入力の前後に記録。単に「焦点が存在する」だけでなく、Tab・矢印・十字キー・追加の軸入力について実際の焦点移動とスクロール変化が各ケースで発生したことを別集計 `input-movement.json` でも確認する。

物理コントローラーは未接続。InputMapに存在する十字キーと左スティックY軸に対応するInputEventを検査した。最初のViewport.push_inputによる軸送信は実移動0だったため軸操作成功とは扱わず、Input.parse_input_eventで入力状態更新を通す追加検査を全8条件で実施して実移動・追従・状態不変を確認した。実機操作やOSごとの差の検証とは区別する。

## 保持した検査失敗

- `diagnostic-3-forward`：314判定中4失敗。PopupMenuにViewport.push_inputだけでは選択入力が届かず、開いたままになった。画面再生成後のTab検査もその状態のまま進んだため、スクロール実発生の判定が失敗した。
- `diagnostic-3-forward-v2`：392判定中2失敗。Input.parse_input_eventでPopupMenuへの入力は届いたが、Homeキーで先頭に戻るという検査側の仮定が不一致。実測ではHome後も選択番号1のままで、Down2回が2→0へ循環した。
- 最終ハーネスでは現在のPopupMenu選択番号ぶん実Upを送り、先頭から必要回数Downを送る。選択番号の直接設定、grab_focus、pressed/item_selectedの直接emitは使用しない。

上記原ログ・途中版ハーネス・JSON・PNGを保持した。ゲーム修正は追従の1行だけで、検査期待値・既存検査・時間上限を変えていない。全実行にタイムアウトなし。準備した未使用のX11キー補助案は実行しておらず、配布対象から除外した。

## 固定環境と既存検証

Godot `4.7.2.stable.official.ed1daf0bf`。archive SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、binary SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。archive内binaryと実行binaryのbytes一致を確認した。

検証はcheckout外の固定HEADコピーで実行。既存検査器、test、保護、素材、project.godotのbytesを固定HEADの全ファイルmanifestと照合し、検査出力を本番checkoutへ混ぜない。

| コマンド | 結果 |
|---|---|
| `timeout 600 godot --headless --editor --import --quit` | 前74.67秒/後6.35秒、exit 0 |
| `timeout 600 godot --headless --import` | 5.73秒、exit 0 |
| `python3 tools/validate_assets.py --strict` | 7.68秒、exit 0。画像1154・音15・字体2・パレット3、問題なし |
| `python3 tools/check_frozen_files.py` | exit 0、保護26件全一致 |
| `python3 tools/run_locked_checks.py` | 136.18秒、exit 0。R-01〜R-08全PASS、各verify既存300秒上限を維持 |
| `timeout 180 godot --headless --path . --script res://tools/check_first_region_screen.gd` | 4.52秒、exit 0、REGION_UI_PASS checks=10 |
| `timeout 240 godot --headless --path . --script res://tools/check_integrated_ui.gd` | 7.03秒、exit 0、INTEGRATED_UI_RESULT failures=0 controls=93 |

R-07はA01〜A14とFIRST_REGION_PASS、R-08は25 tests・3046 assertions、failed/pending 0を確認。既存integrated-ui検査には旧フローと直接signal検査もあるため、それを今回の通常到達再現の代用にはしない。

成功マーカーだけでなくSCRIPT ERROR・Parse Error・ERROR・WARNING・リークを監査。headless成功検査に該当エラー/警告なし。実描画には環境の `Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver.` が各1件ある。Xorgのソケット所有者通知もログに保持した。これを隠したり、実描画が警告ゼロであると報告したりしない。

## 作業契約と引渡し

AGENTS.md、.scope-lock、docs/tasks/README.md、素材規約は075で読んだ内容とのbytes一致を確認。職業・装着枠仕様、現行地方の仕様、該当画面コード・既存検査も確認した。Godotスキルはローカル配置と取得できたクラウド250件・executor0件で見つからず、導入していない。Library保存は現在のLibraryスキルを使用する。

今回の明示依頼に従い、通常のrepo内証拠保存・commit/pushは親の正式保存方式へ分担した。証拠は `/workspace/task076-party-focus-evidence/` のみ。docs/decision-log.mdとdocs/tasks/README.mdへの追記、066、main、利用者PC、remote push/PR/mergeは実施していない。074/075作業木のHEAD・状態・UIファイルハッシュを前後比較する。

作業前後の追跡差分・ローカルrefに対する未push候補をgit-before.txt/git-after.txtへ保存。候補一覧には以前の依頼commitも含まれるため、GitHubに未保存という断定には使わない。076リモート枝をread-only ls-remoteで照合すると依頼HEADと一致し、新規ローカルcommitは作っていない。

ZIPは3ファイル全文（payload）、元bytes（originals）、固定HEADへ適用して全文一致まで検証したpatch、原ログ、R全ログ、加工しない前後PNG17組と比較索引、診断PNG、入力・全状態・矩形JSON、実行ハーネス各版、全ファイルハッシュ、audit、manifestを含む。キャッシュ、検証用コピー、環境変数、転送情報、一時Git indexは除外。ZIP全件のCRC/bytes/SHA256を照合し、保存結果のID・bytes・SHA256を別途返す。

復旧は追従1行を削除し、依頼状態行を戻し、本報告を除けば基点の3パスへ戻せる。

残る未検証は親による正式保存後のGitHub全CI・統合、物理コントローラーおよび利用者実機の操作。ローカル成功で代用せず、正式完了とはしない。
