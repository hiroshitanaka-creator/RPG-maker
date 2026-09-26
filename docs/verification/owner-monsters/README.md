# 依頼者原画の敵・確認画像

- `catalog-sheet.png`：取り込んだ102体。ゲーム用PNGの実寸、id付き。
- `replacement-before-after.png`：既存22種の旧・新比較。旧画像を維持した3種も明記。
- `battle-mock-plains.png`、`battle-mock-cave.png`：通常敵3体と仲間4人を512×288の背景へ実寸配置した静止図。
- `boss-mock.png`：水門の荒獣に割り当てた大鬼と仲間4人。実画面の撮影ではない。
- `held-back.png`：登録していない人間・神・精霊の人型と、若い4人の原画。原画名・列位置を表示。
- `original-review-1.png`〜`original-review-3.png`：36枚すべてを確認する原本の縮小一覧。
- `checks.json`：初回提出版の機械検査の実行結果。

対応と配置案は `docs/monster-catalog.md`、加工記録は `assets/source_records/owner-monsters.json`。画像の読みやすさは実寸で確認したが、依頼者の採用判断を代行するものではない。特に大鬼は、最大192×160でも原画の細かな毛皮・装飾をすべて残すことはできない。

再生成は `python tools/import_owner_monsters.py`、確認図は `python tools/build_owner_monster_review.py`、検査は `python tools/check_owner_monsters.py`。敵データ・ゲーム処理・仲間の絵は変更しない。

検査対象は `sprint-0-owner-monsters-2026-09-26-final` タグが指す、このスプリント最後のコミットに固定する。Gitの保存内容を `.tools/owner-snapshot-*` に展開して検査し、作業ツリーとは比較しない。作業中の検査も `--revision <git write-treeのID>` で不変のGit版を指定する。最終タグを後続スプリントで動かさない。

## 2026年9月27日の体格修正

上記の検査とタグは初回提出版の記録として維持する。現在の素材は `tools/resize_owner_monsters.py` で原画から再変換する。旧 `import_owner_monsters.py` だけを実行すると初回の均一な大きさへ戻るため、修正版の再生成には使わない。

小42体・中22体・大22体・ボス16体。区分は透明余白を除いた不透明領域の長辺で測り、小48〜64px、中64〜80px、大96px、ボス128〜192px。PNGキャンバスは64×64、96×96、192×160のいずれかで、元の縦横比を維持する。大鬼は156pxでボス区分に収まるため、その体格を維持した。

`size-before-after.png` は体格修正の実寸比較。戦闘見本3枚と敵一覧も再生成した。最新の変換記録は `assets/source_records/owner-monsters-size-review.json`、各体の区分と実寸は `docs/monster-catalog.md` に記録する。

修正版の検査は `python tools/check_size_rock_review.py`。`sprint-0-size-rock-review-2026-09-27` タグの内容を読み、過去のタグ・検査を変更しない。102体の再変換一致、体格範囲、スライムが狼より小さいこと、旧画像3体・原画・仲間・パレット・音の不変性、岩壁の歪みなしを確かめる。
