# スプリント3：職業の衣装（第1回）

> 2026年9月28日：12職の戦闘素材を依頼者が採用。続いて残り8職の歩行素材を制作した。現在の成果物・検証範囲は [残り8職の歩行素材](sprint3-walks-remaining.md) を参照。以下は各区切り当時の記録。

> 2026年9月28日：残り8職の戦闘素材を追加した。最新の形式・固定色・比較画像・検査は [残り8職の戦闘素材](sprint3-battles-remaining.md) を参照。ここにある未作成・採用待ちの記述は第1回当時の記録であり、今回も残り8職の歩行素材は対象外。

> 2026年9月27日の追加指示で、完成済み4職の戦闘絵は96px素材・72px表示へ作り直す。現在の取り込み手順は [戦闘画面の目標への対応](battle-layout-target.md) と `tools/import_large_battles.py`。以下の48px戦闘絵と旧取り込みコマンドは第1回の履歴として残す。歩行絵は第1回の成果物を維持する。

全体の目標は12職×4人の歩行・戦闘。計画の分割ルールに従い、今回は戦士・武闘家・僧侶・魔法使いの4職×4人を作成した。残る8職は未作成であり、スプリント3全体の完了とは扱わない。

## 取り込みと実装

- 指定原画IMG_1018〜1021は衣装の基準、採用済み `party-design-sheet.png` は顔・髪・体格の基準に使った。原画は変更していない。
- 組み込みimagegenで歩行と戦闘の動作を生成。13枚の原画を `assets/_incoming/sprint3-2026-09-27/` に保存した。戦士の最初の戦闘原画は横幅が大きいため不採用とし、剣をコンパクトにした版を使用した。
- `tools/import_job_costumes.py` で透明領域から分割し、歩行32×48・3×4、戦闘48×48・3×1へ最近傍で変換。各衣装の歩行・戦闘に共通の自然色16色を使い、アルファ0/255、接地行47にそろえた。武闘家の橙は肌と混同しない黄土色へ対応させた。
- 32シート・240コマ。再生成でシート・台帳・変換記録34ファイルがバイト一致。各シートの全コマは空でなく、重複コマ0。左右48組は単純反転の一致0。
- 生成指示と原画のSHA-256は `assets/source_records/sprint3-generation.json`、切り出し・倍率・色の規則・成果物のSHA-256は `assets/source_records/sprint3-costumes.json`。
- `data/character_visuals.json` に人物別の職業衣装を登録し、`CharacterVisuals.appearance` が現在の職業から選ぶ。未作成の職は従来の基本衣装。侵蝕の兆候・魔物化は既存の優先表示を維持し、描き直しはスプリント4。

## 検証と画像の意味

共通の `GameSession.new_game(4)` と `choose_job` で4人×4職へ変更し、歩行・戦闘32参照と保存・別インスタンスへのロード4ケースを確認した。人物の職業フィールドや進行フラグを直接書き換える検査ではない。

最初の村は仕様どおり転職未解放のまま。転職解放イベントはスプリント5で作る。`*-walk-render.png` と `*-battle-*.png` は共通転職処理の結果を描いた確認用の見本であり、物語の解放・スイナの加入の証明ではない。戦闘は本番の `RpgBattleView` を使用する。

最初の地方の実ゲームでも新衣装を表示し、既存の通し撮影でA01〜A14を確認した。`docs/verification/first-region/` の画像は通常操作による実ゲーム。`docs/verification/sprint3/` は衣装一覧・原画比較・歩行GIF・表示見本。

```powershell
python tools/import_job_costumes.py --jobs warrior martial_artist priest mage
python tools/validate_assets.py --strict
godot --path . --rendering-method gl_compatibility --script res://tools/capture_job_costumes.gd -- --capture
godot --path . --rendering-method gl_compatibility --script res://tools/capture_first_region_recruits.gd
```

## 次の区切り

未作成：盗賊・狩人・薬師・吟遊詩人（IMG_1022〜1025）、騎士・賢者・剣士・祈祷師（IMG_1026〜1029）。いずれも4人分の歩行・戦闘を作る。今回の衣装の色・人物の見分けやすさ・動きは確認画像で依頼者が判断する。
