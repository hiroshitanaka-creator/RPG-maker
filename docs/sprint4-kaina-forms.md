# スプリント4 第1回：カイナの魔物化8系統

追記：依頼者は8系統の形と動作を採用した。現在の戦闘素材は、以下の初回16色版から17〜20色へ色だけを修正している。最新の修正内容は `sprint4-kaina-colors.md`。歩行素材は初回のまま。

2026年9月29日。PR #2を含むmain `53c1d8979296a7a54e3264aa870d825dd1cc4c8d` を取り込んで開始した。開始時の未コミット変更・未pushコミットはともに0件。

## 今回の範囲

- カイナのスライム・獣・不死・鳥・植物・甲殻・精霊・竜の8系統。戦闘8シート・24コマ、歩行8シート・96コマ。
- 戦闘は96×96の横3コマ、左向きの待機・攻撃・被弾。既存の描画で72px表示する。
- 歩行は32×48、下・左・右・上の4方向×3コマ。既存の0→1→0→2の表示を使う。
- 原画はIMG_1100の左3体、IMG_1105の4体、IMG_1109の左1体だけ。旧IMG_1032〜1035・IMG_1093〜1097は使用していない。
- 既存の素材パスへ差し替えたため、ゲーム本体の処理、魔物化の解放条件、戦闘配置は変更していない。

家と水際の暫定採用、後日の「見た目の仕上げ」、スプリント4→スプリント5の残り→6の順番、新原画9枚の対応を `roadmap-v2.md` に反映した。家や水際の画像は今回変更していない。

## 確認画像

- [原画と切り抜き（同じ倍率）](verification/sprint4-kaina/source-cutouts.png)
- [原画・戦闘3動作・72px表示の比較](verification/sprint4-kaina/source-battle-comparison.png)
- [歩行8系統・4方向3コマ](verification/sprint4-kaina/walk-eight.png)
- [平原の8系統](verification/sprint4-kaina/battle-plains-eight.png)
- [洞窟の8系統](verification/sprint4-kaina/battle-cave-eight.png)
- [死者の国の8系統](verification/sprint4-kaina/battle-underworld-eight.png)

戦闘一覧は本番の `FirstRegionScreen` と `RpgBattleView` で撮影した24枚を並べたもの。撮影用にカイナだけを各系統のマスター済み状態として読み込み、共通の職業適用処理を使用した。物語上の魔物化解放や、修練回数を実際に稼いだ証拠とは区別する。個別の1024×576画像は `verification/sprint4-kaina/runtime/` に保存した。

## 制作と変換の記録

1. 原本はそのまま保管し、9枚のSHA-256を原本フォルダのREADMEと `asset-checks.json` に記録した。
2. カイナだけを手動の矩形で指定し、外周につながる明るい灰色を除いた。最大の連結した体を残し、隣の系統のはみ出しを除いた。体内の青白い光沢は残す。生成入力の切り抜きはそのまま保存した。
3. 比較用の切り抜きでは、植物・甲殻・精霊・竜の枝・脚・翼に囲まれた灰色背景も除去した。比較画像は原画と同じ倍率で並べる。ハルドの白い体にはこの処理をまだ適用していない。
4. 内蔵imagegenで8枚の動作原画を生成した。各1枚に戦闘3コマと歩行12コマを収めた。全文の指示と入力・出力のハッシュは `assets/source_records/kaina-form-generation.json`。
5. Python/Pillowで分割し、動作ごとの枠に収まる共通倍率で最近傍縮小した。甲殻系の攻撃は大きく伸ばしすぎず、胴体の見かけの大きさを保つ。変換倍率・切出し位置・不透明部分の大きさ・接地行は `kaina-form-conversion.json`。
6. 戦闘・歩行とも同じ16色を既存のnatural.gplから選んだ。規約の上限は戦闘20色・歩行16色を維持。紺色の布、目の黄土色、骨の明るい色、精霊の青い光を残した。細い枝や布のしわは縮小・減色で簡略化される。
7. 精霊系以外の戦闘素材は外側に青灰色 `#728593` の1画素の縁取りを加えた。精霊系は原画由来の明るい輪郭を使用。すべて二値透過（完全透明か完全不透明）とした。
8. 96→72pxの最近傍縮小では新しい中間色や半透明が生じないことを確認した。4分の3への縮小なので、細い線が一部間引かれる点は残る。比較画像で実表示を確認できる。

既存の12職、残る3人、侵蝕の兆候、背景・地形・音・字体・パレットは無変更。対象外の登録ファイル665件と原本9枚を開始時のmainとバイト単位で照合した。

## 実行した検査

| コマンド | 結果 |
| --- | --- |
| `python tools/prepare_kaina_forms.py` | 原本を変更せず8系統を切出し |
| `python tools/import_kaina_forms.py` | 16シート、戦闘24・歩行96コマを変換 |
| `godot --headless --editor --import --quit` | 成功。エラー・警告なし |
| `godot --path . --rendering-method gl_compatibility --script res://tools/capture_kaina_forms.gd -- --capture` | 400項目成功、24枚撮影。素材参照・96px/72px・歩行形式・保存復元を確認 |
| `python tools/review_kaina_forms.py` | 寸法・色数・透過・原画/変換ハッシュ・対象外不変・縮小を確認 |
| `python tools/validate_assets.py --strict` | 素材665件、音14件、字体2件、問題なし |
| `python tools/check_frozen_files.py` | 保護対象26件、一致26件 |
| `python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .` | R-01〜R-08すべて成功 |
| `git diff --check` | 問題なし |

R-01〜R-08、既存検査、保護ファイル、合否条件は変更していない。今回追加した撮影・素材検査の結果は `runtime/checks.json` と `asset-checks.json` に保存した。

再現にはPython、Pillow、NumPy、SciPyを使用する。画像生成は保存済みの原画を再使用でき、取り込みと検査の再実行に画像生成APIは不要。`prepare_kaina_forms.py` → `import_kaina_forms.py` → Godotインポート・撮影 → `review_kaina_forms.py` の順で画像と記録を再作成できる。

## 今回の停止位置

カイナ8系統の画像の採否を依頼者が判断する。採用後にリオネ・ハルド・スイナを作る。ハルドの白い体の切り抜きは未実施・未検証。侵蝕の兆候の新しい絵は未着手で、32姿を作り終えた段階で2〜3案を提示する。スプリント5の残りも未着手。
