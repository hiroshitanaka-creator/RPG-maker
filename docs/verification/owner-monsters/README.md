# 依頼者原画の敵・確認画像

- `catalog-sheet.png`：取り込んだ102体。ゲーム用PNGの実寸、id付き。
- `replacement-before-after.png`：既存22種の旧・新比較。旧画像を維持した3種も明記。
- `battle-mock-plains.png`、`battle-mock-cave.png`：通常敵3体と仲間4人を512×288の背景へ実寸配置した静止図。
- `boss-mock.png`：水門の荒獣に割り当てた大鬼と仲間4人。実画面の撮影ではない。
- `held-back.png`：登録していない人間・神・精霊の人型と、若い4人の原画。原画名・列位置を表示。
- `original-review-1.png`〜`original-review-3.png`：36枚すべてを確認する原本の縮小一覧。
- `checks.json`：今回の機械検査の実行結果。

対応と配置案は `docs/monster-catalog.md`、加工記録は `assets/source_records/owner-monsters.json`。画像の読みやすさは実寸で確認したが、依頼者の採用判断を代行するものではない。特に大鬼は、最大192×160でも原画の細かな毛皮・装飾をすべて残すことはできない。

再生成は `python tools/import_owner_monsters.py`、確認図は `python tools/build_owner_monster_review.py`、検査は `python tools/check_owner_monsters.py`。敵データ・ゲーム処理・仲間の絵は変更しない。

検査対象は `sprint-0-owner-monsters-2026-09-26-final` タグが指す、このスプリント最後のコミットに固定する。Gitの保存内容を `.tools/owner-snapshot-*` に展開して検査し、作業ツリーとは比較しない。作業中の検査も `--revision <git write-treeのID>` で不変のGit版を指定する。最終タグを後続スプリントで動かさない。
