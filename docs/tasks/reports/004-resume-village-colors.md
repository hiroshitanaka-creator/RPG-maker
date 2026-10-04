# 004 村の色調整の保全・検証報告

## 開始時の計画と実照合

- 実行PC：MSI。元リポジトリ `C:\Users\tanak\RPGゲーム`、元HEAD `6384ee81f99a1c3262823fa5fda04075f214f459`、元ブランチ `codex/sprint6-village-color`。追跡先未設定。最新mainとの比較では未pushコミット0件。
- 提出用リポジトリ：`D:\codex\Documents-Codex\2026-10-04\task\repo`。同じMSI上の隔離コピー。元の作業ツリーを一切変更せず、004専用ブランチへ取得済み依頼書SHA `138f9362957e29dbf011696f0e73ae88149d30fc`を引き継ぐ。
- 最新main：`d2ad6c044920a44340b725987b86c36f4adf7952`。001・002・003の状態行はすべて「確認済み」。[開始main CI](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37175069958) は全3ジョブcompleted/successを再照合。004再開は親タスクの明示承認。旧タスクは停止済みと伝達されている。
- 保全：`D:\codex\Documents-Codex\2026-10-04\task\preserved-004`。35件の実体・開始SHA・全追跡SHA・status.z・staged/unstagedのbinary差分・履歴・追跡先を保存し、全35実体を再読込一致確認。staged 0、unstaged 30、untracked 5。元の状態・HEAD・全差分は終端でも再照合する。
- 申告との件数・HEAD・ブランチ差はなし。担当場所内30件／未許可5件。停止時のコードは未検証候補であり、一括採用しない。
- `.agents/skills` は元と隔離コピーのどちらにも存在しない。該当スキルを読んだとの主張はしない。
- 保護契約と凍結26件を読み、今回変更が許可されたPython 4件は保護対象外と照合。専用検証 `tools/check_region2_village_palette.py` は開始時存在しない。
- 実施予定：先に固定Godot import、出典4色の実画素照合、色選択限定再生成、独立2回全バイト比較、既存Python／Godot／25枚Windows/OpenGL／native照合、11負例以上、素材strict・保護26件・R-01〜R-08、対象SHA CI全ジョブ、5条件成立後のみmain反映とmain CI。

## 停止時35件の実体

| パス | 状態 | SHA-256 | 004への扱い |
| --- | --- | --- | --- |
| `assets/interiors/region2_village_inn.png` | ` M` | `2c44f156d032e35078dabf82bb10f75348459509cd6d92d18943a0f061a07573` | 担当一覧内の候補。検証後の提出物と区別 |
| `assets/interiors/region2_village_inn_overlay.png` | ` M` | `0fb8d5dcd841b40054669c90f954b6ab6cbe7eab312c5e142206faa8169cf6ea` | 担当一覧内の候補。検証後の提出物と区別 |
| `assets/interiors/region2_village_item.png` | ` M` | `5e2d86623b7ed6895b3f85c2a1bb375e05dbf6c53ef17ac3d0908850c78ea1e0` | 担当一覧内の候補。検証後の提出物と区別 |
| `assets/interiors/region2_village_item_overlay.png` | ` M` | `4ccb53913dbee84881684bffb0297e106bf5a59a3ed8fbd178df2b8caf0e3faa` | 担当一覧内の候補。検証後の提出物と区別 |
| `assets/interiors/region2_village_shrine.png` | ` M` | `9a11c3a971a96d6174f78bee44d5faceb44d6e5cf3c3557b5a46bb351bd2dbc4` | 担当一覧内の候補。検証後の提出物と区別 |
| `assets/interiors/region2_village_shrine_overlay.png` | ` M` | `5822413322555fb018228a04e5e97bad3f5299402cd083c64ff8ef176fcd9a19` | 担当一覧内の候補。検証後の提出物と区別 |
| `assets/interiors/region2_village_weapon.png` | ` M` | `a3155d680949550645e0b0c19e6131858f0d045d003b93eea1cdcb0e9b6dba41` | 担当一覧内の候補。検証後の提出物と区別 |
| `assets/interiors/region2_village_weapon_overlay.png` | ` M` | `84e1bac257cd9bf51e730251fe6055787d6f0e34a3e6cd05d459762351040509` | 担当一覧内の候補。検証後の提出物と区別 |
| `assets/palette/natural.gpl` | ` M` | `e0221fc6fd01e7adddaafc150f13302b903b24659323b0fe43bd51cfccf969f8` | 担当一覧内の候補。検証後の提出物と区別 |
| `assets/source_records/region2-village-backdrops.json` | ` M` | `48dee756c7da49687191dc23adda930fa43703666ed956aa4bc24f90320d685b` | 担当一覧内の候補。検証後の提出物と区別 |
| `assets/town_backdrops/region2_village_exterior.png` | ` M` | `c894cdc87e4204747dbb2d337e4c8c52e89172a2dab842023a4b7644938284d6` | 担当一覧内の候補。検証後の提出物と区別 |
| `assets/town_backdrops/region2_village_exterior_overlay.png` | ` M` | `290c7719d17811695083046f30e14aa24ae4dee6afed51dd5d701b806bd6ae0e` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/exterior/collision-overlay.png` | ` M` | `dbe0f5674c079f90dfb2b2b006841671b13d143a647794b32873de8696341f87` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/exterior/grid.png` | ` M` | `6e08acf70b2f61c7630904f53aa0ca9f8a623c590cb005c56fb84845108f2c42` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/exterior/source-comparison.png` | ` M` | `6153fdb249847c86c4459a9057d0cebe714a1961a2aac18a3412675bad95f072` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/inn/collision-overlay.png` | ` M` | `8a99cf1ce76bbb916fc9b73939f74bb76165e6fc5fb7c47e6c8cb2a50eeef306` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/inn/grid.png` | ` M` | `ec706d5e51f08d9ed3c7e3b215c6cbaa29d5439ca5c50ea1be1dfe6ed5cd27c2` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/inn/source-comparison.png` | ` M` | `cbc54fc75ac15f25c23fb04564730ddb2aaeb0a57f05ee079c80111afbfc509d` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/item/collision-overlay.png` | ` M` | `4583cfa791fae879578907d3f0bac15f923d137422e0d894d33782da993e4c25` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/item/grid.png` | ` M` | `0b5873db8d63d7088ce945a90340fc844c3116bc33544af47bad4a77259f3a48` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/item/source-comparison.png` | ` M` | `6a488935b24a40f12155f6e9d0d1a165124e3ed3db5df65c1e825dfee043b759` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/shrine/collision-overlay.png` | ` M` | `b20d51f2af1508da7f31de0451e3105484f6930dad40bbb32ba0ce9a068fb937` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/shrine/grid.png` | ` M` | `a13f85667ff08745b62634346cb09e94e1d8409ba2413511da4a90a7e11e5bbd` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/shrine/source-comparison.png` | ` M` | `fa896c2449d073c53b615ecb294a1bc009283d3a55b8e2266b0d6ef81d28c3a2` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/weapon/collision-overlay.png` | ` M` | `0283f67ddffdd606b5e09ec161b51bfcc0ad844e13a1537ebc59d3b53cd3a778` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/weapon/grid.png` | ` M` | `d295380d3a82544cca34390772c0db7bc606416ddb74dc841085051d0ecbd2d8` | 担当一覧内の候補。検証後の提出物と区別 |
| `docs/verification/region2-village-backdrops/weapon/source-comparison.png` | ` M` | `981b9e83992a1245ceb19648abfd90a9f68f4dda11d92f37156cd673ebbe76e7` | 担当一覧内の候補。検証後の提出物と区別 |
| `tools/build_region2_village_backdrops.py` | ` M` | `aa4eec8ce97afa8267cd6970841a9104a26cd986c813eb724bf851233d020a9d` | 担当一覧内の候補。検証後の提出物と区別 |
| `tools/check_first_region_gado_data.py` | ` M` | `ad5258113a24b840b3ca2f908d79b445457b9b03f18da3b86a0e455a3d2d57a2` | 担当一覧内の候補。検証後の提出物と区別 |
| `tools/validate_assets.py` | ` M` | `ff881f2c54f643bb09cf5aaf6e780d807d9ed194f7f29993b6dae115d09cd6b5` | 担当一覧内の候補。検証後の提出物と区別 |
| `assets/source_records/region2-village-colors.json` | `??` | `2a483dfdc680b7c47ab1646e8b9c9048313e3a7bfb6b31c8fb2be232fd52d9fd` | 保全・読取りのみ（担当一覧外） |
| `docs/verification/region2-village-backdrops/color-palette-checks.json` | `??` | `aceab395e564a80a7a00aee8bf4265547e38b50a454c958fb7e17e838cd5a0d8` | 保全・読取りのみ（担当一覧外） |
| `tools/check_region2_village_colors.py` | `??` | `a500fc93cde8d1a90aebd29e14d4fa7c8e63fa45cb0b9d154b2bef2276911a8f` | 保全・読取りのみ（担当一覧外） |
| `tools/check_village_palette.py` | `??` | `79dbab0ca0507eaf349975adb62e153d44af6fc82637088547330adf4149d00b` | 保全・読取りのみ（担当一覧外） |
| `tools/village_palette.py` | `??` | `10d79940e2a658a17e0513bc2ec7763ce729df1fab8bc7bfebd214c334b41fee` | 保全・読取りのみ（担当一覧外） |

## 一覧外候補の実パスと役割

- `assets/source_records/region2-village-colors.json`：追加4色の原画・座標・SHAと選択理由を記録した未許可の2つ目の出典記録。変更・stage・commitしない。
- `tools/check_region2_village_colors.py`：6384ee81との形状・色差・対象外素材照合と比較画像生成の候補。変更・stage・commitしない。
- `tools/check_village_palette.py`：旧80色と11負例を検証する候補。変更・stage・commitしない。
- `tools/village_palette.py`：原画4色の固定出典を検証する共通処理候補。変更・stage・commitしない。
- `docs/verification/region2-village-backdrops/color-palette-checks.json`：停止時の11負例の結果。未照合JSONなので保全・参照のみ。変更・stage・commitしない。

専用処理は依頼書が新設を明示許可した `tools/check_region2_village_palette.py` に実装し、出典は既存 `region2-village-backdrops.json` の限定追記へ集約する。元候補は削除せず保全のまま。未許可パスの追加を要求せず、担当範囲の手段を使う。

## main取込みの選択

元をローカルclone（no-hardlinks）し、隔離コピーだけでGitHubをfetch、既存004ブランチへswitchした。旧HEADからmainへ追加済みの17文書はmain由来であり004の新規差分へ混ぜない。元ブランチへのcheckout/reset/stash/cleanは一切なし。戻し方は隔離コピーの提出コミットを通常revertすること。元の35件は保全先または元ツリーで再読込できる。候補保存だけのコミットは作らず、検証済み提出物をcommitする。

## 検証・自己点検

必須検査・提出SHA CI・main反映と同SHAのmain CIは以下の実結果。初の見た目採否、歩きやすさ、施設や村の完成は未確認。

## 追加色と出所・必要性

旧80色1940バイトSHA `1b1c00dd929b96b64703972a0ae9368c36636b96c8f717dded78524e57913088` は不変。現在84色2020バイトSHA `e0221fc6fd01e7adddaafc150f13302b903b24659323b0fe43bd51cfccf969f8`。原画5点は固定mainと全バイト一致。4色とも旧色の最近傍置換誤差があり、5背景で実使用されるため数合わせ追加ではない。

- `#7E4C2C` RGB [126, 76, 44]：`assets/_incoming/owner-2026-10-03-region3-port/01-oasis-inn.png`、座標[1072, 276]、原画SHA `3bec585c4bfe1fda0401b18b084832d51733bbfbe3cbffb6ec55a6eb7d9c3301`。旧近似RGB [116, 90, 50]、二乗誤差332、使用画素63900。土色の階調を原画に合わせて保持するため。
- `#CC773D` RGB [204, 119, 61]：`assets/_incoming/owner-2026-10-03-region3-port/03-oasis-weapon-shop.png`、座標[1128, 647]、原画SHA `81a4fa6e5f68c494bef92bd67a0c400193a2c30711472f6ce1704775968495d9`。旧近似RGB [191, 105, 77]、二乗誤差621、使用画素54368。土色の階調を原画に合わせて保持するため。
- `#A7592D` RGB [167, 89, 45]：`assets/_incoming/owner-2026-10-03-region3-port/01-oasis-inn.png`、座標[782, 781]、原画SHA `3bec585c4bfe1fda0401b18b084832d51733bbfbe3cbffb6ec55a6eb7d9c3301`。旧近似RGB [154, 96, 72]、二乗誤差947、使用画素221036。土色の階調を原画に合わせて保持するため。
- `#713D1D` RGB [113, 61, 29]：`assets/_incoming/owner-2026-10-03-region3-port/01-oasis-inn.png`、座標[1157, 150]、原画SHA `3bec585c4bfe1fda0401b18b084832d51733bbfbe3cbffb6ec55a6eb7d9c3301`。旧近似RGB [104, 66, 47]、二乗誤差430、使用画素81526。土色の階調を原画に合わせて保持するため。

村外1538素材は開始mainのblobと実ファイルhash-objectが全件一致。台帳は全バイト一致、原画全件・パレット既存部分・対象外画像を変更していない。通行world、形状定義、背景アルファ、上層アルファ、通行・上層マスク、色以外の全記録は固定mainと一致。

停止候補の選択アルゴリズムの申告を実行済み扱いにせず、出典記録の方法を実際に再実行した採取画素・置換誤差・使用数・原画色差の検証に合わせた。停止時の原記録は保全先でバイト不変。

| 対象 | 開始main RGB RMSE | 今回RGB RMSE | 形状 |
| --- | --- | --- | --- |
| exterior | 12.356343 | 11.836524 | 全画素一致 |
| inn | 11.903279 | 8.978143 | 全画素一致 |
| item | 12.273142 | 10.347536 | 全画素一致 |
| weapon | 11.251100 | 8.546995 | 全画素一致 |
| shrine | 9.457948 | 8.414967 | 全画素一致 |

## 実行コマンドと結果

Godotは元PCの4.7.2-stableの実行ファイルを隔離repo内`.tools/godot`へ複製して版を実測した（`4.7.2.stable.official.ed1daf0bf`）。PATHに`.tools/bin/godot.cmd`を設定して同版のconsole実行ファイルを呼ぶ。APPDATAをタスク内の`runtime-profile`へ設定し、実保存・ログも他作業と分けた。R検査は同一提出差分・同一保護ファイル・同一Godotを全バイト引継いだ`qa004`で実行し、既存の範囲外検証記録を提出repoへ上書きしない。検査コマンド・アサーション・時間上限は変更しない。

| コマンド | 終了値・実結果 |
| --- | --- |
| `git status --short`、`git diff --binary`、`git diff --cached --binary`、`git branch -avv`、`git log origin/main..6384ee81` | 元35件・staged0・未push0。保全全実体と差分の再読込一致 |
| `godot --version` | 0、4.7.2.stable.official.ed1daf0bf |
| `godot --headless --editor --import --quit` | 0、最終隔離設定でERROR/WARNING/Parse Errorなし |
| `godot --headless --import` | 0、ERROR/WARNING/Parse Errorなし |
| `python -B tools/build_region2_village_backdrops.py` | 0、5地形・10画像・各64色。world／registry差分0 |
| `python -B tools/check_region2_village_backdrops.py` | 0、244項目。2つの独立Temp出力との全バイト一致。原画変換差0 |
| `python -B tools/check_region2_village_scope.py` | 0、旧固定dad3fca→f53dcb5の10領域・CI全文一致。004の差分検査とは区別 |
| `godot --headless --path . --script res://tools/check_region2_village_backdrops.gd` | 0、2170項目。最終実行ERROR/WARNINGなし |
| `godot --path . --display-driver windows --rendering-method gl_compatibility --resolution 512x288 --position -32000,-32000 --script res://tools/check_region2_village_backdrops.gd -- --capture` | 0、Windows/OpenGL NVIDIA RTX4050、2230項目・25枚。最終実行stderr空。ウィンドウはHiddenで起動 |
| `python -B tools/check_region2_village_native.py` | 0、25枚の独立合成差0。手前遮蔽0、奥の可視・遮蔽各8以上。GPU許容差1の条件を維持 |
| `python -B tools/check_region2_village_palette.py --comparisons` | 0、80色1940バイト不変・原画4色一致・5形状一致・対象外1538件一致・15負例拒否・5比較生成 |
| `python tools/validate_assets.py --strict` | 0、1134素材・15音・2字体・3パレットに問題なし。不足素材なし |
| `python tools/check_frozen_files.py` | 0、保護26件一致 |
| `python tools/check_first_region_gado_data.py`（隔離QA） | 0、既存SHA・本文・5 variants・2回生成を維持。INTRO_MEDIA/INTRO_DATA_PASS |
| `python tools/run_locked_checks.py`（隔離QA） | 0、R-01〜R-08すべてPASS。警告・構文エラー・pending0 |
| `python D:\Codex\.codex\scope-lock\scripts\verify_cli.py`（隔離QA） | 0、R-01〜R-08すべてPASS。指定のpython3コマンドは同じPython 3.13.5のpythonで実行 |

最初の元パスでのimportは、portable engineのeditor設定保存先への権限エラーを検出したため成功扱いにしていない。その後engineを隔離コピーしてimportを再実行。続く初回runtime/captureは検査自体がPASSでもuserログの書込エラーがあったため、APPDATAを隔離して両方を再実行しERRORなしを確認した。失敗した初回のexit0を合格証拠に使っていない。git fetchもsandboxのschannel認証／OpenSSL証明書エラー後、通常のWindows資格情報を使う実行で取得し、TLS検証は無効化していない。

## 負例の実内容

停止時候補のPythonとJSONの実体を読み、同じ11入力変換を再実行した。旧バイト150の1bit反転、旧4/5行交換、5色目と記録追加、別RGBと記録差替え、追加4色削除、追加順序反転、原画SHA差替え、採取座標(0,0)差替え、出所をbase.gplへ差替え、実原画末尾1bit反転、無記録末尾文字追加。すべて拒否。

追加で旧色行削除、出典original欄削除、reason欄削除を拒否。村外は実`assets/backgrounds/castle.png`をTempへ複製して末尾1bitを反転したファイルの実hash-objectを渡し、開始mainとの不一致を拒否。元素材へ異常を書き込まない。件数だけで停止時網羅性の代用にしていない。

## R-01〜R-08の実結果

| 要件 | 終了値 | tests | assertions | pending | 結果 |
| --- | --- | --- | --- | --- | --- |
| R-01 | 0 | 2 | 765 | 0 | PASS |
| R-02 | 0 | 5 | 946 | 0 | PASS |
| R-03 | 0 | 2 | 73 | 0 | PASS |
| R-04 | 0 | 1 | 293 | 0 | PASS |
| R-05 | 0 | 2 | 79 | 0 | PASS |
| R-06 | 0 | 2 | 87 | 0 | PASS |
| R-07 | 0 | A01〜A14 | 14 | 0 | PASS |
| R-08 | 0 | 17 | 2302 | 0 | PASS |

R実行記録：`2026-10-04T04:13:31.205068+00:00`、契約SHA `601a7452fe13be169d28327dfce1946b5a2ee2e7a1b1d8f92924d77dc95dedb3`。scope-lock-current.jsonは隔離QAに保存し、範囲外の既存提出記録へ混ぜない。ログは`qa004/.tools/verification/`、親タスクにも終了値とこの表を提示する。

## 最新比較と未評価

[004比較一覧](../../verification/region2-village-backdrops/README.md#004-の最新比較) に原画・開始main・今回・目標・実描画を識別した5比較。最新25枚は同じ5フォルダのnative-*.png。比較index、原画・目標・実描画のSHAを保存した。見た目の初回採否は未確認、指揮役の実物確認も未実施。本件で歩きやすさや施設／村の完成を推定しない。既存PLAYTEST_QUEUEの人間評価を保持し、範囲外の同ファイルへ追記しない。

## 提出・統合と自己点検

- 実装・素材・検証・比較の提出SHA：`acf064884c9f0c17d2ac4f57a624365175789640`。統合SHAも同じ（mainへの通常fast-forward反映）。開始main `d2ad6c044920a44340b725987b86c36f4adf7952`から関連する004依頼書登録`138f936`と提出コミットだけを反映。旧作業の無関係なコミットは0件。
- 反映直前にCI全3ジョブ・R全8・保護26件・既存検査と時間上限の保持・77提出パスの限定一覧一致を照合し、5条件すべての成立後に通常pushした。保護と契約・既存CI・本番処理・全原画・村外素材・台帳を変更していない。
- 1：停止全35件保全。終端でも元HEAD・status・staged/unstaged差分・全35実体・全追跡SHA一致。
- 2：原画5点・旧80色1940バイト不変。追加4色はSHAと実座標画素一致。
- 3：対象10画像の色だけ。全world・通行・入口・家具・寸法・上層形状と本番未接続状態を固定mainに照合。
- 4：独立2回全バイト再生成、244検査、15負例、最新25枚、素材strict成功。
- 5：ローカルR-01〜R-08・保護26件成功。提出SHAとmainのCIは全3ジョブがcompleted/success。
- 6：提出77全パスを004限定一覧と機械照合済み。stagedと許可全パス集合も一致。範囲外5候補と他作業はstage／commit／pushしていない。
- 7：初の採否・歩きやすさ・施設／村の完成は未確認／未実装。本件の成功から推定していない。

本件の実装・素材・検査の未達：なし。未評価：指揮役の実物確認、依頼者の初の見た目採否。範囲外候補を追加採用する判断は不要（許可された専用検証と既存台帳で検証を実装した）。新機能は担当外。

## 変更した全ファイル（実装・証拠77件）

- `assets/interiors/region2_village_inn.png`
- `assets/interiors/region2_village_inn_overlay.png`
- `assets/interiors/region2_village_item.png`
- `assets/interiors/region2_village_item_overlay.png`
- `assets/interiors/region2_village_shrine.png`
- `assets/interiors/region2_village_shrine_overlay.png`
- `assets/interiors/region2_village_weapon.png`
- `assets/interiors/region2_village_weapon_overlay.png`
- `assets/palette/natural.gpl`
- `assets/source_records/region2-village-backdrops.json`
- `assets/town_backdrops/region2_village_exterior.png`
- `assets/town_backdrops/region2_village_exterior_overlay.png`
- `docs/decision-log.md`
- `docs/region2-village-backdrops.md`
- `docs/tasks/004-resume-village-colors.md`
- `docs/tasks/reports/004-resume-village-colors.md`
- `docs/verification/region2-village-backdrops/README.md`
- `docs/verification/region2-village-backdrops/color-integrity-004.json`
- `docs/verification/region2-village-backdrops/comparison-index-004.json`
- `docs/verification/region2-village-backdrops/data-checks.json`
- `docs/verification/region2-village-backdrops/exterior/collision-overlay.png`
- `docs/verification/region2-village-backdrops/exterior/color-review-004.png`
- `docs/verification/region2-village-backdrops/exterior/grid.png`
- `docs/verification/region2-village-backdrops/exterior/native-behind-empty.png`
- `docs/verification/region2-village-backdrops/exterior/native-behind.png`
- `docs/verification/region2-village-backdrops/exterior/native-detail.png`
- `docs/verification/region2-village-backdrops/exterior/native-empty.png`
- `docs/verification/region2-village-backdrops/exterior/native-start.png`
- `docs/verification/region2-village-backdrops/exterior/review-comparison.png`
- `docs/verification/region2-village-backdrops/exterior/source-comparison.png`
- `docs/verification/region2-village-backdrops/inn/collision-overlay.png`
- `docs/verification/region2-village-backdrops/inn/color-review-004.png`
- `docs/verification/region2-village-backdrops/inn/grid.png`
- `docs/verification/region2-village-backdrops/inn/native-behind-empty.png`
- `docs/verification/region2-village-backdrops/inn/native-behind.png`
- `docs/verification/region2-village-backdrops/inn/native-detail.png`
- `docs/verification/region2-village-backdrops/inn/native-empty.png`
- `docs/verification/region2-village-backdrops/inn/native-start.png`
- `docs/verification/region2-village-backdrops/inn/review-comparison.png`
- `docs/verification/region2-village-backdrops/inn/source-comparison.png`
- `docs/verification/region2-village-backdrops/item/collision-overlay.png`
- `docs/verification/region2-village-backdrops/item/color-review-004.png`
- `docs/verification/region2-village-backdrops/item/grid.png`
- `docs/verification/region2-village-backdrops/item/native-behind-empty.png`
- `docs/verification/region2-village-backdrops/item/native-behind.png`
- `docs/verification/region2-village-backdrops/item/native-detail.png`
- `docs/verification/region2-village-backdrops/item/native-empty.png`
- `docs/verification/region2-village-backdrops/item/native-start.png`
- `docs/verification/region2-village-backdrops/item/review-comparison.png`
- `docs/verification/region2-village-backdrops/item/source-comparison.png`
- `docs/verification/region2-village-backdrops/native-pixel-checks.json`
- `docs/verification/region2-village-backdrops/palette-validation-004.json`
- `docs/verification/region2-village-backdrops/shrine/collision-overlay.png`
- `docs/verification/region2-village-backdrops/shrine/color-review-004.png`
- `docs/verification/region2-village-backdrops/shrine/grid.png`
- `docs/verification/region2-village-backdrops/shrine/native-behind-empty.png`
- `docs/verification/region2-village-backdrops/shrine/native-behind.png`
- `docs/verification/region2-village-backdrops/shrine/native-detail.png`
- `docs/verification/region2-village-backdrops/shrine/native-empty.png`
- `docs/verification/region2-village-backdrops/shrine/native-start.png`
- `docs/verification/region2-village-backdrops/shrine/review-comparison.png`
- `docs/verification/region2-village-backdrops/shrine/source-comparison.png`
- `docs/verification/region2-village-backdrops/weapon/collision-overlay.png`
- `docs/verification/region2-village-backdrops/weapon/color-review-004.png`
- `docs/verification/region2-village-backdrops/weapon/grid.png`
- `docs/verification/region2-village-backdrops/weapon/native-behind-empty.png`
- `docs/verification/region2-village-backdrops/weapon/native-behind.png`
- `docs/verification/region2-village-backdrops/weapon/native-detail.png`
- `docs/verification/region2-village-backdrops/weapon/native-empty.png`
- `docs/verification/region2-village-backdrops/weapon/native-start.png`
- `docs/verification/region2-village-backdrops/weapon/review-comparison.png`
- `docs/verification/region2-village-backdrops/weapon/source-comparison.png`
- `tools/build_region2_village_backdrops.py`
- `tools/check_first_region_gado_data.py`
- `tools/check_region2_village_backdrops.py`
- `tools/check_region2_village_palette.py`
- `tools/validate_assets.py`

## 提出とmainのCI実結果・終了状態

- 提出専用ブランチ：SHA `acf064884c9f0c17d2ac4f57a624365175789640`、[37176760956](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37176760956)。全3ジョブの終了を確認。
  - Godot・凍結受入テスト：completed/success、終了2026-10-04T04:25:02Z。
  - 素材検査：completed/success、終了2026-10-04T04:22:25Z。
  - 試遊前の通常戦闘・案内・画面・復帰検査：completed/success、終了2026-10-04T04:25:37Z。
- main反映後：SHA `acf064884c9f0c17d2ac4f57a624365175789640`、[37177002200](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37177002200)。全3ジョブの終了を確認。
  - 素材検査：completed/success、終了2026-10-04T04:28:07Z。
  - 試遊前の通常戦闘・案内・画面・復帰検査：completed/success、終了2026-10-04T04:29:59Z。
  - Godot・凍結受入テスト：completed/success、終了2026-10-04T04:29:29Z。

`gh run watch --exit-status`も提出／mainとも終了値0。途中で匿名GitHub APIが403回数上限に達したため、接続済みPCの認証済みCLIへ切替えてmain全ジョブを再照合した。資格情報は表示・記録・commitしていない。CI失敗として扱っていない。

この報告の最後の更新は、CI実測記録と004状態行の登録だけであり、実装・素材・検査・比較の提出SHAは上記acf0648に固定する。報告の更新コミットとそのmain最終HEAD／最終CIは、Git履歴および親タスクへの終了通知で識別する。自分自身を含むGitコミットSHAを本文へ自己参照させない。

状態は「報告済み」。指揮役の実物確認まで「確認済み」にしない。依頼者の初の見た目採否も未確認。初の採否は5比較をまとめて1回で依頼者に提示する。施設機能・人物・商品・職業解放・遺跡・本編接続は本件で実装していない。

終了時の元場所：HEAD6384ee81、元ブランチ、30未コミット＋5未追跡、全35実体・全追跡SHA・全staged/unstaged差分は開始時と一致。保全物は削除していない。提出repoは実装push後clean、未push0。最後の報告更新も通常commit・pushし、範囲外の新規制作へ進まない。

指揮役の判断：004の実物確認、依頼者の初の見た目採否の取りまとめ。範囲外候補5件の担当追加は不要で、保全のまま残す。
