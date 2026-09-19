# 提供モンスター画像の取り込み

2026年9月19日。依頼者の「モンスター画像を作成しました。使えたら使って下さい。」に基づき、2枚の提供画像から17点を切り出した。14点を本編の敵へ割り当て、3点は使用先を増やさず任意素材として登録した。画像生成は行っていない。

## 原本と処理

| 原本ファイル | 作業用の名前 | 寸法 |
|---|---|---|
| Gemini_Generated_Image_q0mnxfq0mnxfq0mn.jpg | sheet_a.jpg | 2048×2048 |
| Gemini_Generated_Image_d5tm1pd5tm1pd5tm.jpg | sheet_b.jpg | 2048×2048 |

原本は`assets/_incoming/user_monsters_20260919/`へバイト一致でコピーした。この一時置き場は既存の`.gitignore`に従いGit対象外。規約適合後のPNG、処理コード、原本と出力のSHA-256をリポジトリへ保存する。ラベルの「魔獣系」「ボス」などは画像の識別に使い、新しい職業・章・設定の追加指示とは扱わない。

`tools/import_user_monsters.py`は原本ハッシュを照合し、記録した矩形で切り出す。外周から白背景を除き、コウモリの翼内の白抜き、翼獣の灰色の背景光、見出しの断片を除去する。最近傍縮小・足元合わせ・既存64色パレットへの16色以内の量子化・アルファ0/255への二値化を行う。左右反転や描き直しは行わない。

```powershell
. .\tools\prepare_scope_env.ps1
# 上表の原本2枚を作業用の名前で _incoming の所定位置へ置いて実行する。
python tools/import_user_monsters.py --apply
python tools/validate_assets.py --strict
```

`--apply`なしでは`.tools/user-monsters/`へのプレビュー出力だけを行う。処理座標、閾値、原本・出力ハッシュは[取り込み記録](verification/user-monster-import.json)、確認用一覧は[17点のプレビュー](verification/screens/user_monsters.png)を参照する。

## 使用先

全PNGは`assets/monsters/<素材ID>/idle.png`。寸法は正方形。名前と敵への割り当ては実装上の提案であり、世界観の確定ではない。

| 素材ID | px | 本編の使用先 |
|---|---:|---|
| wet_beast | 64 | 川辺の荒獣 |
| winged_beast | 64 | 守門の翼獣 |
| flame_slime | 32 | 熔体スライム |
| stone_slime | 32 | 岩殻スライム |
| bone_wolf | 64 | 灰還りの骸獣・蘇生役 |
| bone_bat | 32 | 骨翼コウモリ |
| lava_turtle | 64 | 熔殻の番兵 |
| shadow_wolf | 64 | 影毛の荒獣 |
| chimera_boss | 64 | 溶岩の大荒獣 |
| magma_wolf | 64 | 炉心の魔狼 |
| wind_wolf | 64 | 疾風の荒獣 |
| crystal_slime | 32 | 冷晶スライム |
| ghost_bat | 32 | 幽翼コウモリ |
| glacier_turtle | 64 | 氷殻の番兵 |
| zombie_wolf | 64 | 任意素材。未配置 |
| storm_wolf | 64 | 任意素材。未配置 |
| underworld_boss | 96 | 任意素材。未配置 |

元の20画像と共通パレットを保持し、台帳は37画像になった。追加分のうち実際に使う14点は`required`、未配置3点は`optional`。旧5点と合わせ、本編の敵30種は19通りの画像を使う。30種すべてに別の絵があるという意味ではない。

## 採用を保留した3点

- sheet_aの「ボス2」とsheet_bの「ボス4」は正面向き。右向き固定の規約に合わないため、PNG登録・敵への割り当てを行わない。
- sheet_bの「毒液スライム」は、現在の64色へ変換すると紫の特徴が失われる。共通パレットを変更せず、原本のまま保留した。

2枚で重複している敵は1点として扱った。未配置の3点のために敵数や章数を増やしていない。外部サービスでの生成条件・配布権の確認は本作業では実施していない。
