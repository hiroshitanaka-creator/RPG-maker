# 残り8職の戦闘素材（2026年9月28日）

盗賊・狩人・薬師・吟遊詩人・騎士・賢者・剣士・祈祷師の戦闘素材を追加した。各職4人×待機・攻撃・被弾の3動作、合計32シート・96コマ。1コマ96×96、シート288×96、左向き、画面上72px、二値透過、接地行95。確定済みの戦闘配置と完成済み4職の画像は変更していない。今回の対象は戦闘素材で、残り8職の歩行素材は制作していない。

## 原画と制作

`docs/roadmap-v2.md` 付録BのIMG_1022〜1029を衣装の基準とし、採用済み人物設定画と完成済み戦闘原画を参照して、組み込みimagegenで各職1枚の4人×3動作原画を生成した。元の依頼者原画は変更していない。

- 生成原画：`assets/_incoming/battle-eight-2026-09-28/`
- 使用した指示全文：`assets/source_records/battle-eight-generation.json`
- 切り出し、倍率、固定色、追加色、原画と出力のSHA-256：`assets/source_records/battle-eight-conversion.json`
- 取り込み：`tools/import_remaining_battles.py`。既存の4職と同じ分割・最近傍縮小・接地位置の処理を使う。
- 職業と画像の接続：`data/character_visuals.json`。戦闘画像の参照だけを追加し、歩行は既存の参照へ戻る。

## 固定色と衣装色

依頼者承認により、仲間の戦闘素材の上限を全職共通20色へ変更した。既存台帳では人間・魔物化の仲間戦闘56項目の上限だけを変更し、画像そのものは再配色していない。歩行・敵・背景などの上限、サイズ、透過、接地、出所の検査条件は維持する。

顔まわりは完成済み4職と同じ固定16色で変換する。追加色は衣装の該当色面だけに適用する。緑の目や口に当たる顔付近の小さな色面は衣装から分けて固定色へ残す。生成りの追加色は上半身の髪・顔と暖色の肌を対象外にした胴衣・道具の部分へ適用する。固定色へ回す画素が、従来の16色変換から変わっていないことを取り込み時に確認する。

| 職業 | 固定16色に加える衣装色 | 実際のシート色数（4人） |
| --- | --- | --- |
| 盗賊 | 212F14、314619、505F26、5B6B29 | 19・20・18・20 |
| 狩人 | 同上 | 20・20・17・20 |
| 薬師 | B5AA95、D9CCB4、E9E7CB、58544C | 20・20・20・20 |
| 吟遊詩人 | 追加なし | 15・15・14・15 |
| 騎士 | 追加なし | 16・16・16・16 |
| 賢者 | B5AA95、D9CCB4、E9E7CB | 19・19・17・19 |
| 剣士 | 3D0B14、5A170E、74281B、B3433F | 20・20・20・20 |
| 祈祷師 | D9CCB4、E9E7CB | 17・18・16・17 |

剣士の深紅4色は依頼者の追加承認に基づき、IMG_1028の実在画素から採取して `natural.gpl` の末尾へ追加した。既存64色の順序・値は不変で、現在は68色。採取位置は `assets/source_records/natural-crimson-extension.json`。剣士専用パレットは作っていない。`tools/validate_assets.py` の変更は、natural.gplの総色数上限を64から68へ変える条件と表示だけで、他のパレットは64色のまま。

## 確認画像

保存先：`docs/verification/sprint3-battle-eight/`。

- `<job>-battle-sheet.png`：各職の4人×3動作。2倍の最近傍表示。
- `<job>-reference-comparison.png`：上が依頼者原画、下が96pxの取り込み結果。
- `all-twelve-jobs.png`：完成済み4職と今回8職、計12職×4人×3動作。
- `runtime/<job>.png`：職業適用後の本番戦闘画面。12職分を保存。

初期の色数調査と深紅追加前の比較は、`identity-color-audit.*`・`swordsman-color-limit.*` として経緯を残す。これらにある停止・色差の記述は追加承認前の状態で、最終の剣士画像は `swordsman-reference-comparison.png` を参照する。

## 検証

`tools/capture_remaining_battles.gd` は既存の `GameSession.change_job` で撮影用の編成を用意し、12職×4人×3動作の参照と寸法、12回の保存・別インスタンスへの読込を検査する。通常の `choose_job` の解放条件は変更せず、最初の地方と上級職が未解放の状態を維持することも確認する。画面は本番の `FirstRegionScreen` と `RpgBattleView` を使用しており、物語中で上級職の解放まで遊んだ証拠ではない。

`asset-preservation.json` に、作業開始前のコミットb1723c0に対して既存571画像が不変、既存台帳は対象56項目の上限だけ変更、既存64色不変、新32シートの原本・出力ハッシュ一致を記録した。固定16色は変換記録にも全件保持している。

```powershell
. ./tools/prepare_scope_env.ps1
python tools/append_owner_crimson_palette.py
python tools/import_remaining_battles.py --jobs thief hunter apothecary bard knight sage swordsman shaman
python tools/build_remaining_battle_review.py --jobs thief hunter apothecary bard knight sage swordsman shaman
python tools/validate_assets.py --strict
godot --headless --editor --import --quit
godot --path . --script res://tools/capture_remaining_battles.gd -- --capture
python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .
python tools/check_frozen_files.py
```

今回の見た目の採否は、依頼者の画像確認による。遺跡背景の手前の倒れた柱は改変せず、roadmapの「見た目・音」の未決事項へ記録済み。次のスプリントには進まない。
