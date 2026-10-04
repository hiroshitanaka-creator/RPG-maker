# 006 村と4室の移動・保存・帰還の接続報告

## 開始・提出対象と前提

- 開始main：`552261345f68a4916ddeefad959896b44da2fcbf`。依頼書：`3ddbbc14289599f529421a3587a5b7973a000545`。
- 実装提出：`8ac824f316aea69954c459409087c9d42bead942`。監督指定mainを取り込んだ検証対象：`927cd60579f08415b27ceab69b4315085fef272f`。報告提出・初回main統合：`37b16815492ca2922fd2850d2e1bae4283bdb3c2`。統合結果だけの報告追記コミットと、その最終CIは最終応答にも記録する。最終コードのCIは [37188213052](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37188213052) 全3ジョブ、[37188213012](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37188213012) 追加1ジョブとも終了・成功。
- 両005は確認済み。開始CI [37183938648](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37183938648) は全3ジョブ成功。開始時の未コミット・未push変更は0件。調査基準345e78eから開始mainへの変更は素材対応依頼書の状態行のみ。
- 指定の同PC作業コピーとして `D:\codex\Documents-Codex\2026-10-04\task-3\repo` に隔離。元 `C:\Users\tanak\RPGゲーム` の35候補は読取・ハッシュ照合だけを行い、状態と全35件のバイトは不変。
- 読んだ正本・入力：AGENTS、伝言板README、006、両005報告、体験仕様、ロードマップ、002報告、村背景・準備・素材規約・建物背景記録、契約・保護一覧、台帳、村・港・海岸JSON、村定義器、本番移動・表示・帰還・保存・UIコード。checkoutに `.agents/skills` は存在しない。
- 監督の追加指示に従いmain `677e5a74937921250ec388c72fb1ceaba0341c8c` の新原画6件を取り込んだ。全バイトを保持し、006へ自動採用していない。開始原画18件、背景・パレット・素材台帳は変更なし。

## 変更ファイル

- `scripts/world/region2_village.gd` とUID、`world/region2_village.json`：既存5背景を参照する接続データ。床や上層の複製管理なし。
- `scripts/world/first_region.gd`、`first_region_travel.gd`、`first_region_presentation.gd`、`first_region_view.gd`：追加読込、出入口・8往復リンク、保存node許可、村内非遭遇、visited・帰還、既存村アイコン。
- `tools/check_region2_village_connections.gd` とUID・Python、`tools/capture_region2_village_connections.gd` とUID、`.github/workflows/region2-village-connections.yml`：006専用の追加検査と証拠作成。既存検査・CIは不変。
- `docs/region2-village-connections.md`、本報告書、`docs/verification/region2-village-connections/**`、`docs/decision-log.md`、`PLAYTEST_QUEUE.md`、006状態行。
- 上流からの原画6件は006の独自差分に数えない。固定比較の `comparison_base` は指定main 677e5a7、開始素材不変の基準は5522613のまま。

## 接続・保存・帰還

実IDは `region2_village`、roomは外観0／宿1／道具屋2／武器屋3／祠4。対応表・座標・向きは [接続記録](../../region2-village-connections.md) を参照。世界入口169,88、港外169,99から既存地上13歩。西アーチ3,13→世界168,88・西向き、東アーチ42,13→世界170,88・東向き。村の西着地4,15、東着地41,15は南向き。4室は8,10へ北向き、8,11から対応する外観扉前へ南向きで戻る。

既存 `save_game/load_game` と `first_region.travel.version=1` を使用。保存版・新項目・新しい規則は追加なし。非初期値のJP・成功回数・マスター・侵蝕30・消耗したHP/MP・所持品も5マップで保持を検査した。保存入力は正常26件・補正入力5件の31実物をsaved-inputs/へ保管した。20状態は5マップ×4方向で、保存ハッシュ・cell・facing・entry_lock・全状態一致を [runtime-checks.json](../../verification/region2-village-connections/runtime-checks.json) に記録。各マップ1例を別プロセスのタイトル再開から読み、壁保存の既存安全補正・通知を実画面で確認して通常歩行で港へ戻った。

初入村時だけvisitedへ村IDを1件追加する。全5マップから既存訪問先へ帰還でき、港から村へも通常メニューで帰還した。選択した生存者だけMP2を消費、村前は世界168,88、所有船は既存第2港155,110。未訪問・未習得・戦闘中・死亡・MP不足の拒否と状態不変を確認。未訪問の旧保存へ訪問を補完しない。

## 自己点検1〜10

| 項目 | 結果・証拠 |
|---|---|
|1 港との徒歩往復・両アーチ|本番APIと通常キーで往復。逆移動・再訪・入力なし・押し続けに往復ループなし。runtime section1、journey/checks.json|
|2 4室・8リンク・客側経路|対応室と方向一致。BFSと本番移動APIで出口・家具前後へ到達。section2|
|3 全セル・閉じた4扉・非遭遇|外観636、宿84、道具78、武器78、祠87床。全セルと全床隣接の実判定一致。非接続4扉に部屋・物語なし。section3・7|
|4 20保存・5再起動|別セッションで全状態一致、全20例で歩行退出。5プロセスの通常タイトル再開・徒歩帰路成功。restart-0〜4.json、restart-0〜4/checks.json|
|5 全保存領域・訪問記録|船・visited・習得・編成・HP/MP・所持金・品・職業・修練・侵蝕・マスター・既存物語フラグ一致。初訪問だけ1件増え、再訪で不変。section5|
|6 旧保存・安全補正・不正拒否|壁・家具・範囲外を既存入口へ補正、5マップの通知を実画面確認。不正node・room・型を拒否し現在状態保持。section6、各再起動の03-position-relocation-notice.png|
|7 機能の誤発火|全5マップのNPC・施設・物語イベント0。受付・祭壇・4閉扉で調べても全状態不変。section7|
|8 本番描画・上層|通常往復28枚、アーチ下・高い手前壁6枚、5再起動・補正通知15枚の計49枚。見える人物画素の全一致、既存上層と通知窓で隠れる画素を別計数。新しい見た目の採用なし|
|9 帰還・回帰・CI|section9の正例・負例、港・現在の第2地方航路・導入・保存・画面回帰を実行。対象CI・R・保護の最終集計は下記（任意の旧検査2件は別記）|
|10 変更範囲・原画不変|固定コミット比較は許可範囲のみ。開始素材等1,559件、PC35候補、原画18件、監督指定追加原画6件不変。scope-checks.json、preservation-checks.json、upstream-preservation.json、original-pc-end-checks.json|

## 検査と実行記録

固定版は `4.7.2.stable.official.ed1daf0bf`。同PCにある実行ファイルをバイト一致でコピーし、自己完結設定と作業用APPDATAを使った。既存検査が追跡済み検証記録を書き換えるため、別の同PC検証コピー `task-3/qa006` で実行し、006用の記録だけを本リポジトリへ採取した。

- `godot --headless --editor --import --quit`：開始・最新main取込み後とも終了0。エラー・警告・資源不明0件。`import-8ac824f.log`、`import-upstream.log`。
- `python tools/check_region2_village_connections.py --commit cbae42a517911e4d7e3c4d48c9690a4219acd548 --godot <固定版>`：終了0。本番API7,592項目（非初期値5例と保存入力31実物の照合を含む）、20保存、別プロセス5例（9／26／37／51／43項目）。固定範囲PASS。
- ネイティブWindows描画で `capture_region2_village_connections.gd`：journey 137項目28枚、details 34項目6枚、restart各17項目3枚。全て終了0。入力・移動・180秒の既存予算を維持。撮影起点は人工の港内境界保存と明示し、村へのワープを証拠に使用しない。ログ・各checks.json・native-evidence-index.jsonを保存。
- `python tools/validate_assets.py --strict`：終了0、画像1134・音15・字体2・パレット3、問題なし。
- 既存村scope・背景・native・palette検査、港背景Python・Godot、村背景Godot：終了0。
- `check_region2_port.gd` 935項目、`check_second_region_coast.gd` 91項目、`check_first_region_gado.gd` 1988項目、導入data検査、`check_saved_position_relocation.gd` 31室199項目、`check_saved_value_types.gd`、`check_first_region_screen.gd` 10項目：終了0。全ログをregressions/へ保存。
- `python tools/run_locked_checks.py`：終了0、R-01〜R-08全8件PASS。`python D:\Codex\.codex\scope-lock\scripts\verify_cli.py`：終了0、全verify成功。保護照合26件一致。
- 実装8ac824fの [既存CI 37186479569](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37186479569) 全3成功、[追加CI 37186479624](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37186479624) 成功。

検査コード最終SHAは `cbae42a517911e4d7e3c4d48c9690a4219acd548`。本番6ファイルのblobは927cd60と同一。取込み後R-01〜R-08全8件、保護26件、素材strictは再実行終了0。保存の通し経路は4人・3人それぞれ359状態・差分0、正式600秒内で成功。`acceptance-summary.json` に受入1〜10と現行回帰を集計。旧任意検査2件の未達は別記し、全コマンド成功とは記載しない。実行していない検査や未終了CIを成功扱いしない。

## main統合の実記録

報告提出37b1681の [既存CI 37189194673](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37189194673) 全3ジョブ、[追加CI 37189194669](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37189194669) 1ジョブの終了・成功を確認。R-01〜R-08成功、保護26件一致、検査不変、許可範囲内の5条件をそろえ、677e5a7から37b1681へ通常fast-forwardでmainに反映した。統合後は検査より先に固定版のimportを実行し、終了0・エラー／警告0件。その後の保護照合も26件一致。

mainの [既存CI 37189466363](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37189466363) 全3ジョブ、[追加CI 37189466355](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37189466355) 1ジョブもすべて終了・成功。実SHAと5条件・全ジョブの結果は [main-integration37b.json](../../verification/region2-village-connections/main-integration37b.json) に記録した。固定比較対象37b1681でも許可範囲のみ、保護・既存検査など2,015件のblobが不変。元PC35候補の内容とGit状態、開始素材等1,559件も再照合して不変。追記は報告と証拠だけで本番コードを変更しない。

## 失敗した試行と担当外の不整合

- 初回importはGodot設定先の書込制約で失敗。作業コピーの自己完結設定へ切り替え、固定版で再実行成功。
- 追加撮影器の初回はJSON座標型の比較と、確認地点からもう1歩進めた向き合わせが原因で失敗。整数化と通常歩行で北向きに到達する経路へ修正して成功。
- 通常ロード通知が人物に重なった初回の画像照合は失敗。通知窓と既存上層の遮蔽を独立計数し、残りの全人物画素一致と5室の安全補正通知を確認して成功。既存画面や検査の条件は変えていない。
- 006の現在の航路回帰とは別に、任意で追加実行した旧 `check_coastal_travel.gd` は `return_learned` 参照エラーで180秒終了124。開始main5522613でも同じエラー・同じ上限で再現。現在の航路検査 `check_second_region_coast.gd` は成功。旧検査や本番の旧拠点仕様は変更していない。`regressions/baseline-coastal.*` を保存。
- 追加の旧本編保存検査の最初の実行は外側の180秒で打ち切られた。正式手動CIのコマンド・上限で再試行。通常経路は4人・3人とも600秒内で終了0、各359状態の差分0。旧保存契約の一括再生は300秒で終了124となり、作業用APPDATAをCのTempへ分離した再試行も同じ上限で124。3人359状態のPASS行までは到達したが、4人側の終了は未検証。既存検査の上限を変更していない。
- 監督指定mainの取り込み1コミットのGit自動要約は英語のまま。履歴の書換えは行っていない。

## 未達・未検証

006の機械受入1〜10は成功。指揮役の実物確認と主観試遊は未実施。任意の旧航路検査と旧保存契約の一括再生は前節のとおり未達で、既存検査の変更は006の許可範囲外。通常保存通し2編成は成功している。

## 自律判断・残作業

指定座標、既存追加読込・保存版・帰還形式、通知窓の画素計数、指定上流原画の固定比較はdecision-logへ理由・戻し方付きで記録した。006の接続だけを通常revertでき、原画を巻き戻す必要はない。

施設サービス、10人の人物採用と接続、品揃え、解放、遺跡は後続に保持。依存する人物・商品・場面が未採用のため006では創作しない。建物の出入りを「4施設完成」「店実装済み」と扱わない。手触りはPLAYTEST_QUEUEへ分離。指揮役の実物確認前の状態は「報告済み」にとどめ、007は開始しない。
