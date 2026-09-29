# スイナの青紫と、カイナ戦士の侵蝕の模様見本

開始時のmainは `35222876e1a5aa40dcdd51b19a2f927996c63290`。未コミット変更・未pushコミットは0件。

## スイナの戦闘素材

依頼者指示に従い、新原画の実在画素から青紫4色を採取し、natural.gpl末尾に追加した。既存68色の順序・値・ファイルの既存部分は不変。追加後は72色。色は `#2C1251`、`#4D267F`、`#7342B7`、`#A778DE`。原画の座標とSHA-256は `assets/source_records/natural-violet-extension.json` に記録した。

スイナの魔物化戦闘8枚だけを再配色し、形・3動作・透過・位置・96px素材・72px表示を保った。1素材20色以内。歩行や他の既存素材は再配色していない。

[原画と再配色後の比較](verification/sprint4-party/pc_04-source-battle.png)

剣士の深紅追加と同じ手順で、`tools/validate_assets.py` のnatural.gpl全体の上限だけを68から72へ変更した。判定の数値とエラー表示の数値の2箇所のみで、他のパレットの64色上限、各素材の20色・16色、透過・寸法・接地・出所などの条件は変更していない。

## 侵蝕の段階を確認した結果

`docs/rpg-plan-v1.md` の第5章と `GameSession.erosion_stage()` に、次の段階が既に定義されている。

| 値 | 段階 | 既存の扱い |
| --- | --- | --- |
| 0〜29 | 平常 | 兆候なし |
| 30〜59 | 兆候 | 外見・戦闘台詞が変化 |
| 60〜89 | 変異 | 人間職JP半減・特定職の解放条件 |
| 90〜100 | 不可逆 | 人間職へ戻れない |

90以上で戦士のままの入力は `game_session.gd` の保存状態検査で拒否される。今回もこの拒否を追加検査で確認した。90を魔物姿の例として並べるか、今回の戦士見本を0・30・60だけにするか、依頼者へ確認中。90の見本は未作成であり、不可逆条件や保護された受入は変更していない。

## 今回作った見本

案2の腕・頬の模様を独立した透明画像として作り、衣装と合成して本番描画へ渡す方式にした。衣装の元PNGは上書きしない。30の模様を60でもすべて残し、腕に線と枝を増やす。紺の線に明るい縁を付け、二値透過のまま光って見えるようにした。新しい画像生成は使っていない。

`CharacterVisuals` は人物・職業・段階ごとの合成画像を参照できる。全12職が同じ戦闘・歩行シート寸法であることを確認した。今回はカイナの戦士の30・60だけを位置調整した。残る11職や他の3人の模様はまだ作っていない。

作成したのは重ね絵4枚と合成画像4枚。重ね絵は人物の足を含まないため、素材種別を `erosion_pattern_overlay` とし、セル寸法・配置を記録した。合成した人物シートには通常のフレーム・接地検査を適用する。模様の外側の画素、衣装の輪郭と足元は不変。

- [戦闘画面の0・30・60比較](verification/erosion-pattern-preview/battle-stages.png)
- [歩行画面の0・30・60比較](verification/erosion-pattern-preview/walk-stages.png)
- [素材を拡大した比較](verification/erosion-pattern-preview/warrior-stages-detail.png)

戦闘と村は本番画面で撮影した。侵蝕値は見本用の明示入力。村では通常の移動処理を通し、歩行コマを撮影した。侵蝕を実際に稼いだ到達記録ではない。

## 変更ファイルと検査

- 青紫：`assets/palette/natural.gpl`、スイナ戦闘8PNG、変換記録、`tools/extend_natural_violet.py`、`tools/import_party_forms.py`、素材規約と上限数値。
- 模様：カイナ戦士の重ね絵・合成画像8PNG、台帳、制作記録、`data/character_visuals.json`、`scripts/game/character_visuals.gd`。
- 確認：`tools/build_erosion_pattern_preview.py`、`tools/capture_erosion_pattern_preview.gd`、`tools/build_erosion_preview_review.py`、`tools/check_violet_erosion_preview.py`、確認画像・記録。

実行順：`extend_natural_violet.py` → `import_party_forms.py --actors pc_04 --kinds battle` → `review_party_forms.py --actors pc_04` → `build_erosion_pattern_preview.py` → Godotインポート → `capture_erosion_pattern_preview.gd` → `build_erosion_preview_review.py`。

追加検査では既存68色の不変、4色の原画との一致、スイナ24コマの輪郭不変、差し替え対象外の既存登録素材673件の不変、模様以外の画素不変、30から60への模様増加を確認する。既存の `validate_assets.py --strict`、`check_frozen_files.py`、R-01〜R-08も実行する。

今回の実行結果：追加素材検査成功、本番撮影121項目成功、素材673件・音14件・字体2件は問題なし、凍結ファイル26件一致、R-01〜R-08すべて成功。通常CIはpush後に全ジョブの終了を確認して報告する。

試作中に撮影用変数の型宣言、30の模様が60で一部落ちる重ね方、素材台帳の制作記録参照を修正した。検査の条件を緩めて解決したものではない。

## 未実施

90以上の見本は、戦士を維持できない既存仕様との関係を依頼者へ確認中。残る11職・3人の模様位置調整、侵蝕の全素材の採用、スプリント5の残りには進んでいない。
