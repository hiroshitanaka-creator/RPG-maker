# スプリント5：森の塔とスイナの加入

スプリント4は9d9fc2eで本番登録を終え、R-01〜R-08と[CI全3ジョブ](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/36521334508)が成功した。素材検査23秒、Godot・凍結受入テスト2分35秒、試遊前検査4分5秒。依頼者の指示に従い、次の区切りとして森の塔へ戻った。

## 今回の範囲

- 城の謁見で許可を得た後、城の北西の入口から森の塔へ歩いて入る。
- 苔の石床、円形の石壁、崩れた柱を持つ3階。上下の階段4接続、宝箱3個。
- 2階に東階段の崩れ跡を置き、採用済み加入会話の内容に対応させた。
- 最上階に既存の守門の翼獣を配置。敵の能力・技・報酬・カタログは変更していない。
- 撃破後、スイナの会話を最後まで進めると4人になる。会話全文は `docs/first-region-recruit-scenes.md` の採用済み10行と一致する。
- 加入後は山道の入口を通れる。今回は山道の短い区間までで、港町への接続・転移呪文・船は次の区切り。
- 塔用の戦闘背景、ダンジョン曲、ボス曲は登録済みの素材を使う。

## 確認画像

目標は保管済みIMG_1009.PNG。`docs/reference/visual-targets/forest-tower.png` にバイトを変えず複製した。

- [目標と配置の比較](verification/sprint5-forest-tower/target-comparison.png)
- [世界マップの入口](verification/sprint5-forest-tower/runtime/01-world-tower.png)
- [1階](verification/sprint5-forest-tower/runtime/02-floor-1.png)、[2階](verification/sprint5-forest-tower/runtime/03-floor-2.png)、[3階](verification/sprint5-forest-tower/runtime/04-floor-3.png)
- [最上階の戦闘](verification/sprint5-forest-tower/runtime/05-tower-boss.png)
- [スイナとの会話](verification/sprint5-forest-tower/runtime/06-suina-conversation.png)、[同行の申し出](verification/sprint5-forest-tower/runtime/07-suina-offer.png)
- [加入後の探索](verification/sprint5-forest-tower/runtime/08-four-party-exploration.png)、[4人での通常戦闘](verification/sprint5-forest-tower/runtime/09-four-party-battle.png)
- [開いた山道](verification/sprint5-forest-tower/runtime/10-mountain-path.png)

塔の確認画像は本番描画。比較画像の全体図だけは本番の配置データから描き、実ゲーム画像と区別する。目標のらせん階段に対し、今回のゲームには登録済みの直線の石段を使っている。

## 検査方法

`tools/check_forest_tower.py` は3階・全階段の往復到達性、宝箱と人物への接近、採用済み会話全文、原画のハッシュ、既存拠点・敵・共通パレットの保持を確認する。

`tools/capture_forest_tower.gd` は、新規開始から保護されたR-07の通常入力経路を通り、その続きで謁見・塔の攻略・加入・山道へ進む。位置・所持品・進行フラグは注入しない。保護されたスクリプトを変更せず継承し、180秒・3,000入力・600歩・300ターンの上限を維持する。撮影時のみ垂直同期による待ちを外すが、歩行速度・150msの移動処理・時計は変更しない。

加入前、加入後、山道で保存し、別のGameSessionへ読み込んで完全一致を確認する。ボス前は加入できないこと、同行の申し出の行では3人のままであること、加入と宝箱が二重実行されないことも確認する。実行結果は `docs/verification/sprint5-forest-tower/` に保存する。

最終の通常操作は83項目・10画像、704入力・380歩で成功した。併せてR-07の14項目もすべて成功し、村退出時の人数は3人。旧保存からの加入などの境界検査は `tools/check_forest_tower_session.gd` で20項目成功した。この境界検査だけは人工的な保存状態を使い、通常到達の証拠とは区別する。

`python tools/validate_assets.py --strict` は1,050画像・14音・3パレット・2字体すべて成功。`python tools/check_frozen_files.py` は26件一致。`verify_cli.py --quiet .` はR-01〜R-08すべて成功し、記録を `r01-r08.txt` に保存した。既存の検査ファイル・契約・合否条件・時間上限は変更していない。CIの終了結果はpush後に確認して報告する。

最初の撮影では、塔の入口候補への経路、階段の着地点の瓦礫、歩行途中の宝箱操作、旧実装にスイナの待機データがない問題を検出し、修正した。会話の最後で加入に失敗していたことが、決定入力の繰り返しと上限到達の原因だった。新規開始では待機を含む4人分を用意し、旧保存では塔でスイナに会った際に初期データを補う。元の仲間の育成・所持品・位置を補完や書換えで変えない。

## 主な変更ファイル

- `world/first_region.json`、`world/interiors.json`、`world/first_region_visuals.json`：塔の配置・階段・会話・山道。
- `scripts/world/first_region.gd`、`scripts/game/game_session.gd`：通常移動・戦闘開始・加入・保存の条件。
- `scripts/world/first_region_view.gd`、`scripts/ui/first_region_atlas.gd`、`scripts/ui/game_root.gd`：入口とボスの表示、世界地図の現在地、背景と曲。
- `assets/tiles/forest_tower_round_room.png`、`assets/registry.json`、`assets/source_records/forest-tower.json`：既存画素から作った円形の部屋と出所。
- `tools/build_forest_tower.py`、`tools/check_forest_tower.py`、`tools/capture_forest_tower.gd`：再現・配置検査・本番撮影。
- 計画、加入会話の実装状況、参考画像のREADME、この報告と確認画像。

## 今回に含めない残作業

港町、転移呪文、船は次の区切り。塔の画像を依頼者が確認するまで、この先へ進まない。約60時間の実測や全体の難易度の確定は今回の検査で達成したとは扱わない。
