# スプリント5：入り江・船・帰還の風

## 現在の状態

依頼者はMP2、入り江・停泊船の配置と、`docs/proposals/coastal-travel-checks.md` の検査追加・更新・実行を承認した。固有の境界検査93項目、港町の通常操作65項目、船・帰還の通常操作80項目が成功し、本番撮影12枚を保存した。既存の合否条件・R-01〜R-08・保護ファイル・時間上限は維持した。

確認中に停泊船の整数倍表示に補間がかかっていたため、探索の描画で最近傍を明示した。画像原本や表示位置は変えず、停泊船と航行船の画素一致率は今回の記録で100%。人物の90%以上の画素が見える既存条件も維持した。mainへの反映とmainの全CI結果は、実施後の最終報告で示す。

## 追加した内容

- 港町を40×28タイルにし、右下の入り江へ3本の桟橋を延ばした。桟橋を除いた海面391セルは全体の34.9%。既存の8施設と17人を保ち、配置だけを移した。
- IMG_0974の4方向を切り出し、96×96を4コマ横に配置。向きは下・左・右・上。二値透過、natural.gplの既存64色以内、最近傍縮小。原本のJPEGは不変。
- 船は荷受け所の会話を終えると借りられる。中央の桟橋で乗船し、第1地方の沿岸に出る。港や浅瀬で降り、町の陸地へは徒歩で入る。港の船は素材を整数2倍で表示する。
- 帰還の風は祠の会話を終えると習得する。職業に関係なく生存中の仲間を選び、MP2で訪問済みの村・城下町・港町の入口前へ戻る。船は港へ戻る。未訪問・MP不足・戦闘不能・洞窟や塔の中・戦闘中は拒否する実装。
- 船の位置、乗船状態、習得、訪問先を保存する。旧保存では従来の状態を読めるよう追加状態を任意項目とし、必要になった時点で既知の訪問だけを記録する。
- 世界地形の原本 `world/terrain.json` は変更せず、第1地方の表示・航行用領域を72×40へ広げた。徒歩の到達範囲は従来の範囲を維持する。他地方の拠点はこの区切りで追加しない。
- 海の遭遇率は既存世界マップと同じ0.025、敵は既存の川辺の荒獣、背景は既存の海。敵の能力・技・報酬は変更していない。
- 飛行船の原画・素材・接続は変更していない。

## 確認できる画像

- [船原画と4方向の取り込み結果](verification/sprint5-travel/ship-source-comparison.png)
- [新しい全体配置と停泊船](verification/sprint5-travel/port-with-ship-layout.png)
- [目標画像と入り江・停泊船の比較](verification/sprint5-travel/bay-with-ship-comparison.png)

全体図は配置データと登録した船から描いた見本で、実ゲーム画面ではない。航行・帰還の実画面として提示しない。

## 本番撮影の全場面

以下は本番のGodot描画。開始保存は新規開始から通常操作で村・洞窟・城・塔を越えたものを使い、保存内容のSHA-256を照合してタイトル画面から再開した。位置・仲間・MP・所持品・勝敗・乱数状態は注入していない。

| 場面 | 実画面 |
| --- | --- |
| 入り江と停泊船 | [01](verification/sprint5-travel/runtime/01-bay-docked-ship.png) |
| 乗船前 | [02](verification/sprint5-travel/runtime/02-before-boarding.png) |
| 海を航行中 | [03](verification/sprint5-travel/runtime/03-sailing.png) |
| 通常遭遇した海の戦闘 | [04](verification/sprint5-travel/runtime/04-sea-battle.png) |
| 浅瀬・下船前 | [05](verification/sprint5-travel/runtime/05-shallows-before-landing.png) |
| 浅瀬・下船後 | [06](verification/sprint5-travel/runtime/06-shallows-on-foot.png) |
| 浅瀬・再乗船後 | [07](verification/sprint5-travel/runtime/07-shallows-reboarding.png) |
| 帰還の風・仲間選択 | [08](verification/sprint5-travel/runtime/08-return-caster-selection.png) |
| 帰還の風・行き先選択 | [09](verification/sprint5-travel/runtime/09-return-destination-selection.png) |
| 港町の入口へ戻った直後 | [10](verification/sprint5-travel/runtime/10-returned-to-port.png) |
| 桟橋へ戻った船 | [11](verification/sprint5-travel/runtime/11-ship-returned-to-pier.png) |
| 港で再乗船し、下船した直後 | [12](verification/sprint5-travel/runtime/12-port-disembarked.png) |

## 現時点で実行した検査

- `python tools/check_port_town.py`：全9マップ・16扉・全施設・新しい桟橋・乗船位置への到達が成功。海への徒歩侵入禁止など既存条件は維持。
- `python tools/check_coastal_assets.py`：原本SHA-256、4方向・96px・64色以内・二値透過、3本の桟橋、海面34.9%、港と浅瀬の海上接続が成功。
- `godot --headless --path . --script res://tools/check_coastal_travel.gd`：人工状態の境界検査93項目が成功。拒否時の状態不変、3転移先、選んだ仲間だけMP2消費、船の帰港、旧保存・乗船・下船・航行の保存復元、飛行不可を確認。
- `godot --path . --rendering-method gl_compatibility --script res://tools/prepare_port_departure.gd`：通常到達84項目とR-07の14項目が成功し、未編集の開始保存を作成。
- `godot --path . --rendering-method gl_compatibility --script res://tools/capture_port_town.gd`：港町の通常操作65項目・15画像が成功。
- `godot --path . --rendering-method gl_compatibility --script res://tools/capture_coastal_travel.gd`：船・帰還の通常操作80項目・12画像が成功。278歩・353入力で、既存の600歩・3,000入力・180秒の上限を維持。通常の海の遭遇と戦闘も観測。
- `godot --headless --editor --import --quit`：終了コード0、読込エラーなし。
- `python tools/validate_assets.py --strict`：1,053画像・14音・3パレット・2字体が成功。
- `python tools/check_frozen_files.py`：26件一致。
- `python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .`：R-01〜R-08すべて成功。

人工状態の境界検査と、通常操作での到達・撮影は別の証拠として保存した。海の戦闘後と帰還後の状態も保存・復元して一致を確認した。通常操作の例では海の戦闘で戦闘不能になった仲間がいるため、帰還の仲間選択ではその人物が無効表示になっている。

## 承認範囲で更新した既存検査

`check_port_town.py` は、移動した桟橋・乗船場所の座標と結果保存先だけを変更し、全施設到達・海への徒歩侵入禁止・原画一致などの判定を保持した。`capture_port_town.gd` は、新しい露店・桟橋の撮影位置、結果保存先を指定できる仕組みを更新した。「徒歩のまま」の判定はそのまま保ち、船の借用が追加された現状に合う説明へ直した。新しい船用撮影でも、航行船と停泊船それぞれに90%以上の画素一致を確認する。

## 変更した主なファイル

- `scripts/world/first_region_travel.gd`、`world/first_region_travel.json`：船・乗降・帰還・保存の条件。
- `scripts/world/first_region.gd`、`scripts/world/first_region_view.gd`、`scripts/game/game_session.gd`：移動・訪問先・会話での習得・船の表示。
- `scripts/ui/game_root.gd`、`scripts/ui/first_region_screen.gd`：乗降操作と帰還の仲間・行き先選択。
- `tools/import_owner_ship.py`、`tools/build_port_town.py`、`tools/build_coastal_travel.py`：素材変換・入り江・沿岸と配置画像の再現。
- `tools/check_port_town.py`、`tools/capture_port_town.gd`：承認済みの配置・撮影検査の更新。
- `tools/check_coastal_assets.py`、`tools/check_coastal_travel.gd`、`tools/capture_coastal_travel.gd`：船と転移の固有検査・本番撮影。
- `assets/vehicles/owner_ship.png`、`assets/source_records/owner-ship.json`、`assets/registry.json`：船と出所の記録。
- `world/first_region.json`、`world/interiors.json`、`world/first_region_visuals.json`：港町と沿岸。
- 計画書、決定済みMP2の仕様、原画README、検査具体案、この報告と準備画像。

灯台の岩の岬、海岸線の仕上げ、屋根の統一は計画書へ記録しただけで、今回の修正には含めていない。
