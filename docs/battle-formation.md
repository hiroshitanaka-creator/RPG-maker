# 戦闘画面の味方を縦1列に変更

2026年9月27日。戦士・武闘家・僧侶・魔法使いの衣装は依頼者が採用済み。今回は衣装を変更せず、戦闘画面の配置だけを独立して修正した。残り8職はこの配置の確認後に進める。

## 配置と連動する表示

- `scripts/ui/rpg_battle_view.gd` の `party_rect()` を味方の配置元にした。全員の左端は448px、画像は48×48pxの原寸、上下の間隔は56px。4人は上端36・92・148・204px、3人は64・120・176pxで、上から隊列順に並ぶ。
- 平原背景は、既存画像の草地部分を縦横同じ倍率で拡大表示する。上端の空と下端の前景の花が人物に重ならないようにした。背景画像・衣装画像のファイル自体は変更していない。
- `scripts/ui/first_region_screen.gd` では、行動予定・能力値・戦闘結果の窓を右端418pxまでに収めた。人物の左端448pxと重ならず、選択カーソルの領域も残る。
- 攻撃と被弾の表示、回復・蘇生の光、ダメージと回復の数字、対象カーソルは `actor_rect()` から座標を求める。数字は既存の戦闘結果の `amount` を使い、計算式は変更していない。
- 対象ボタンのキーボード選択・マウス指示で、対象の隣へカーソルを移す。行動する味方の足元を強調する。戦闘不能は再生中のHPを参照して、同じ位置に被弾姿勢と暗い色で表示する。
- R-01〜R-08、26件の凍結ファイル、既存の検査条件は変更していない。凍結要件・受入文書・保護テストには2×2の配置を要求する条件はない。

## 確認画像

`docs/verification/battle-formation/` に保存した。4人開始・転職・戦闘の共通APIで用意した見本を、本番の `FirstRegionScreen` と `RpgBattleView` で描画している。物語で4人目が加入したことや、転職が解放されたことを示す画像ではない。

| ファイル | 内容 |
| --- | --- |
| `01-party-four.png` | 4人の縦隊と実際のコマンド・能力値窓 |
| `02-party-three.png` | 3人の縦隊と実際のコマンド・能力値窓 |
| `03-attack.png` | 通常の戦闘計算から得た攻撃結果の描画 |
| `04-target-cursor.png` | 敵の攻撃で被弾した味方を回復薬の対象として選択 |
| `state-damage.png` | 末尾の味方への被弾表示の見本 |
| `state-heal.png` | 末尾の味方への回復表示の見本 |
| `state-revive.png` | 末尾の味方への蘇生表示の見本 |
| `state-fallen.png` | 末尾の味方の戦闘不能表示の見本 |

`state-*` は表示状態を確認するためのイベント見本であり、戦闘の結果や勝敗の証明には使わない。

## 再実行

```powershell
. ./tools/prepare_scope_env.ps1
godot --path . --script res://tools/capture_battle_formation.gd -- --capture
godot --headless --path . --script res://tools/capture_battle_formation.gd
python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .
python tools/check_frozen_files.py
python tools/validate_assets.py --strict
```

撮影スクリプトは現在の本番描画を呼ぶ継続用の検査で、過去の素材変更を比較する一時検査ではない。隊列順、同一の横位置、等間隔、人物同士・文字窓との非重複、演出の位置、実際の対象ボタンとカーソルの連動、再生時点のHPを検査する。実描画では127項目が成功した。実行ログと版情報は `docs/verification/battle-formation/checks.json` に記録する。
