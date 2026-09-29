# スプリント5：入り江・船・帰還の風

## 現在の状態

船の素材、入り江の配置、船・帰還の風の本番接続を追加した。Godotの読込と既存の素材・凍結・R-01〜R-08の検査は成功した。**船・転移の固有検査と実ゲームでの航行・帰還の撮影は未実施。今回の区切りは未完了。**

依頼者は帰還の風をMP2にする案へ回答済み。別に提示した、船・転移の追加検査と港町の配置・撮影検査の更新への回答を待っている。具体的な条件は `docs/proposals/coastal-travel-checks.md` に保存した。既存の合否条件や時間上限を変更して合格させる案ではない。

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

## 現時点で実行した検査

- `godot --headless --editor --import --quit`：終了コード0、読込エラーなし。
- `python tools/validate_assets.py --strict`：1,053画像・14音・3パレット・2字体が成功。
- `python tools/check_frozen_files.py`：26件一致。
- `python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .`：R-01〜R-08すべて成功。

これらは既存部分の回帰検査であり、新しい船・転移の通常操作を実際に通した証拠ではない。新規の固有検査、港町検査の配置更新、船に乗る・航行する・帰還する実画面の撮影は、検査変更への承認後に行う。

## 変更した主なファイル

- `scripts/world/first_region_travel.gd`、`world/first_region_travel.json`：船・乗降・帰還・保存の条件。
- `scripts/world/first_region.gd`、`scripts/world/first_region_view.gd`、`scripts/game/game_session.gd`：移動・訪問先・会話での習得・船の表示。
- `scripts/ui/game_root.gd`、`scripts/ui/first_region_screen.gd`：乗降操作と帰還の仲間・行き先選択。
- `tools/import_owner_ship.py`、`tools/build_port_town.py`、`tools/build_coastal_travel.py`：素材変換・入り江・沿岸と配置画像の再現。
- `assets/vehicles/owner_ship.png`、`assets/source_records/owner-ship.json`、`assets/registry.json`：船と出所の記録。
- `world/first_region.json`、`world/interiors.json`、`world/first_region_visuals.json`：港町と沿岸。
- 計画書、決定済みMP2の仕様、原画README、検査具体案、この報告と準備画像。

灯台の岩の岬、海岸線の仕上げ、屋根の統一は計画書へ記録しただけで、今回の修正には含めていない。
