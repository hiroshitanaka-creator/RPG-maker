# 009 検査の世代分離の記録

## 着手前の計画

- 最新main・固定006：`5f1c2ba231191b25b9b32a814b616a9f8d0a54ce`（2026-10-04 fetch実施）。開始SHA：`b9024b8379ea08070fa6b4f61149b257e25277e6`。開始時未コミット0件。main未反映は親登録152cdb1と009登録b9024b8のみで、指定ブランチに保持する。
- 006確認記録と未着手007/008は親承認済み `152cdb18228f377adb2f25e868a59d9649f597e4` の4パスと009登録1パスを独立照合する。009だけ作業中とし、007/008は着手しない。
- 変更予定：AGENTS.md末尾、006専用workflow、tools/check_region2_village_regression.py・.gd・UID、新規009監査/検査/撮影器、docs/verification/task-009/、decision-log、本依頼書の状態行、本報告。既存006検査器・撮影器、ci.yml、保護、本番、素材を変更しない。
- 読込：AGENTS.md、docs/tasks/README.md、006/007/009依頼書、006報告、asset-spec、rpg-plan-v1、experience-spec-v2、設計資料、registry全項目。checkoutと/workspaceの.agents/skillsは存在しない。関連skillはverification-before-completionだけを読む。別委譲・モデル変更なし。
- 元の006：範囲監査＋7592 runtime項目、20方向保存、5別プロセス（件数は実行経路ごとに記録）。runtime・restart各180秒、Godot import600秒、job15分。撮影器はjourney137、details34、restart5回（各17項目、実行時に再計数）、画像49枚・保存入力31件。撮影は各180秒・600移動・3000入力・300ターン。元のcode/期待値/予算を固定側でそのまま実行。
- 開始版の旧006範囲監査は終了1：失敗は007/008/009依頼書だけ（baseline-scope-checks.json）。固定側へ後続登録を混入せず、最新側では009差分監査と継続回帰を実行する。
- 分類案：範囲・原画保全・006依頼書固定は当時だけ。接続・地形・上層・保存・visited・帰還は最新でも継続。全events空、受付/祭壇無反応、祠利用不可は固定側で保持し、最新では007の6人会話/既存宿回復/既存祠条件の正負例へ引き継ぐ。009で未実装サービスをPASSとはしない。
- 期待値は固定006ツリーから別fixtureへ保存し、現在の実装から再生成しない。NPC占有は地形とは別の条件として全セル照合し、入口出口の到達と非占有の全床連結を守る。
- 固定実行SHA異常、扉誤接続、不正保存受理を一時コピーだけで壊して失敗を確かめ、保護・原画は変更しない。
- 全CI/R/保護/範囲/弱体化なしを確認後、通常mergeする。旧任意航路失敗と旧保存契約300秒timeoutは006報告どおり未解決として残す。

## 世代ごとの対応と007への引継ぎ

固定側は常に5f1c2baのGitツリーを別checkoutし、当時のPython/GDScript/撮影器を全バイト不変で実行する。7592項目・20保存・5別プロセスに加え、journey/details/restart0〜4を毎回別jobで撮影し、画像28+6+15=49枚を再検証する。元の歴史証拠は最新側で保存する（既存PNG54枚のうち通常操作49枚、before5枚、入力31件）。後続の依頼書とコードを固定側へ混入させない。

最新側は独立fixtureで世界入口・東西出口・8扉の接続先を固定し、本番APIを検査する。地形・床数・背景・上層・帰還着地も固定006ツリーから保持した値を使う。毎回fixtureを固定Gitツリーと照合するため、現在の実装値を期待値に流用しない。実行checkoutのHEADと指定SHAが異なれば拒否する。

`events空`と受付/祭壇の無反応を最新では要求しない理由は007の明示承認だけである。固定側からは1件も外さない。最新側では非接続4扉の全方向無反応を引き続き検査する。サービスの成功を009のPASSへ混ぜず、下表を007担当の新検査へ渡す。地形の床とNPC占有を全セルで区別し、占有床の隣接へも到達でき、非占有床の全連結と入口・出口・客側セルを通常APIで守る。

| ID | 元の006条件 | 007で追加する正例 | 007で追加する負例 | 009での扱い |
| --- | --- | --- | --- | --- |
| S01 | mapsの全5室events空 | 採用原画の6人が配置され各人へ通常歩行で到達・決定キー会話、こちらを向く。宿のおかみは受付台の後ろ。短い非物語会話を明示一覧 | 人数不足・会話不能・物語の重要内容・港の人物/台詞の流用、NPCが入口出口を塞ぐケースを拒否 | 固定ではevents空を5室全検査。最新ではNPC占有と地形の通行を分離。6人サービス自体は未実装・未検証 |
| S02 | interactionsとcaptureの受付無反応 | 宿の既存休むAPIで全員のHP/MP回復、状態の許された回復差分だけ。所持金37等の入力から新料金なしを検証 | 宿へ入るだけ/遠方から回復、勝手な料金徴収、戦闘中の利用、回復漏れを拒否 | 固定では全方向状態不変。007担当が宿の正負例と通常入力撮影を新設 |
| S03 | 村の祠利用不可、祭壇無反応 | 既存祠の条件を不変で適用。既存許可状態（侵蝕89以下など）で既存の減少30・忘却・解除を実APIと画面で照合 | 侵蝕90以上/不可逆、誤ったイベントID、別の部屋、戦闘中、不明人物、侵蝕0の人間など既存拒否条件と全状態保持を検査 | 固定では祠不可を全位置検査。既存保護/R条件不変。009で村の祠を使えるとは報告しない |
| S04 | 回復/購入/装備/祠/解放/付与なしの混合条件 | 道具屋・武器屋は建物・担当者・会話まで | 会話/入室/決定キーで販売UI、品・金・武器変化、新規商品付与が起きる例を拒否 | 購入/装備/付与禁止は007でも継続し、専用正負例に分解。混合条件の当時版は固定で全保持 |
| S05 | 職業解放・物語イベント0 | 会話・宿・既存祠の利用後に新たな解放場面/採用外進行フラグが増えない | 祠入場だけで解放、007範囲外の人物/名前/規則/遺跡/物語変更を拒否 | C全体の10人・品揃え・解放・遺跡の後続を削らない。今回区切りの6人と区別 |
| S06 | 全床通行・全床連結・描画・20保存/5再起動 | NPCの足元は地形の床のまま占有だけを禁止し、迂回・客側・出入口へ到達。NPC配置後も5マップの保存/安全補正と屋根・葉・高い壁・カメラ端の画素検査を継続 | NPC占有を壁へ書き換える、入口閉塞、NPC上への移動、不正保存の受理、全床または画像検査の省略を拒否 | 009の最新継続検査をそのまま運用し、007の追加正負例を併走する。明示されない新機能を自己判断で合格/skipにしない |

007はこの表に沿う新検査と通常入力撮影を追加する。009では007本文・人物素材・施設機能を変更しない。007が完成するまで最新継続回帰は毎回動く。

## 全assertionの対応表

下表は固定ソースの全check呼出しとPythonの判定/返却を機械列挙した135箇所。ループ内の全反復を含む。固定側では全ソース・条件・上限をそのまま実行する。未分類0は `check_task009_assertion_map.py` が固定ソースから再列挙して照合する。支援関数内のcheckと撮影のcheckも含む。撮影器が継承する保護された通常入力支援と時間・移動・入力・ターン予算は固定側/最新側の両方で同じ原本を継承する。

| ID | 元検査・箇所 | 条件（ループの全反復を含む） | 分類 | 固定側 | 最新側 / 引継ぎ |
| --- | --- | --- | --- | --- | --- |
| A001 | `tools/capture_region2_village_connections.gd:30` `picture` | `castle_check(DisplayServer.get_name()!="headless" and image.get_size()==Vector2i(1024,576),"本番UI・実レンダラー: "+name)` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::picture |
| A002 | `tools/capture_region2_village_connections.gd:31` `picture` | `castle_check(image.save_png(OUTPUT+name+".png")==OK,"本番画面保存: "+name)` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::picture |
| A003 | `tools/capture_region2_village_connections.gd:65` `picture` | `castle_check(shot["visible"]>0 and shot["matched"]==shot["visible"],"足元順で上層外の人物全画素一致: "+name)` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::picture |
| A004 | `tools/capture_region2_village_connections.gd:66` `picture` | `castle_check(shot["hidden"]>=8 and shot["visible"]>=8,"奥の上層による部分遮蔽: "+name)` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::picture |
| A005 | `tools/capture_region2_village_connections.gd:87` `_run` | `castle_check(FileAccess.file_exists(source),"本番save_gameで作られた開始保存")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::_run |
| A006 | `tools/capture_region2_village_connections.gd:89` `_run` | `castle_check(source_sha==FileAccess.get_sha256(DIR+"saved-inputs/"+source.get_file()),"撮影起点がリポジトリの保管済み通常保存と全バイト一致")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::_run |
| A007 | `tools/capture_region2_village_connections.gd:92` `_run` | `castle_check(FileAccess.get_sha256(destination)==source_sha,"開始保存の無編集コピー")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::_run |
| A008 | `tools/capture_region2_village_connections.gd:95` `_run` | `castle_check(await _button(["手動セーブから再開"]) and await _settle(),"タイトルの通常ロード")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::_run |
| A009 | `tools/capture_region2_village_connections.gd:105` `coast_to_village` | `castle_check(_at(_world_point([169,99])),"既存港外を起点にする")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::coast_to_village |
| A010 | `tools/capture_region2_village_connections.gd:109` `coast_to_village` | `castle_check(_at(_world_point([168,88])),"港外から指定の13歩経路で村入口前へ")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::coast_to_village |
| A011 | `tools/capture_region2_village_connections.gd:123` `journey` | `castle_check(_at({"layer":"interior","node":"brine_port","room":0,"cell":[4,2]}),"人工境界保存の港内起点を明示")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A012 | `tools/capture_region2_village_connections.gd:125` `journey` | `castle_check(await _walk(_definition["second_port_exit"],_world_point([169,99])),"通常入力で港出口へ")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A013 | `tools/capture_region2_village_connections.gd:126` `journey` | `castle_check(await coast_to_village(),"通常キー13歩で村へ入場")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A014 | `tools/capture_region2_village_connections.gd:129` `journey` | `castle_check(_state()==stationary,"入場後の入力なしでは再遷移しない")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A015 | `tools/capture_region2_village_connections.gd:131` `journey` | `castle_check(visited.count("region2_village")==1,"初訪問を既存visitedへ1件")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A016 | `tools/capture_region2_village_connections.gd:135` `journey` | `castle_check(await _walk(point(index,[8,10])),"扉から通常入室: "+str(index))` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A017 | `tools/capture_region2_village_connections.gd:142` `journey` | `castle_check(await _walk(point(index,front)),"受付・祭壇・扉前へ通常歩行")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A018 | `tools/capture_region2_village_connections.gd:145` `journey` | `castle_check(await _walk(point(0,[16,9])),"押し続け試験の扉前へ通常退出")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A019 | `tools/capture_region2_village_connections.gd:147` `journey` | `castle_check(_pose().get("room")==1,"扉の上入力を押し続けても室内で進み、往復しない")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A020 | `tools/capture_region2_village_connections.gd:148` `journey` | `castle_check(await _walk(point(1,[8,10])),"出口の押し続け試験へ通常歩行")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A021 | `tools/capture_region2_village_connections.gd:150` `journey` | `castle_check(_pose().get("room")==0,"退出の下入力を押し続けても外観にとどまる")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A022 | `tools/capture_region2_village_connections.gd:151` `journey` | `castle_check(await _walk(point(index,front)),"押し続け試験後に通常再入室")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A023 | `tools/capture_region2_village_connections.gd:153` `journey` | `castle_check(_state()==before,"調べる操作で機能を発火しない")` | 007の承認済み新機能で置き換える現在条件 | 同じソース・行を固定006で全実行 | 007引継ぎ表 S01〜S06（未着手・未検証） |
| A024 | `tools/capture_region2_village_connections.gd:154` `journey` | `castle_check(samples.size()==1 and await _walk(point(index,[samples[0][0],samples[0][1]+1])) and await _step_direction(Vector2i.UP) and _at(point(index,samples[0])),"家具・手前壁の奥へ通常歩行し北向きに立つ")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A025 | `tools/capture_region2_village_connections.gd:157` `journey` | `castle_check(await _walk(point(index,[8,11]),Region2Village.data()["definition"]["region2_village_doors"][index*2-1]["to"]),"対応扉前へ通常退出")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A026 | `tools/capture_region2_village_connections.gd:160` `journey` | `castle_check(await _walk(point(0,[42,13]),_world_point([170,88])),"東アーチから退出")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A027 | `tools/capture_region2_village_connections.gd:163` `journey` | `castle_check(_pose().get("layer")=="world","アーチ退出後の同方向押し続けで往復しない")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A028 | `tools/capture_region2_village_connections.gd:164` `journey` | `castle_check(await _walk(_world_point([169,88]),point(0,[41,15])),"東側から再入場")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A029 | `tools/capture_region2_village_connections.gd:166` `journey` | `castle_check(await _walk(point(0,[3,13]),_world_point([168,88])),"西アーチから退出")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A030 | `tools/capture_region2_village_connections.gd:167` `journey` | `castle_check(await _walk(_world_point([169,88]),point(0,[4,15])),"西側から再入場")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A031 | `tools/capture_region2_village_connections.gd:168` `journey` | `castle_check(_state()["first_region"]["travel"]["visited"]==visited,"再訪問で重複なし")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A032 | `tools/capture_region2_village_connections.gd:170` `journey` | `castle_check(await _key(KEY_ESCAPE) and await _button(["セーブ"]) and await _button(["現在の冒険に戻る"]),"通常メニューの保存")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A033 | `tools/capture_region2_village_connections.gd:171` `journey` | `castle_check(await _walk(point(0,[4,16])),"保存後に一歩移動")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A034 | `tools/capture_region2_village_connections.gd:172` `journey` | `castle_check(await _key(KEY_ESCAPE) and await _button(["手動セーブから再開"]) and await _settle(),"通常メニューの再読込")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A035 | `tools/capture_region2_village_connections.gd:173` `journey` | `castle_check(_state()==before_save,"通常保存の全状態復元")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A036 | `tools/capture_region2_village_connections.gd:175` `journey` | `castle_check(await to_port(),"読込後に通常徒歩で港へ帰着")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A037 | `tools/capture_region2_village_connections.gd:178` `journey` | `castle_check(await _key(KEY_ESCAPE) and await _button(["帰還の風"]) and await _button(["%s MP %d" % [actor["name"],actor["mp"]]]),"既存メニューで帰還と生存者を選択")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A038 | `tools/capture_region2_village_connections.gd:180` `journey` | `castle_check(await _button(["オアシスの村（仮）"]),"訪問済み村を選択")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A039 | `tools/capture_region2_village_connections.gd:182` `journey` | `castle_check(member["mp"]==actor["mp"]-2 and _at(_world_point([168,88])) and after["first_region"]["travel"]["ship_cell"]==[155,110],"港側から村へMP2・既存第2港の船")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::journey |
| A040 | `tools/capture_region2_village_connections.gd:187` `restart_route` | `castle_check(_state()==expected,"別プロセスのタイトル再開で全状態復元")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::restart_route |
| A041 | `tools/capture_region2_village_connections.gd:192` `restart_route` | `castle_check(await _key(KEY_ESCAPE) and await _button(["手動セーブから再開"]) and await _settle(),"本番メニューで壁保存を読み込む")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::restart_route |
| A042 | `tools/capture_region2_village_connections.gd:193` `restart_route` | `castle_check(_session().position_relocated and str(_main.get("_notice")).contains("安全な入口へ移動しました。") and _pose()["cell"]==FirstRegion.entrance_landing("region2_village",index),"既存の安全補正通知と入口への置き直し")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::restart_route |
| A043 | `tools/capture_region2_village_connections.gd:195` `restart_route` | `castle_check(await to_port(),"別プロセス再起動後に通常キーだけで港へ戻る")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::restart_route |
| A044 | `tools/capture_region2_village_connections.gd:200` `details` | `castle_check(await _walk(point(0,[3,14])),"西アーチ下へ通常歩行")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::details |
| A045 | `tools/capture_region2_village_connections.gd:202` `details` | `castle_check(await _walk(point(0,[42,14])),"東アーチ下へ通常歩行")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::details |
| A046 | `tools/capture_region2_village_connections.gd:205` `details` | `castle_check(await _walk(point(index,[7,8])),"高い手前壁の客側へ通常歩行")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::details |
| A047 | `tools/capture_region2_village_connections.gd:208` `details` | `castle_check(await _walk(point(index,[8,11]),Region2Village.data()["definition"]["region2_village_doors"][index*2-1]["to"]),"高い壁の開口部から通常退出")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::details |
| A048 | `tools/capture_region2_village_connections.gd:209` `details` | `castle_check(await to_port(),"詳細撮影後も港へ通常帰路")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::details |
| A049 | `tools/capture_region2_village_connections.gd:212` `finish` | `castle_check(Time.get_ticks_msec()< _deadline and _moves<=LIMIT_MOVES and _input_log.size()<LIMIT_INPUTS and not _input_violation,"既存の180秒・移動・入力予算と禁止操作を維持")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/capture_task009_village_regression.gd::finish |
| A050 | `tools/check_region2_village_connections.gd:29` `preserve_save` | `check(file!=null,"通常保存の実ファイルを006証拠へ保管")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::preserve_save |
| A051 | `tools/check_region2_village_connections.gd:31` `preserve_save` | `check(FileAccess.get_sha256(source)==FileAccess.get_sha256(target),"保管した通常保存の全バイト一致")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::preserve_save |
| A052 | `tools/check_region2_village_connections.gd:46` `game_for` | `check(game.import_state(saved),"本番セッションへ受理: "+str(saved["overworld"]))` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::game_for |
| A053 | `tools/check_region2_village_connections.gd:73` `walk` | `check(not route.is_empty(),"本番移動経路: "+str(goal))` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::walk |
| A054 | `tools/check_region2_village_connections.gd:77` `walk` | `check(game.move_first_region(cell).get("kind")=="moved","一歩移動: "+str(cell))` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::walk |
| A055 | `tools/check_region2_village_connections.gd:84` `leave` | `check(game.export_state()["overworld"]["room"]==0,"保存復帰後の室外退出")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::leave |
| A056 | `tools/check_region2_village_connections.gd:86` `leave` | `check(FirstRegion.at(game.export_state()["overworld"],world([168,88])),"保存復帰後に世界へ退出")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::leave |
| A057 | `tools/check_region2_village_connections.gd:89` `make_base` | `check(game.new_first_region(),"新規状態")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::make_base |
| A058 | `tools/check_region2_village_connections.gd:111` `connections` | `check(game.save_game("user://village006_port-start.json"),"人工開始状態を通常保存（港からの撮影起点）")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A059 | `tools/check_region2_village_connections.gd:113` `connections` | `check(game.move_first_region(Vector2i(4,1)).get("kind")=="moved" and FirstRegion.at(game.export_state()["overworld"],world([169,99])),"既存港出口から世界へ")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A060 | `tools/check_region2_village_connections.gd:116` `connections` | `check(route.size()==13,"既存陸地13歩")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A061 | `tools/check_region2_village_connections.gd:119` `connections` | `check(FirstRegion.walkable(game.export_state(),cell),"指定沿岸セル通行: "+str(cell))` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A062 | `tools/check_region2_village_connections.gd:121` `connections` | `check(result.get("kind") in ["moved","battle"],"港から通常一歩: "+str(cell))` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A063 | `tools/check_region2_village_connections.gd:124` `connections` | `check(FirstRegion.at(arrived["overworld"],p(0,[4,15])) and arrived["overworld"]["facing"]==0,"西側から内側へ南向き着地")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A064 | `tools/check_region2_village_connections.gd:125` `connections` | `check(arrived["first_region"]["travel"]["visited"]==base["first_region"]["travel"]["visited"]+["region2_village"],"初訪問の1件だけ追加")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A065 | `tools/check_region2_village_connections.gd:128` `connections` | `check(unchanged==baseline,"初訪問で他の進行・人物・品不変")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A066 | `tools/check_region2_village_connections.gd:132` `connections` | `check(FirstRegion.at(state,exit_link["to"]) and state["facing"]==exit_link["facing"],"アーチ退出と外向き: "+str(exit_link["facing"]))` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A067 | `tools/check_region2_village_connections.gd:134` `connections` | `check(game.move_first_region(WorldExpedition.point(state["cell"])).is_empty() and game.export_state()==before,"入力なしの再遷移なし")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A068 | `tools/check_region2_village_connections.gd:135` `connections` | `check(game.move_first_region(Vector2i(169,88)).get("kind")=="moved","退出直後の逆移動で再入村")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A069 | `tools/check_region2_village_connections.gd:137` `connections` | `check(game.export_state()["overworld"]["cell"]==landing and game.export_state()["overworld"]["facing"]==0,"東西着地と向き")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A070 | `tools/check_region2_village_connections.gd:138` `connections` | `check(game.export_state()["first_region"]["travel"]["visited"].count("region2_village")==1,"再訪問の重複なし")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A071 | `tools/check_region2_village_connections.gd:139` `connections` | `check(game.move_first_region(Vector2i(landing[0],landing[1]-1)).get("kind")=="moved" and game.export_state()["overworld"]["node"]=="region2_village","入場方向の継続で退出ループなし")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A072 | `tools/check_region2_village_connections.gd:144` `connections` | `check(game.move_first_region(cell).get("kind") in ["moved","battle"],"同じ既存地上領域を徒歩帰路: "+str(cell))` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A073 | `tools/check_region2_village_connections.gd:145` `connections` | `check(game.export_state()["overworld"]["node"]=="brine_port","港へ通常徒歩入場")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A074 | `tools/check_region2_village_connections.gd:150` `connections` | `check(game.move_first_region(WorldExpedition.point(from["cell"])).get("kind")=="moved" and FirstRegion.at(game.export_state()["overworld"],link["to"]),"8本の扉リンク: "+str(from))` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A075 | `tools/check_region2_village_connections.gd:151` `connections` | `check(game.export_state()["overworld"]["facing"]==link["facing"],"扉の着地方向")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A076 | `tools/check_region2_village_connections.gd:156` `connections` | `check((continued.get("kind")=="moved" and game.export_state()["overworld"]["room"]==link["to"]["room"]) if can_move else (continued.is_empty() and game.export_state()==before),"同じ方向の継続で往復せず、採用済みの壁ならその場で止まる")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::connections |
| A077 | `tools/check_region2_village_connections.gd:168` `maps` | `check(FirstRegion.walkable(saved,Vector2i(x,y))==expected,"全セル通行一致: %d %d,%d" % [index,x,y])` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::maps |
| A078 | `tools/check_region2_village_connections.gd:171` `maps` | `check(WorldExpedition.point(saved["overworld"]["cell"])==Vector2i(x,y) or not path(saved,Vector2i(x,y),false).is_empty(),"リンク判定を除いたBFSで全床連結")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::maps |
| A079 | `tools/check_region2_village_connections.gd:176` `maps` | `check(FirstRegion.move(probe,cell).get("kind")=="moved","村の全床・全隣接で非戦闘")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::maps |
| A080 | `tools/check_region2_village_connections.gd:177` `maps` | `check(floors==[636,84,78,78,87][index],"採用済み床数")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::maps |
| A081 | `tools/check_region2_village_connections.gd:178` `maps` | `check(FirstRegionPresentation.map_for(saved["overworld"])==map,"本番表示が既存背景を参照")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::maps |
| A082 | `tools/check_region2_village_connections.gd:181` `maps` | `check(not path(saved,WorldExpedition.point(target),false).is_empty(),"リンク判定を除いたBFSの客側・家具前後到達")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::maps |
| A083 | `tools/check_region2_village_connections.gd:186` `maps` | `check(FirstRegion.room(saved["overworld"])["events"].is_empty(),"村NPC・施設・物語イベント0: "+ROLES[index])` | 007の承認済み新機能で置き換える現在条件 | 同じソース・行を固定006で全実行 | 007引継ぎ表 S01〜S06（未着手・未検証） |
| A084 | `tools/check_region2_village_connections.gd:197` `saves` | `check(game.save_game(filename),"通常保存: "+filename)` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::saves |
| A085 | `tools/check_region2_village_connections.gd:200` `saves` | `check(restored.load_game(filename) and restored.export_state()==saved,"20状態の別セッション完全復元: "+filename)` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::saves |
| A086 | `tools/check_region2_village_connections.gd:201` `saves` | `check(not restored.position_relocated,"正常保存は補正しない")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::saves |
| A087 | `tools/check_region2_village_connections.gd:203` `saves` | `check(restored.export_state()==saved,"船・visited・編成・HP/MP・品・職・修練・侵蝕・マスター・物語フラグ全一致")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::saves |
| A088 | `tools/check_region2_village_connections.gd:205` `saves` | `check(restored.export_state()["overworld"]["layer"]=="world","20状態の読込後歩行・退出")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::saves |
| A089 | `tools/check_region2_village_connections.gd:223` `growth_saves` | `check(game.save_game(file),"村5マップの修練・マスター・侵蝕・消耗状態を通常保存")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::growth_saves |
| A090 | `tools/check_region2_village_connections.gd:226` `growth_saves` | `check(restored.load_game(file) and restored.export_state()==saved,"非初期値のJP・成功回数・マスター・侵蝕30・HP/MP・所持金・品も全一致")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::growth_saves |
| A091 | `tools/check_region2_village_connections.gd:232` `restart` | `check(game.load_game("user://village006_%d_0.json" % index) and game.export_state()==expected,"別プロセス再起動後の完全復元")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::restart |
| A092 | `tools/check_region2_village_connections.gd:234` `restart` | `check(game.export_state()["overworld"]["cell"]==[168,88],"別プロセス読込後の徒歩退出")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::restart |
| A093 | `tools/check_region2_village_connections.gd:242` `invalid_saves` | `check(game.save_game(file),"補正入力の通常保存")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::invalid_saves |
| A094 | `tools/check_region2_village_connections.gd:245` `invalid_saves` | `check(PlaySessionMetrics.write_json("user://village006_relocation_%d.json" % index,relocation),"本番UIの補正通知用入力を保存")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::invalid_saves |
| A095 | `tools/check_region2_village_connections.gd:255` `invalid_saves` | `check(PlaySessionMetrics.write_json(file,doc),"壁・家具・範囲外の保存入力")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::invalid_saves |
| A096 | `tools/check_region2_village_connections.gd:257` `invalid_saves` | `check(restored.load_game(file) and restored.position_relocated and restored.export_state()["overworld"]["cell"]==FirstRegion.entrance_landing("region2_village",index),"既存の入口安全補正")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::invalid_saves |
| A097 | `tools/check_region2_village_connections.gd:259` `invalid_saves` | `check(restored.export_state()==expected,"補正以外の全状態不変")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::invalid_saves |
| A098 | `tools/check_region2_village_connections.gd:260` `invalid_saves` | `check(restored.save_game(file) and restored.load_game(file) and not restored.position_relocated,"再保存後に補正通知が残らない")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::invalid_saves |
| A099 | `tools/check_region2_village_connections.gd:265` `invalid_saves` | `check(not game.load_game(file) and game.export_state()==before,"不正保存拒否と現在状態保持: "+str(change))` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::invalid_saves |
| A100 | `tools/check_region2_village_connections.gd:268` `invalid_saves` | `check(game.save_game(file),"旅情報なし旧保存")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::invalid_saves |
| A101 | `tools/check_region2_village_connections.gd:269` `invalid_saves` | `check(restored.load_game(file) and restored.export_state()==old,"旧保存を旧保存のまま復元")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::invalid_saves |
| A102 | `tools/check_region2_village_connections.gd:271` `invalid_saves` | `check("region2_village" not in old["first_region"]["travel"]["visited"],"未訪問旧保存に村訪問を捏造しない")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::invalid_saves |
| A103 | `tools/check_region2_village_connections.gd:281` `interactions` | `check(entering.move_first_region(WorldExpedition.point(cell)).get("kind")=="moved" and FirstRegion.at(entering.export_state()["overworld"],p(0,cell)),"非接続4扉に踏み込んでも別室へ飛ばない")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::nonconnecting_doors |
| A104 | `tools/check_region2_village_connections.gd:285` `interactions` | `check(game.interact_first_region().is_empty() and game.export_state()==before,"調べても回復・取引・装備・祠・解放・付与なし")` | 007の承認済み新機能で置き換える現在条件 | 同じソース・行を固定006で全実行 | 007引継ぎ表 S01〜S06（未着手・未検証）。非接続4扉はnonconnecting_doorsで現在も全方向無反応を検査 |
| A105 | `tools/check_region2_village_connections.gd:286` `interactions` | `check(not game.at_purification_shrine(),"村の祠を解除施設にしない")` | 007の承認済み新機能で置き換える現在条件 | 同じソース・行を固定006で全実行 | 007引継ぎ表 S01〜S06（未着手・未検証） |
| A106 | `tools/check_region2_village_connections.gd:294` `returns` | `check(game.cast_first_region_return("pc_02",destination["id"]),"村5マップから訪問済み既存先へ帰還: "+destination["id"])` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::returns |
| A107 | `tools/check_region2_village_connections.gd:297` `returns` | `check(after==expected and FirstRegion.at(after["overworld"],FirstRegion.outside(destination["entrance"])),"選択した生存者だけMP2・位置・船以外不変")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::returns |
| A108 | `tools/check_region2_village_connections.gd:298` `returns` | `check(after["overworld"]["cell"]==[168,88] and after["overworld"]["facing"]==1 and after["first_region"]["travel"]["ship_cell"]==[155,110],"村入口前と既存第2港の船")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::returns |
| A109 | `tools/check_region2_village_connections.gd:306` `returns` | `check(game.start_first_region_battle({"kind":"battle","id":"first_region_encounter","enemies":["slime"],"seed":6006})!=null,"負例の本番戦闘開始")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::returns |
| A110 | `tools/check_region2_village_connections.gd:308` `returns` | `check(not game.cast_first_region_return("missing" if negative=="unknown_actor" else "pc_02","missing" if negative=="unknown_target" else "region2_village") and game.export_state()==before,"帰還負例の状態不変: "+negative)` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::returns |
| A111 | `tools/check_region2_village_connections.gd:311` `returns` | `check(game.cast_first_region_return("pc_01","region2_village") and game.export_state()["overworld"]["cell"]==[168,88],"港側から訪問済み村へ帰還")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::returns |
| A112 | `tools/check_region2_village_connections.gd:312` `returns` | `check(game.move_first_region(Vector2i(169,88)).get("kind")=="moved" and game.export_state()["overworld"]["node"]=="region2_village","帰還後に通常入村")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::returns |
| A113 | `tools/check_region2_village_connections.gd:315` `finish` | `check(Time.get_ticks_msec()-started<LIMIT_MS,"180秒の検査上限")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::finish |
| A114 | `tools/check_region2_village_connections.gd:318` `finish` | `check(PlaySessionMetrics.write_json(OUT+filename,report),"検査JSON保存")` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.gd::finish |
| A115 | `tools/check_region2_village_connections.py:45` `git` | `return subprocess.check_output(["git", *args], cwd=ROOT)` | 最新でも継続 | 同じソース・行を固定006で全実行 | 最新側のGit SHA取得・JSON保存・終了判定 |
| A116 | `tools/check_region2_village_connections.py:65` `scope` | `denied = [s for s in changed if s not in ALLOWED and not s.startswith("docs/verification/region2-village-connections/")]` | 当時だけ | 同じソース・行を固定006で全実行 | 固定側のscope（最新の範囲は009専用監査、後続はその段階の監査） |
| A117 | `tools/check_region2_village_connections.py:66` `scope` | `deleted = git("diff", "--diff-filter=D", "--name-only", BASE, target).decode().splitlines()` | 当時だけ | 同じソース・行を固定006で全実行 | 固定側のscope（最新の範囲は009専用監査、後続はその段階の監査） |
| A118 | `tools/check_region2_village_connections.py:70` `scope` | `failures = denied + deleted` | 当時だけ | 同じソース・行を固定006で全実行 | 固定側のscope（最新の範囲は009専用監査、後続はその段階の監査） |
| A119 | `tools/check_region2_village_connections.py:71` `scope` | `if normalize(original) != normalize(current)` | 当時だけ | 同じソース・行を固定006で全実行 | 固定側のscope（最新の範囲は009専用監査、後続はその段階の監査） |
| A120 | `tools/check_region2_village_connections.py:74` `scope` | `return {row.split("\t", 1)[1]: row.split()[2] for row in git("ls-tree", "-r", ref).decode().splitlines()}` | 当時だけ | 同じソース・行を固定006で全実行 | 固定側のscope（最新の範囲は009専用監査、後続はその段階の監査） |
| A121 | `tools/check_region2_village_connections.py:76` `scope` | `if contains_batch3` | 当時だけ | 同じソース・行を固定006で全実行 | 固定側のscope（最新の範囲は009専用監査、後続はその段階の監査） |
| A122 | `tools/check_region2_village_connections.py:77` `scope` | `if set(batch3_changes) != {"A\t"+s for s in BATCH3_ORIGINALS}` | 当時だけ | 同じソース・行を固定006で全実行 | 固定側のscope（最新の範囲は009専用監査、後続はその段階の監査） |
| A123 | `tools/check_region2_village_connections.py:81` `scope` | `if contains_upstream and set(upstream_changes) != UPSTREAM_ORIGINALS` | 当時だけ | 同じソース・行を固定006で全実行 | 固定側のscope（最新の範囲は009専用監査、後続はその段階の監査） |
| A124 | `tools/check_region2_village_connections.py:84` `scope` | `altered = [s for s in original_paths if a[s] != b.get(s)]` | 当時だけ | 同じソース・行を固定006で全実行 | 固定側のscope（最新の範囲は009専用監査、後続はその段階の監査） |
| A125 | `tools/check_region2_village_connections.py:87` `scope` | `return {"status": "PASS" if not failures else "FAIL", "base": BASE, "comparison_base":comparison_base, "preserved_upstream_originals":upstream_changes, "commit": target,<br>            "changed_files": changed, "failures": failures, "protected_and_existing_unchanged": len(original_paths),<br>            "grok_originals_unchanged": len(originals), "preserved_batch3_upstream": BATCH3_UPSTREAM if contains_batch3 else None,<br>            "preserved_batch3_originals": sorted(retained_batch3), "checks_weakened_or_removed": 0 if not altered else None,<br>            "method": "固定開始mainと指定コミットのGitツリー・blobを比較。既存検査・CI全バイト不変。"}` | 当時だけ | 同じソース・行を固定006で全実行 | 固定側のscope（最新の範囲は009専用監査、後続はその段階の監査） |
| A126 | `tools/check_region2_village_connections.py:102` `run_godot` | `report = json.loads((OUT / (name + ".json")).read_text(encoding="utf-8"))` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.py::run |
| A127 | `tools/check_region2_village_connections.py:103` `run_godot` | `ok = result.returncode == 0 and not bad and report["status"] == "PASS" and report["checks"] > 0 and report["execution_sha"] == sha` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.py::run |
| A128 | `tools/check_region2_village_connections.py:105` `run_godot` | `return {"status": "PASS" if ok else "FAIL", "command": command, "exit_code": result.returncode, "errors": bad, "checks": report["checks"]}` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.py::run |
| A129 | `tools/check_region2_village_connections.py:117` `main` | `checks = {}` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.py::main |
| A130 | `tools/check_region2_village_connections.py:118` `main` | `if not args.runtime_only` | 最新でも継続 | 同じソース・行を固定006で全実行 | 固定scopeと最新動作を別jobで必須実行。009差分はcheck_task009_scope.py |
| A131 | `tools/check_region2_village_connections.py:122` `main` | `if not args.scope_only` | 最新でも継続 | 同じソース・行を固定006で全実行 | 固定scopeと最新動作を別jobで必須実行。009差分はcheck_task009_scope.py |
| A132 | `tools/check_region2_village_connections.py:128` `main` | `if len(data["save_states"]) != 20 or {s["room"] for s in data["save_states"]} != set(range(5)) or {s["facing"] for s in data["save_states"]} != set(range(4))` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.py::main |
| A133 | `tools/check_region2_village_connections.py:130` `main` | `if set(data["sections"]) != {"1", "2", "3", "4", "5", "6", "7", "9"}` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.py::main |
| A134 | `tools/check_region2_village_connections.py:132` `main` | `report = {"status": "PASS" if all(s["status"] == "PASS" for s in checks.values()) else "FAIL", "execution_sha": sha, "results": checks}` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.py::main |
| A135 | `tools/check_region2_village_connections.py:135` `main` | `return 0 if report["status"] == "PASS" else 1` | 最新でも継続 | 同じソース・行を固定006で全実行 | tools/check_region2_village_regression.py::main |

## AGENTSへの追記全文


## 検査の世代と段階移行（2026-10-04 依頼者承認）

- 今後の依頼書では、段階限定の状態と変更範囲の受入を、その段階の完成コミットの完全SHAに固定する。別checkoutで当時のコード・期待値・検査器を使い、push/PRのCIで毎回全項目を再検証し、対象SHAと結果を記録する。
- 継続する動作の不変条件は、最新HEADの本番コードに対する回帰検査で毎回確かめる。固定版の成功だけで最新の成功を代用しない。
- 承認済みの次段階へ移るときは、元の全assertionを「当時だけ」「最新でも継続」「承認済み新機能で置き換える現在条件」に分類し、固定側・最新側・後続検査の対応表と新機能の正負例を用意する。当時だけの条件も固定側に全て残す。
- NPCの占有と地形の通行を区別し、入口・出口への到達を守る。未実装の後続機能を成功扱いせず、引継ぎと未検証を明示する。
- 検査項目の削除・省略・黙ったskip・continue-on-error・実装から期待値を作る自己一致・時間上限の延長で合格させない。別job化する場合も既存の各job・コマンド上限を超えない。時間が不足する場合は証拠とともに報告する。
- この追記は既存の権限・保護・承認の規則を変更しない。

## CIで検出した検査道具の修正

初回842306fのCIは、負例用コピーにlatest出力がまだ無いときrmtreeが終了1となった。クリーンコピーでlatestを生成する方式へ修正し、古い結果JSONも実行前に除く。警告や機能失敗を許容する変更ではない。最新回帰の帰還期待値を全帰還先の固定位置・向き・entry_lock・船位置で独立化し、船未所有も追加、表示map全体の固定照合を追加した。既存の段階限定条件は固定側で全て維持する。

試作時のローカル動作証拠は未コミットの検査器を含むため、表示された当時のHEADだけを厳密な実行コードSHAとは扱わない。最終のCIはclean checkoutのGITHUB_SHAを実行し、最新runnerは本番・検査器・期待値の未コミット変更も拒否する。固定006は初めから別checkoutの完成SHAとコードが一致する。

## 提出と実行結果

完成コードSHA：`d3a9c48b8328085fb79736791d29588915d34b2a`。実装842306f、クリーンコピーと独立期待値の補強d3a9c48を通常commit/push。報告版7b2e883の全40CI成功後、独立レビューによりNPC正例の壁配置を発見し、009専用正負例を追加補強した。最終補強版SHAとCIは下の追記に記録する。本番コードは変更しない。PRは [#16](https://github.com/hiroshitanaka-creator/RPG-maker/pull/16)。開始mainと最終統合直前のmainはともに5f1c2ba（再fetch実施）。

| コマンド | 実行対象・結果 | 証拠 |
| --- | --- | --- |
| `godot --headless --editor --import --quit`（timeout600） | 規定4.7.2、固定/最新とも終了0・エラー/警告0 | fixed-import.log、latest-import.log |
| `python tools/check_task009_lifecycle.py --fixed-path <別checkout> --fixed-sha 5f1c2ba… --godot <規定版>` | 固定006のscope PASS、7592項目、20状態、5別プロセスPASS。ローカル全体36.034秒 | fixed/lifecycle-summary.json、fixed/各JSON・log・保存実物 |
| 同上 `--capture journey/details/restart-0〜4` | 固定の137/34/17×5項目、49枚。全mode終了0、警告/エラー0。各180秒内 | fixed-render/各mode/checks.json・PNG・execution.log |
| `python tools/check_region2_village_regression.py --commit HEAD --godot <規定版>` | clean d3a9c48で7662項目、20状態、5別プロセスPASS。全6プロセス計33.947秒 | latest/regression-summary.json、各JSON・log・保存実物 |
| 同上 `--capture journey/details/restart-0〜4` | 最新の132/34/17×5項目、49枚、全mode終了0・警告/エラー0。ローカル画面は842306fの試作、最終d3a9c48の全画面はpush/PR CIで実行し成功 | latest/各mode、ci/d3-push-jobs.json、d3-all-checks.json |
| `python tools/test_task009_lifecycle.py --fixed-path <別checkout> --godot <規定版>` | 誤SHAは終了1、扉0の室1→2は終了1・扉assertion失敗、不正room5受理は終了1・拒否assertion5失敗。timeout/Parse Error0。旧7662項目のコピー正例はNPCが壁上のため占有実証として無効。床配置の補強正例は7656項目PASS、配置前後の各39項目と占有無視負例で別途実証 | negative-cases/summary.json と全負例JSON/log |
| `python tools/check_task009_assertion_map.py` | 135箇所、未分類0、fixture固定006一致 | assertion-map.json / .md、CIログ |
| `python tools/run_locked_checks.py` | R-01〜R-08全8件PASS、全体テストと14条件の通常操作通しを含む。最終d3a9c48も既存CIで全件PASS | locked-results.json、locked-checks.log、CI Godot jobのPASSマーカー |
| `python tools/check_frozen_files.py` | 保護26/26一致 | CI各jobの照合・scope監査 |
| `python tools/validate_assets.py --strict` | 終了0、問題なし | assets-strict.log、既存CI素材job |
| `python tools/check_task009_scope.py --commit HEAD` / `--worktree` | 009担当内、削除0、既存CI/検査/本番/素材不変。親承認4パスと007/008保持 | scope-checks.json、preservation.json |
| `git diff --check` / Pythonコンパイル | 終了0 | ローカル実行 |

原画を含む2181パスの開始SHAからのSHA-256一致、assets/_incoming/334件不変を全件記録した。009範囲監査では既存検査も含む2423保全パスを照合。006の歴史PNG54枚（通常操作49枚+before5枚）・入力31件は1バイトも変えない。元の006検査器・撮影器・ALLOWEDとci.ymlは不変。007/008本文・状態行も親152cdb1と全バイト一致。

分類数：最新でも継続 121箇所, 007の承認済み新機能で置き換える現在条件 4箇所, 当時だけ 10箇所。各コマンド180秒、import600秒、追加job15分を全て維持。撮影の600移動・3000入力・300ターンも不変。画像49枚を固定側/最新側で欠かさず毎回別jobで検証する。

## 完成コードの全CI（全job終了確認済み）

- d3a9c48 push：通常CI [37193610582](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610582) 全3、専用CI [37193610575](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575) 全17が成功。
- d3a9c48 PR：通常CI [37193612812](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193612812) 全3、専用CI [37193612767](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193612767) 全17が成功。計40/40。PR側のcheckoutはGitHub合流候補SHA、固定側は常に5f1c2baである。
- 初回842306fの通常CI3件は成功、専用CIは16成功/負例道具のディレクトリ前提1失敗。失敗を成功扱いせず、ci/842-negative-failure.logを残した。修正後は固定/最新の項目・予算を保って全job成功。

下表の時間はGitHub job全体（setup/import/uploadを含む）。実行コマンド単体の時間・件数・対象SHAはci/d3-push-jobs.jsonへ実測ログから保存した。PR側全jobの開始/終了/所要時間と結果はci/d3-all-checks.jsonに保存。

| job（push） | 実行コードSHA | 結果・件数 | 時間（秒） |
| --- | --- | --- | --- |
| [lifecycle-audit](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410769971) | d3a9c48（最新） | success / 135分類・範囲・負例3/正例1 | 158 |
| [normal-input-and-rendering (latest, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770097) | d3a9c48（最新） | success / 17項目 / 3枚 | 153 |
| [acceptance-and-regression (latest)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770132) | d3a9c48（最新） | success / 7662 / 20保存 / 5再起動 | 102 |
| [acceptance-and-regression (fixed)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770136) | 5f1c2ba（当時の原本） | success / 7592 / 20保存 / 5再起動 | 118 |
| [normal-input-and-rendering (latest, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770151) | d3a9c48（最新） | success / 34項目 / 6枚 | 172 |
| [normal-input-and-rendering (fixed, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770165) | 5f1c2ba（当時の原本） | success / 17項目 / 3枚 | 175 |
| [normal-input-and-rendering (latest, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770175) | d3a9c48（最新） | success / 132項目 / 28枚 | 235 |
| [normal-input-and-rendering (latest, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770178) | d3a9c48（最新） | success / 17項目 / 3枚 | 152 |
| [normal-input-and-rendering (fixed, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770188) | 5f1c2ba（当時の原本） | success / 17項目 / 3枚 | 142 |
| [normal-input-and-rendering (fixed, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770216) | 5f1c2ba（当時の原本） | success / 17項目 / 3枚 | 127 |
| [normal-input-and-rendering (fixed, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770218) | 5f1c2ba（当時の原本） | success / 17項目 / 3枚 | 213 |
| [normal-input-and-rendering (fixed, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770221) | 5f1c2ba（当時の原本） | success / 17項目 / 3枚 | 156 |
| [normal-input-and-rendering (latest, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770236) | d3a9c48（最新） | success / 17項目 / 3枚 | 159 |
| [normal-input-and-rendering (fixed, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770239) | 5f1c2ba（当時の原本） | success / 34項目 / 6枚 | 201 |
| [normal-input-and-rendering (latest, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770257) | d3a9c48（最新） | success / 17項目 / 3枚 | 161 |
| [normal-input-and-rendering (latest, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770272) | d3a9c48（最新） | success / 17項目 / 3枚 | 192 |
| [素材検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610582/job/111410770115) | d3a9c48（最新） | success / 既存の全検査（GodotはR全8件） | 76 |
| [Godot・凍結受入テスト](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610582/job/111410770182) | d3a9c48（最新） | success / 既存の全検査（GodotはR全8件） | 219 |
| [normal-input-and-rendering (fixed, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610575/job/111410770258) | 5f1c2ba（当時の原本） | success / 137項目 / 28枚 | 248 |
| [試遊前の通常戦闘・案内・画面・復帰検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37193610582/job/111410770223) | d3a9c48（最新） | success / 既存の全検査（GodotはR全8件） | 265 |

## main反映と残る制約

全CI・R全件・保護不変・弱体化なし・担当範囲内の5条件を実証した。報告・証拠を提出し、そのCIも全job確認後にPR #16を通常mergeする。main反映SHAと統合後CIは反映後の追記・最終応答に記録する。強制push/履歴変更/原画削除は行わない。

- 009の固定/最新の機械検査は成功。独立レビュー後の追加補強CIも全終了を確認してから完了する。007/008は未着手・未発注のまま。6人会話・宿・祠の機能は009で実装も成功扱いもしない。S01〜S06の正負例の実装は007担当へ引継ぐ。
- 006に既存の任意旧航路検査の失敗（return_learned参照）と旧保存契約300秒timeoutは未解決として保持する。009で再実行して改善したとは報告しない。現在の航路・保存は既存CIの対象で成功。
- 人間の主観試遊と約60時間の実測、物理音声機器の聴感検証は未実施。009は検査分離の依頼で、これらを完成扱いにはしない。
- CI基盤のNode.js 20非推奨は既存の警告。Godotログの警告0と区別する。既存ci.ymlやGUTを修正しない。
- 判断依頼は0件。007/008を開始しない。

## 変更ファイル一覧

全パスは `docs/verification/task-009/changed-files.txt` に列挙。コード/ルール：AGENTS.md、.github/workflows/region2-village-connections.yml、tools/check_region2_village_regression.py/.gd/.gd.uid、tools/capture_task009_village_regression.gd/.gd.uid、tools/check_task009_scope.py、tools/check_task009_lifecycle.py、tools/check_task009_assertion_map.py、tools/test_task009_lifecycle.py。文書：decision-log、009状態行、本報告。証拠・独立fixture・対応表・全CI・負例・保存実物・画像はdocs/verification/task-009/だけ。親登録006確認/007/008と009依頼書の持込みは009開始SHA以前の変更として分離。

## 独立レビュー後のNPC正負例補強

d3a9c48と報告版7b2e883のコピー正例で使った `[18,13]` は固定fixtureの壁 `#` だった。旧7662件PASSを「床上NPC占有の実証」とした報告は誤りとして訂正する。Git履歴に旧結果を保持し、検査項目や予算を変えず床 `[20,25]` と隣接 `[20,26]` の明示検査へ補強した。007の人物・会話・宿・祠は実装しない。

| コピー検査 | 観測結果 | 判定と証拠 |
| --- | --- | --- |
| NPC配置前 | 固定/実地形とも `.`、通行true、入口 `[4,15]` から隣接へ本番通常歩行、床への移動 `moved` | 39項目PASS、negative-cases/npc-floor-before.json |
| NPC配置後 | 地形 `.` を保持、占有true、通行false、同じ隣接まで到達、床への実移動空・全状態不変 | 39項目PASS、npc-floor-after.json |
| 後続登録＋床上NPCの全継続回帰 | 7656項目、20保存、全床/占有/入口出口の検査がPASS。7662との差は占有セルと隣接辺を通行対象から外し、占有隣接到達を実行した結果 | registered-request-and-npc-occupancy.json |
| 占有拒否を無効化した負例 | NPCがいる床へ通行・実移動が成功し、通行拒否と状態保持の2assertionが失敗 | 終了1・39項目・2失敗、npc-occupancy-ignored.json。timeout/parse errorを成功扱いしない |

プローブの全ソースはnegative-cases/npc-probe-source.gd.txtに保管。別コピーの新規一時検査から、本番APIと継続回帰の経路支援を呼ぶ。配置前後の固定地形・NPC有無・通行・位置・実移動・全状態を実行JSONに残す。原画、本番データ、本番コードは元ツリーへ書き込まない。旧固定SHA・誤接続・不正保存受理の3負例も省略せず併走する。

補強のローカル実行は7b2e883上の未コミット009道具で実行（negative-cases/summary.jsonのexecution_shaは土台HEAD）。クリーンな完成commitでの同じ正負例は提出後のCIで再実行し、全jobとともに記録する。
