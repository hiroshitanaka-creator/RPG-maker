# 008 桜封の栞とGrok原画11枚の記録

## 作業前の確認と計画

1. 最初に初期checkoutの `docs/STATUS.md` と依頼書008を読み、その後リモート最新mainのSTATUSを確認した。最新mainは `86698d0c8992cfbb3720bdbc4fe3ce8fe9371d3c`。発注で提示された `9d2f61fffb513e31c6714fc617f56b8be1a1c3c3` との差は親担当のSTATUS更新1件だけ。最新STATUSは007/021/022/023のPR #18統合済み、008のみ作業中と記録しており、同じ文書を変更する別の作業中依頼はない。初期checkoutに未コミット変更0件・最新mainにないコミット0件。
2. 登録済みブランチ `codex/task-008-record-bookmark-and-batch3` の元先端 `b0bb059ac3a846ad96722d7214dda0fc11feac50` を保全し、独立checkoutで最新mainを通常mergeした。mergeコミットは `97a22b28ba195071e7355681df94e8c6aac994eb`、親は登録済み先端と最新mainの2件。merge後の最新mainとの差分0件。初期checkoutの切替失敗による変更は元へ戻し、初期checkoutは清潔な状態を保持した。強制push・rebase・履歴書換えはしていない。
3. `assets/_incoming/owner-2026-10-05-grok-batch3/` には指定の原画11枚がすべてある。不足0件、余分0件。各ファイルを実際に開いて確認し、作業前SHA-256と最新mainの実ファイルを照合した。11枚すべて全バイト一致。下の表にファイルごとの値を記録する。
4. 設計文書3節の変更前全文は次のとおり。既存の決定3行を「メダル」の置換以外は保持し、2026-10-04の名前・見た目の決定2行、指定の未決、変更記録を加える。付録Bには依頼書の表11行と注意3項目をそのまま転記する。指定4文書だけを変更し、栞の実装や未決の数・配置・交換・人物を決めない。

```markdown
## 3. メダル（集める物）

- **決定**（2026-10-03）：メダルのように集める仕組みを入れる。
- **決定**：町や建物の中のつぼ・樽などを調べて見つける「調べる場所」を作る。調べる場所は、今の「宝箱」とは**別の種類**として作る（保護された検査 R-07 が洞窟の宝箱の数を数えているため、宝箱と同じ種類にすると R-07 が壊れる）。
- **決定**：集めた数に応じて、珍しい物と交換してくれる人がいる。
- **未決**：集める物の名前と見た目（ほかのゲームの「ちいさなメダル」の名前と見た目は使わない）、全部でいくつ集められるか、どこに置くか、何枚で何と交換できるか、交換してくれる人の名前と場所。
```

## 変更内容

変更するファイルは次の4件だけ。

- `docs/design/items-and-equipment.md`：3節と指定の変更記録1行。
- `docs/roadmap-v2.md`：付録B本節内、既存の `owner-2026-10-04-grok-region3` の表・注意の直後、次の「2026年9月27日の決定」の前に「付録B追記：Grok の原画（owner-2026-10-05-grok-batch3）」を追加。
- `docs/tasks/008-record-bookmark-and-batch3.md`：状態行だけ。
- `docs/tasks/reports/008-record-bookmark-and-batch3.md`：本報告。

3節の変更後全文：

```markdown
## 3. 桜封の栞（集める物）

- **決定**（2026-10-03）：桜封の栞のように集める仕組みを入れる。
- **決定**：町や建物の中のつぼ・樽などを調べて見つける「調べる場所」を作る。調べる場所は、今の「宝箱」とは**別の種類**として作る（保護された検査 R-07 が洞窟の宝箱の数を数えているため、宝箱と同じ種類にすると R-07 が壊れる）。
- **決定**：集めた数に応じて、珍しい物と交換してくれる人がいる。
- **決定（2026-10-04）**：集める物は、メダルではなく栞にする。名前は「桜封の栞」。
- **決定（2026-10-04）**：見た目は、`assets/_incoming/owner-2026-10-05-grok-batch3/bookmark-design-candidates-4.png` の左から2番目の候補（薄い透明な板の中に桜の花びらが3枚、細い金色の枠、深い紅色の組みひもの房）。
- **未決**：全部でいくつ集められるか、どこに置くか、何枚で何と交換できるか、交換してくれる人の名前と場所。
```

冒頭の「このファイルの内容は、まだゲームに実装されていません。実装するときは、依頼者の指示を待ってください。」は全バイト保持。3節と変更記録の追記以外は不変であり、表題・導入・全回復薬の入手欄など008範囲外の古いメダル表記は変更していない。

## 原画・台帳の実物照合

原画11枚を1枚ずつ画像表示で確認した。主な中身・位置・候補の順序で対応表を書き換える食い違いは見つからなかった。洞窟の階段の上り／下りと階同士の実際の接続は文書指定として保持し、画像だけでゲーム内動作まで確認済みとはしない。

| 原画 | 目視した内容 |
| --- | --- |
| `region3-village-exterior.png` | 針葉樹と雪、中央の焚き火広場、左下の凍った池、木材の作業場、右下の丸太の門を確認。 |
| `region3-village-room-inn.png` | 左上の暖炉、左側のベッド2台、右側の受付台を確認。 |
| `region3-village-room-item-shop.png` | 中央の受付台、奥の棚、左右の樽とかごを確認。 |
| `region3-village-room-weapon-shop.png` | 奥の斧・弓などの棚、左の砥石台、右の薪と毛皮、中央の受付台を確認。 |
| `region3-village-room-shrine.png` | 石の祭壇、針葉樹の小枝と火の皿、敷物、左右のろうそくを確認。 |
| `region3-volcano-cave-1f.png` | 溶岩と岩の橋、左の行き止まり、右上の階段を確認。下の部屋の外への出口が不明瞭という指定の注意を確認。 |
| `region3-volcano-cave-2f.png` | 中央の溶岩の池、右上と左下の階段を確認。 |
| `region3-volcano-cave-boss-floor.png` | 溶岩の堀に囲まれた円い広間、奥の溶岩の滝、左下の階段を確認。 |
| `region3-volcano-cave-boss.png` | 黒い石の体、溶岩のたてがみ、四つ足の竜を確認。 |
| `region3-volcano-cave-battle.png` | 洞窟の戦闘背景と非常に暗い床を確認。暗色敵との見えやすさは未検証。 |
| `bookmark-design-candidates-4.png` | 左から和紙・透明・押し花・魔法の4候補を確認。左から2番目に花びら3枚、金色の細い枠、深紅の房を確認。 |

台帳 `assets/registry.json` は全1140素材のJSONを読み、原画11枚のファイル名・保管先に該当する登録を照合したが、batch3の登録は0件だった。`docs/asset-spec.md` の「外部素材の取り込み」に従い `_incoming` は素材検査の対象外の保管場所であり、今回の用途は付録Bへ記録する。登録済みゲーム素材として照合できたとは報告しない。台帳は最新mainの実ファイルと全バイト一致し、008の許可外なので変更していない。

作業前・作業後・取り込んだ最新mainのSHA-256は次の全11件で一致。ファイル名と場所も不変。

| ファイル名 | SHA-256（前後・最新main一致） |
| --- | --- |
| `region3-village-exterior.png` | `a024fd4bbaa0855133224505685284e89c3456a69d2295e16b58fc8f87dcebc2` |
| `region3-village-room-inn.png` | `12e496ec60206222f6a30a0611d92e70fd4360a2092769451dbfab2f9b5ef3c5` |
| `region3-village-room-item-shop.png` | `f09c53d8a2564333ed0610c6c078a9f3481bf2ca234c3c6be73e8378a465306d` |
| `region3-village-room-weapon-shop.png` | `5a03fb0ebf04526f5cfe5b4fa04fa6d76341c0b866449786b078a5fbc9eea250` |
| `region3-village-room-shrine.png` | `851ec005215abaa9c6f030972e0da22c051288c54f545472d10c2e834740e312` |
| `region3-volcano-cave-1f.png` | `1af5b2b63fa1155f18af66c9caa53a5d5f7f2fb2aa8251e1a811525af2e055ec` |
| `region3-volcano-cave-2f.png` | `8ee38537fc9693bce3d88ec89e3c260c580d74f429ea7a20f4fb25c9cf53a2f6` |
| `region3-volcano-cave-boss-floor.png` | `dcb4819dfb897567d4786a0c9000888ec3d520c98639ae8ede72b55686355e09` |
| `region3-volcano-cave-boss.png` | `3f04032b80fc5dba64da30df644310248bd8b6246b09564dffecbf644db4f30c` |
| `region3-volcano-cave-battle.png` | `70e931340241589d3af1f77975932f2e85fef895c5a5792deeec980b61db03ac` |
| `bookmark-design-candidates-4.png` | `6e1c8dad4e7a2b495b8a478c6db053d2feafdce5c73508c2b20aed71f94f9a36` |

## 実行した検査と結果

- `godot --headless --editor --import --quit`：初期環境の4.6.3で終了0。その版での `python tools/run_locked_checks.py` はR-01〜R-07成功、R-08失敗（`test_startup.gd` のGodot版番号、6と7／3と2の不一致2件）。検査・期待値は変更していない。
- CIと同じGodot 4.7.2-stableを取得。配布ZIPのSHA-256は `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` でCI固定値と一致。実行版は `4.7.2.stable.official.ed1daf0bf`。この実行ファイルをPATHの先頭に置いて検証する。書込可能なHOME・XDG_CACHE_HOMEを用意してFontconfigのキャッシュ出力も確認する。
- 固定版の `godot --headless --editor --import --quit`：終了0、エラー・警告・Fontconfigエラー0件。
- 固定版の `python tools/run_locked_checks.py`：終了0、R-01〜R-08すべてPASS。verifyコマンド、300秒上限、合否判定は不変。R-07はA01〜A14の全14件成功。結果JSONとログを読み、次の実測件数を確認。

| 要件 | 結果 | 実行件数 |
| --- | --- | --- |
| R-01 | PASS / 終了0 | 2 tests / 765 assertions、失敗・pending 0 |
| R-02 | PASS / 終了0 | 5 tests / 946 assertions、失敗・pending 0 |
| R-03 | PASS / 終了0 | 2 tests / 73 assertions、失敗・pending 0 |
| R-04 | PASS / 終了0 | 1 tests / 293 assertions、失敗・pending 0 |
| R-05 | PASS / 終了0 | 2 tests / 79 assertions、失敗・pending 0 |
| R-06 | PASS / 終了0 | 2 tests / 87 assertions、失敗・pending 0 |
| R-07 | PASS / 終了0 | A01〜A14全14件、FIRST_REGION_PASS: checks=14 |
| R-08 | PASS / 終了0 | 17 tests / 2302 assertions、失敗・pending 0 |

- `python tools/check_frozen_files.py`：検証後も終了0、保護26件すべて一致。
- 提出コミットのCI：push後に全ジョブの終了とURLを確認して追記する。
- `python tools/validate_assets.py --strict`：終了0。素材1140件・音15件・パレット3件・字体2件、問題なし。
- `python tools/check_frozen_files.py`：検証前に終了0、保護26件すべて一致。
- 文書と原画の照合スクリプト：既存決定3行、指定の未決・未実装注意、表11行の全文一致、注意3項目の全文一致、依頼書の状態行以外不変、原画11枚と台帳不変、登録先端と最新mainの祖先保持を確認。

## 自己点検

1. 名前・左から2番目の透明な栞を「決定（2026-10-04）」として記録。既存決定3行をメダル置換以外は保持。指定の未決は一致。
2. 付録Bの表11行・注意3項目は依頼書と全文一致。
3. 原画のファイル名・場所・全11件SHA-256は前後および最新mainと一致。
4. 変更範囲は指定4文書に限定する。STATUS・全体計画の付録B以外・後続発注・ゲーム本体・原画・台帳・保護ファイル・検査は変更しない。検査が生成する履歴JSONは検証後に元へ戻して成果物から除外する。
5. 固定版のR-01〜R-08、保護照合、提出コミットのCI全ジョブが終わるまで成功扱いにしない。結果確定後に状態を報告済みへ更新する。

## 統合状態と残る事項

mainには未マージ。今回の発注は、親が成果物を独立確認して統合するため、報告済み・push済み・main未統合で返す指示であり、依頼書のmain反映条件は親の統合後に満たす。既存PR #14を引き継ぐ。STATUS更新・全体計画・後続発注は親担当。

1階の外入口の扱いと暗色敵の見えやすさは、原画をゲームに組み込む段階での確認事項として指定の注意を保持した。今回、それらの接続・戦闘画面での見えやすさ・栞の仕組みは実装も検証もしていない。未決の栞の総数・置き場所・交換内容・交換する人の名前と場所は未決のまま。追加の採用判断はしていない。
