# 敵の群れの配置と対象一覧（2026年9月28日）

依頼者が採用した味方の足元、72px表示、30px前進、5体の敵配置、y=223・高さ65pxの窓を維持し、次の2点を修正した。

## 敵1〜4体の足元

| 敵数 | 左右中央・足元下端 |
| --- | --- |
| 1 | (170,196) |
| 2 | (120,160)、(220,196) |
| 3 | (215,134)、(90,178)、(180,200) |
| 4 | (110,120)、(215,134)、(90,178)、(180,200) |
| 5 | 従来どおり：(110,120)、(215,134)、(90,178)、(180,200)、(270,186) |

重なりがない通常敵には補正を加えない。大型の敵が重なる場合だけ、実際の表示幅を使い、足元の高さ・元の左右順・0.75倍の表示倍率を保って左右へ動かす。縦方向の範囲が交わる組に必要な横間隔を取り、被弾時の左右3pxの揺れも含めて重ならないようにする。敵の中心は60〜300、描画枠は左24〜右320の間に収め、前進した味方との間にも余白を残す。

大型2体、および大型2体と小型2体の編成で、横補正・高さと左右順の維持・非重複を検査する。これでも物理的に収まらない幅の編成は、無断で敵を縮めたり重ねたりせず、描画時にエラーとして検出する。

## 対象選択

敵・味方の対象を選んでいる間は「ターン実行」「選び直す」「技の効果を確認」を表示せず、左窓の内側140×57pxすべてを名前一覧に使う。通常のコマンド選択へ戻ると3つの操作を表示する。名前・「戻る」・対象カーソル・選択中の敵のHPと行動予定の機能は維持する。

## 検査と画像

前回承認済みの `tools/capture_battle_formation.gd` を新しい指定座標と表示条件へ更新した。非重複・頭部の画素検査・窓内への文字の収まり・対象選択と演出の一致を維持し、大型の横補正と敵・味方双方の一覧拡張を追加確認する。R-01〜R-08と保護ファイル、素材・CI設定は変更しない。

`tools/capture_enemy_groups.gd` は本番の戦闘処理と描画を使う撮影用スクリプト。出現編成や戦闘の強さを変更しない。保存先は `docs/verification/enemy-groups-20260928/`。

- `01-enemies-1.png`〜`04-enemies-4.png`：指定の敵1〜4体。
- `05-target-selection.png`：名前一覧が窓全体を使う状態。
- `06-large-enemies.png`：追加確認用の大型2体。
- `capture-record.json`：各画像の実際の足元座標と版識別。
- `checks/checks.json`：配置・表示の検査結果。

実行方法：

```powershell
. ./tools/prepare_scope_env.ps1
godot --path . --script res://tools/check_battle_head_pixels.gd
godot --path . --script res://tools/capture_battle_formation.gd -- --capture
godot --path . --script res://tools/capture_enemy_groups.gd
python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .
python tools/check_frozen_files.py
python tools/validate_assets.py --strict
```

頭部の範囲と判定方法は `docs/battle-layout-exact.md` から変更していない。今回の採否を依頼者が判断した後に、残り8職へ進む。
