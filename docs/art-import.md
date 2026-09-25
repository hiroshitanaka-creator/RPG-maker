# 素材取り込み記録

> 履歴資料: 以下の進捗・未達・暫定値は記録時点の状態です。現在の実装・受入・残作業は [現在地](current-status.md) を参照してください。

以下は実施済み作業の履歴。以後の画像生成には[最新の許可範囲](asset-generation-authorization.md)を適用する。許可は地形2枚・敵5体とpc_01の左歩行Bの1コマに限られ、この履歴にある追加人物コマの生成許可へ拡大しない。

2026年9月19日。依頼者の「画像で足りないコマはcodexで生成して下さい。」を受け、Codex内蔵の画像生成を使用した。API/CLI経由の生成は使用していない。原本は変更せず、生成後の切り出し・縮小・減色・二値透過・接地合わせをPython/Pillowで実施した。

| 保存先 | 内容・方法 | 規定 |
|---|---|---|
| `assets/characters/pc_01/walk.png` | 提供画像の11コマを保持し、右向きだった左歩行Bだけ生成して補完。 | 96×192、4方向×3コマ |
| `assets/characters/pc_02/walk.png` | 提供画像12コマを切り出し、大きさを正規化。 | 同上 |
| `assets/characters/pc_03/walk.png` | 左歩行A/Bと後ろ歩行Bを生成。残る9コマは提供画像。 | 同上 |
| `assets/characters/pc_04/walk.png` | 左歩行Bと後ろ歩行Bを生成。残る10コマは提供画像。 | 同上 |
| `assets/characters/pc_01`〜`pc_04/battle.png` | 各人の待機・攻撃・被弾を生成。白髪の人物の右向き被弾候補は採用せず、左向きを再生成。 | 各144×48、3コマ、左向き |
| `assets/characters/pc_01/battle_monster.png` | 提供された不死系の青髪の人物を参照。台帳の`form_reference`は`undead`。 | 144×48、3コマ、右向き |
| `assets/characters/pc_01`〜`pc_04/portrait.png` | 提供された4分割画像から切り出し。今回の補完でファイル内容は変更しない。 | 各64×64 |
| `assets/monsters/{slime,bat,shell_guard,ember_wisp,gate_beast}/idle.png` | 第1章の敵5種を生成。荒獣の端が切れた候補は採用せず再生成。 | 小型32×32、大型64×64、右向き |
| `assets/tiles/{field_outdoor,dungeon_cave}.png` | 屋外・洞窟の16種類ずつのタイルを生成して切り出し。 | 各512×512、タイル32×32 |

全20画像はRGBA、アルファ0/255。共通64色パレットは顔画像で使用中の52色を維持し、新素材から12色を選定。人物・敵は各16色以内。左右反転は使用していない。タイルの先頭行は地面・壁・水・道・目印など16種類。残る行にも同じ地形を配置しており、256種類の地形を制作したという意味ではない。

## 再実行と原本

入力は`assets/_incoming/20260919/`、生成原画は`assets/_incoming/generated_20260919/`に保管した。これらは従来の規約によりGit管理対象外。本番PNG・パレット・処理スクリプト・プロンプト・SHA-256はリポジトリに保存する。別環境で再加工するには入力原本も必要。ゲームの起動には登録済みPNGだけで足りる。

```powershell
python tools/import_character_art.py --portraits-only --apply
python tools/import_chapter1_art.py --apply
python tools/import_party_art.py --apply
python tools/validate_assets.py --strict
```

再作成は上記の順序で行う。最初の処理は顔画像用パレットを再作成し、次の処理が既存52色を保持した最終パレットを構築する。座標・アルファ閾値・接地・共有縮尺はスクリプト内に明記した。

生成プロンプトと原画・出力ハッシュは[image-generation-prompts.json](image-generation-prompts.json)。元の提供画像のハッシュは2つの受領記録に保持している。

## 確認範囲と残り

- 素材検査: 台帳20件すべて存在し、エラー・台帳上の不足0件。
- 全歩行・戦闘シート・敵・タイルの縮小後一覧を目視し、歩行12コマの接地を機械検査した。
- Godot実描画で第1章の主人公歩行・地形・敵・会話の顔画像を確認。タイトル・探索・編成・会話・戦闘・クリアの[画面記録](verification/screens/)を保存した。
- ほかの人物の歩行、味方の攻撃・被弾アニメーション、魔物化シートは素材登録まで。通常ゲームでの表示切り替えへの接続は未実施。
- 魔物化画像はpc_01の不死系参考外見1種類。全員・全モンスター職の外見がそろったという意味ではない。提供画像の外部調達元・ライセンスは未確認のまま。
