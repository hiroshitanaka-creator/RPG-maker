# 残り8職の歩行素材（2026年9月28日）

12職の戦闘素材は依頼者が採用済み。今回は盗賊・狩人・薬師・吟遊詩人・騎士・賢者・剣士・祈祷師の歩行を追加した。各職4人×4方向×3コマで、32シート・384コマ。完成済み4職の歩行と同じ1コマ32×48、全体96×192、上から下・左・右・上、再生順0→1→0→2、接地行47、16色以内、アルファ0/255。左右は別作画で、単純反転ではない。

## 原画と色

- 付録BのIMG_1022〜1029を衣装、採用済み人物設定画を顔・髪・体格、完成済み歩行原画を頭身・並びの基準にした。組み込みimagegenで2人ずつ、各職2枚を生成した。
- 生成原画16枚は `assets/_incoming/walk-eight-2026-09-28/`。指示全文・参照・原本のSHA-256は `assets/source_records/walk-eight-generation.json`。
- 取り込みは `tools/import_remaining_walks.py`。透明領域から分割し、人物ごとに12コマ共通の倍率で最近傍縮小、二値透過、足元を整列する。
- 頭髪と顔の保護領域は、切り出した人物の上部44%にある不透明画素。既存の衣装色判定で大きな緑・赤の衣装面を除き、小さな目・口は残す。この領域は完成済み4職の固定16色へ、同じRGB最近傍の対応で変換する。
- 顔に実際に必要な色を優先して確保し、16色の残り枠を衣装へ使う。候補は固定16色と、その職業の採用済み戦闘素材で使った衣装色。すべて既存のnatural.gpl内から選ぶ。歩行の色数上限、パレット、既存素材は変更していない。
- 切り出し領域・倍率・使用色・顔色を固定した画素数・出力SHA-256は `assets/source_records/walk-eight-conversion.json`。

## 接続と画面修正

`data/character_visuals.json` の各人物・各職業に歩行画像の参照を追加した。村と世界マップの本番描画は、現在の職業からこの参照を選ぶ。侵蝕・魔物化の優先表示は既存のまま。

戦闘画面では `scripts/ui/first_region_screen.gd` のボタン文字を左寄せにした。「ターン実行」が同じ列の長いボタン幅に合わせて中央寄せになるずれを解消する。機能・言葉・配置・窓の寸法は変更していない。

## 確認画像と検証の範囲

`docs/verification/sprint3-walk-eight/` に保存した。

- `all-twelve-walks.png`：12職×4人×4方向×3コマ、計576コマの一覧。
- `<job>-walk-sheet.png`：新8職ごとの3倍拡大一覧。
- `<job>-reference-comparison.png`：上が依頼者原画、下が取り込み結果。
- `runtime/village-<job>.png`：職業を適用したカイナが村で移動している本番描画。12職分。
- `runtime/world-<job>.png`：同じく世界マップの12職分。
- `runtime/command-left-aligned.png`：コマンド修正後。

`tools/capture_remaining_walks.gd` は12職×4人の衣装参照・4方向・再生順・12回の保存復元を検査する。村では新規開始から通常移動で家を出て、リオネとハルドの加入処理を通り、村から世界マップへ歩く。衣装だけは既存の `GameSession.change_job` で撮影用に適用する。各職で位置が変わり、歩行コマに応じて画面が変わることを確認する。村の転職未解放条件は維持しており、物語中で転職を解放した通しプレイの証明ではない。

コマンドは「攻撃」「回復薬」「ターン実行」「技の効果を確認」の4行について、左寄せと文字描画開始位置の一致を検査する。

ローカルの撮影検査は1,900項目成功。素材検査は画像635件・音14件・パレット3件・字体2件に問題なし、保護対象は26件一致。全8職を再取り込みして32シートのバイト一致を確認した。最初のR検査は実行環境の保存先アクセス制限で失敗したため、検査・上限を変えずにアクセス権限を付けて再実行し、R-01〜R-08すべて成功した。結果は確認画像フォルダの `r01-r08.txt` に保存。CIの最終結果は作業報告を参照する。

`tools/build_remaining_walk_review.py` は開始時コミットe76c774に対し既存603画像・3パレットが不変であることを確かめ、`asset-checks.json` に保存する。R-01〜R-08、保護された26ファイル、既存の検査条件は変更しない。

```powershell
. ./tools/prepare_scope_env.ps1
python tools/import_remaining_walks.py --jobs thief hunter apothecary bard knight sage swordsman shaman
python tools/build_remaining_walk_review.py
python tools/validate_assets.py --strict
python tools/check_frozen_files.py
godot --headless --editor --import --quit
godot --path . --rendering-method gl_compatibility --script res://tools/capture_remaining_walks.gd -- --capture
python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .
```

これで12職×4人の歩行・戦闘素材を用意した。今回の歩行素材の採否は確認画像への依頼者の回答を待つ。スプリント4には進まない。
