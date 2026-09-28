# スプリント4：リオネ・ハルド・スイナの魔物化24姿

カイナの色修正採用後の依頼に対応した。開始時のmainは `7b368702b5a62ebd0b26b83ff170c153f762fe77`。未コミット変更・未pushコミットは0件。最新リモートとの差分もなかった。

## 制作内容

- 3人×8系統の24姿。戦闘24シート・72コマ、歩行24シート・288コマ。
- 戦闘は96×96の待機・攻撃・被弾、左向き、72px表示、20色以内。
- 歩行は32×48、下・左・右・上の4方向×3コマ、16色以内。
- 二値透過、最近傍縮小、全コマの足元をそろえる手順を維持。原画と生成原画を別に保管し、制作指示・切り抜き範囲・変換倍率・ハッシュを記録した。
- 目印はリオネの緑の髪留めと赤い房、ハルドの白い包帯、スイナの紫の花。目と花の発光部には明るい画素を残し、72pxへの縮小後も保存された光点を照合する。

原画対応は計画の最新表のとおり。IMG_1101・1102・1104は左3体だけ、IMG_1106・1107・1108は4体、IMG_1109は左から2〜4体目を使う。旧IMG_1032〜1035・IMG_1093〜1097や、各前半原画の4体目は使わない。

## 切り抜きと色の注意点

ハルドの原画は白い体と背景色が近い。カイナ用の明度判定を流用せず、画像外周から背景色の変化を推定し、それに近く外周へ接続する部分だけを除いた。体内の白い部分を残し、原画と同倍率の比較で頭・手・羽・足・包帯の輪郭を確認した。新原画9枚はバイト単位で不変。

スイナの前半原画は淡い外光が獣系と不死系をつないでいた。外光を背景と分け直し、体から離れた薄い外光の断片を除いて、2体が混ざらないようにした。生成は分離後の姿を基準に行った。

内蔵imagegenで1姿につき15コマの動作原画を作成し、Python/Pillowで変換した。ハルドの鳥系は左右歩行の3コマ目が逆の行に生成されていたため、左右反転をせずに正しい行へ並べ直した。並べ替え順は変換記録に残した。生成済み24シートの外端には不透明な画素がなく、画像端による羽・爪・尾の切れがないことも確認する。

配色は人物ごとに既存のnatural.gplから選択した。ハルドにはカイナ向けの明るさ補正を一律にかけず、白と灰色の陰影を残した。スイナの有彩色の紫は、RGBの距離だけで淡い桃色へ寄らないよう、紫の段階から原画に近い明度を選んだ。共通パレットのため、原画の鮮やかな青紫に対して仕上がりは赤紫寄りになる。この色差は比較画像で確認できる。パレット自体は変更していない。

## 確認画像

| 人物 | 原画と切り抜き | 原画・戦闘3動作・72px表示 | 歩行 |
| --- | --- | --- | --- |
| リオネ | [切り抜き](verification/sprint4-party/pc_02-source-cutouts.png) | [戦闘比較](verification/sprint4-party/pc_02-source-battle.png) | [4方向](verification/sprint4-party/pc_02-walk.png) |
| ハルド | [切り抜き](verification/sprint4-party/pc_03-source-cutouts.png) | [戦闘比較](verification/sprint4-party/pc_03-source-battle.png) | [4方向](verification/sprint4-party/pc_03-walk.png) |
| スイナ | [切り抜き](verification/sprint4-party/pc_04-source-cutouts.png) | [戦闘比較](verification/sprint4-party/pc_04-source-battle.png) | [4方向](verification/sprint4-party/pc_04-walk.png) |

- [4人×8系統の一覧](verification/sprint4-party/all-32-forms.png)
- [洞窟での8系統の4人](verification/sprint4-party/battle-cave.png)
- [死者の国での8系統の4人](verification/sprint4-party/battle-underworld.png)

戦闘は本番の `FirstRegionScreen` と `RpgBattleView` を使用。4人を同じ系統のマスター済み素材確認入力として読み込み、共通の職業適用処理を通して撮影した。本編の解放・修練回数・到達を実測したものとは区別する。個別の1024×576画像は `verification/sprint4-party/runtime/` に保存した。

## 変更ファイルと実行コマンド

- 素材：`assets/characters/pc_02/`〜`pc_04/` の魔物化歩行・戦闘48PNG、`assets/registry.json`。
- 原画と記録：`assets/_incoming/party-forms-2026-09-29/`、`assets/source_records/party-form-cutouts.json`、`party-form-conversion.json`、`party-form-generation/`。
- 再現用：`tools/prepare_party_forms.py`、`import_party_forms.py`、`review_party_forms.py`。
- 今回の追加検査：`tools/check_party_forms.py`、`capture_party_forms.gd`。
- 報告・計画・侵蝕の案：本書、`docs/roadmap-v2.md`、`docs/proposals/erosion-signs-visual-options.md`。

| コマンド | 結果 |
| --- | --- |
| `python tools/prepare_party_forms.py` | 3人24姿の切り抜き・比較を作成 |
| `python tools/import_party_forms.py` | 戦闘72・歩行288コマの48シートを作成 |
| `python tools/check_party_forms.py` | 48シートの寸法・色数・透過・出所・光点・対象外不変を確認 |
| `godot --headless --editor --import --quit` | 成功、エラー・警告なし |
| `godot --path . --rendering-method gl_compatibility --script res://tools/capture_party_forms.gd -- --capture` | 4人32姿・1,352項目成功、暗所16枚を撮影 |
| `python tools/review_party_forms.py --runtime` | 人物別比較・32姿一覧・暗所一覧を作成 |
| `python tools/validate_assets.py --strict` | 素材665件・音14件・字体2件、問題なし |
| `python tools/check_frozen_files.py` | 保護対象26件、一致26件 |
| `python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .` | R-01〜R-08すべて成功 |

今回の素材検査では、差し替え対象外の登録ファイル633件と新原画9枚が開始時のmainと一致した。カイナの採用済み8系統、人間12職、侵蝕素材、背景・地形・音・字体・共通パレットは不変。既存検査・保護ファイル・合否条件も変更していない。

取り込みの再現にはPython、Pillow、NumPy、SciPyを使う。生成原画は保存済みであり、変換・検査の再実行に画像生成APIは不要。

取り込みは制作済みの範囲ごとに `--actors pc_02`、`--actors pc_02 pc_03`、`--actors pc_04` と、必要な `--forms` を指定して実行した。通常CIはpush後に全ジョブの終了を確認して報告する。

## 停止位置

今回は3人の魔物化画像を報告し、侵蝕の兆候の3案を提示して止まる。侵蝕の原画・新素材はまだ作っていない。既存の侵蝕条件・数値・解除・表示処理は変更していない。スプリント5の残りにも進まない。
