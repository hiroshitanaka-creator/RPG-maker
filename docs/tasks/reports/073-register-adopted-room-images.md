# 073 採用済み室内5枚の素材登録報告

## 作業前の確認と計画

- 基点mainは `8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`。専用ブランチは `codex/task-073-register-adopted-room-images`。初回の073番号競合なし、開始差分・mainより先のコミット0。続行時も同じmainを確認した。
- `AGENTS.md`、`.scope-lock`、伝言板README・テンプレート、素材規約は初回読取りから不変と再照合した。R-01〜R-08、3/4人・順/逆方向、全ゲームの受入条件を維持する。
- 指定の `godot-dev-director` / `godot-game-verification` は実際の `.agents/skills` と `/workspace/.agents` に存在しない。未導入を明記し、新規導入・同梱コード・テスト基盤の追加はしていない。
- 初回は採用ZIP転送と出所形式で阻害された。2026-10-18 10:19 JSTの依頼者「Aで良いよ」により、5原画を完全パス＋実ファイルSHA-256で限定するowner出所照合が承認された。予定範囲を従来10ファイル＋`tools/validate_assets.py`の計11ファイルとした。
- 計画：承認・入力の再照合→採用PNG実表示→限定出所照合と原バイト登録→checkout外の正負例→登録後の規定検証→差分・原ログ・機械証拠をLibraryで親へ渡す。単独実行。

## 結果と変更一覧

クラウド作業領域で採用PNG5枚を配置し、素材台帳へ `interior_backdrop` を5件追加した。登録後のローカル検証は成功。GitHub保存・CI・main反映は未実施であり、親が公式接続で保存する。

| ファイル | 変更 |
| --- | --- |
| `assets/interiors/region3_room_inn.png` | 採用ZIPの原バイトで追加 |
| `assets/interiors/region3_room_item_shop.png` | 同上 |
| `assets/interiors/region3_room_weapon_shop.png` | 同上 |
| `assets/interiors/region3_room_shrine.png` | 同上 |
| `assets/interiors/region3_room_armor_shop.png` | 同上 |
| `assets/registry.json` | 1154件を保持して5件追加。audio 15件、fonts 2件、defaultsほか不変 |
| `assets/source_records/region3-room-adoption-2026-10-17.json` | 採用・入力・原画hash・承認A・以前の加工・今回のコピー・実表示の記録 |
| `tools/import_region3_adopted_rooms.py` | ZIPと全5PNGを先に照合し、`--apply` で原バイトコピー。既定は検査のみ。異なる既存PNGの上書きは拒否 |
| `tools/validate_assets.py` | owner出所照合に5原画の完全パスと固定SHAだけを追加 |
| `docs/tasks/073-register-adopted-room-images.md` | 承認Aと11ファイルの範囲、受入条件を反映 |
| 本報告書 | 作業・検証・自己点検・引渡しの記録 |

## 入力と原バイト照合

採用ZIPは `adopted-room5-2026-10-17.zip`。Library `libfile_7d30c41f2a60819198bf567516bde485` の原ZIPを、親が私有Drive `1FT2or3SgzWWZrazAEmjlEQME2rt74we-` に保全した。公式Driveの通常参照転送は403だったが、既存callerが同一851055bytesの1件に限って `include_base64` を明示選択し、その公式読取りで取得できた。共有・認証・ネットワーク制限は変更していない。

実測851055 bytes、SHA-256 `25cab1603a081415699b87722d6211ce0b56da6932c02034c0f3dbb988b4aabf`。ZIPのCRC、全7件、adoption.jsonの5件を照合した。PNGは原バイトで展開して全5枚を実表示し、入口・家具・部屋の対応を確認した。再保存・生成・減色・拡大はしていない。

| 対象 | bytes | 色数 | SHA-256 |
| --- | ---: | ---: | --- |
| inn | 184495 | 54 | `52723c0560ca54cf9aff695d383a17235b8f224058dda7a2367304e79cb5e007` |
| item-shop | 168249 | 60 | `76bf5d755bf8b98d7125c800abf02fb27b2b5dda080ac43ff1f966a9c65469cb` |
| weapon-shop | 167018 | 63 | `be55b08fc7da5421f84c8c88001586e523369b9dfff8e950d83bd96500e6d93c` |
| shrine | 166573 | 55 | `46c00cbdc2ad0d02e1d05662793c15bb2117ea28cb9f0ceeab75f118ce8065c8` |
| armor-shop | 165817 | 57 | `eefd5131abf790c2a8e7ff5393054898f8bf126b722cca2982e634a4b21f4b31` |

全5枚448×384、RGBA8、alpha255、32倍数、各64色以下。natural.gplは84色・2020 bytes・SHA `e0221fc6fd01e7adddaafc150f13302b903b24659323b0fe43bd51cfccf969f8` のまま、各画像はその部分集合。採用ZIP・配置先・既存v2納品の5PNGは全バイト一致。原画は固定commit `e61ab37f9542648f25b731cd33924e11e134920b` と一致した。

## 出所照合の具体差分

`OWNER_ADOPTED_ROOM_ORIGINALS` に依頼で固定された5つの原画パスとSHAを記載した。`source=owner` の原画存在・`..` 拒否条件を維持し、従来9月26日フォルダ以外の場合だけ、この表の完全一致パスと実際に読んだ原画のSHA一致を要求する。10月4日フォルダ全体・荷受け所・別名コピーは許可しない。台帳に自己申告されたhashだけで許可しない。

author、license、provided_at、modified、原画存在の条件を維持した。既存1154件の出所判定は旧版と同じ。`check_provenance` 以外の8関数はASTで不変と照合した。色・寸法・パレット・alpha・音・字体などの既存検査を変更していない。

台帳は `source=owner`、`author=依頼者`、`license=LicenseRef-Owner-Provided`。`provided_at=2026-10-18` は今回の採用PNGを073のconsumer環境で受領した日を指すと出所記録に明記した。原画生成日・初回提供日ではない。Grokの個別生成日時・プロンプトは未確認のままnullで残し、生成素材として登録していない。これらの不明情報は承認Aで採用したowner形式の阻害要因にはしていない。

## 診断と登録後検証

追加診断はcheckout外に置き、`test/` は変更していない。

- 出所57ケース成功：5正例、各原画のhash違い・欠落、author/license/provided_at/modified/original_file欠落、author/license不一致、対象外パス、荷受け所、同hashの別名、別表記、既存9月26日素材の正例・欠落拒否。既存1154件の判定も旧版一致。
- インポーターの正常系・再実行で原バイト一致。不正ZIP3ケースは拒否し、配置済み5PNGを変更しない。初回のPillow getdata非推奨警告はgetcolorsへ変更して解消し、最終版の正常系を再実行した。
- 処理器をimportしない別診断でZIP・adoption.json・PNGヘッダー・色・alpha・原画・旧納品・台帳保全を照合した。

Godotは依存関係記録の公式4.7.2 ZIP SHA `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` と実行ファイルを照合済み。版は `4.7.2.stable.official.ed1daf0bf`。専用の書込可能なXDG保存先を使った。

許可外の検証文書を作業ブランチで変更しないよう、登録後のコード・台帳・全素材を隔離コピーして実行した。検証した8つの実行関連変更ファイル（validator・importer・registry・PNG5枚）は最終提出物と全バイト一致。

| コマンド | 登録後の結果 |
| --- | --- |
| `godot --headless --editor --import --quit` | 終了0、60.81秒 |
| `timeout 600 godot --headless --import` | 終了0、5.97秒 |
| `python3 tools/validate_assets.py --strict` | 終了0、画像1159・音15・字体2・パレット3、問題なし |
| `python3 tools/run_locked_checks.py` | 終了0、R-01〜R-08全PASS、115.50秒。各verifyの300秒上限は不変 |
| `python3 tools/check_frozen_files.py` | 終了0、保護26/26一致。作業ブランチでも同結果 |
| `git diff --check` | 終了0 |

R-07はA01〜A14と最終PASS行を確認。R-08は25テスト・3046 assertion、失敗・pendingなし。各Rの全生ログと取り込みログを監査し、SCRIPT ERROR・ERROR・WARNING・Parse Error・リーク警告・FAILマーカーなし。終了0だけを根拠にしていない。初回の登録前基準版の成功は別の `baseline-evidence/` に保存し、上の登録後成功と区別した。

## 自己点検・引渡し・残事項

- 既存追跡7721ファイル中、変更はregistryと許可されたvalidatorの2件。他7719件は不変。新規9件を加え、変更範囲は正確に11ファイル。
- 原画・パレット・ゲームコード・地図・NPC・通行・物語・音楽・保護ファイル・既存test・CI・親担当decision-log/READMEは不変。066・荷受け所・城は対象外。
- 原画の実生成日・個別指示は未知のまま。取得日、原画のGit登録日、採用日を生成日に流用していない。
- 3/4人・順/逆方向の全ゲーム受入条件と既存検査は保持した。今回、新規GitHub CI全行列を実行したとは扱わない。ゲームへの配線・人物配置・通行設定は未実施で、本依頼の範囲外。
- commit・push・PR・mainマージ・Drive書込みは未実施。親が公式GitHub接続で保存し、CIを確認する。main取込み保留は維持する。
- 引渡しZIPは11ファイルの原成果物、binary patch、validator具体差分、採用入力ZIP、adoption.json、入出力manifest、正負例診断、独立照合、登録後原ログを収録。ZIP全件をbytes/SHA/CRC照合する。Library ID・最終ZIPのbytes/SHA・読戻し結果は自己参照を避けZIP外の納品返答に記録する。


## 073 CI回帰修正（正式head 93585b4、PR #49）

### 事前確認と今回の範囲

正式head `93585b4c1817b99ec4bcf0951bfd2e65d7992004` を新しい作業領域へ取得し、初期差分0から開始した。前回成果と履歴は保持した。AGENTS.md・.scope-lock・073依頼書・伝言板・依存版を確認。指定2スキルはこのheadの `.agents/skills` と `/workspace/.agents` にも未導入で、導入・GUT追加はしていない。

計画は、原検査で失敗再現→原生成器2回の出力差分で原因確定→台帳配列だけ修正→同CIの後続・規定検査→2ファイルの差分と証拠を親へ引渡し。単独実行。今回の変更は **assets/registry.json と本報告書の2件のみ**。作業用checkoutへ検証生成物を書かず、checkout外の隔離コピーに同一のコード・素材・Git参照を用意して全検証を行った。

### 原因と修正前の実測

push job `117780794247` とPR job `117780978528` の原ログを取得し、両方の `VILLAGE_SCOPE_PASS`、素材1159件正常、続く `VILLAGE_DATA_FAIL: 2回再生成の全バイト一致: assets/registry.json` と `checks=244`、exit 1を確認した。ローカルの正式headでも原 `check_region2_village_backdrops.py` を無変更で実行し、244検査中の同じ台帳全バイト比較だけが失敗、exit 1となった。

`build_region2_village_backdrops.py` は既存村10件を除いた後、同じ10件を台帳末尾へ再追加する。073がその村10件の後ろへ新5件を追加したため、再生成で「村10件→新5件」が「新5件→村10件」へ入れ替わった。原生成器を独立に2回実行して全38出力を保存・比較したところ、2回の出力同士は全バイト一致し、正式headとの差はregistryだけだった。全1159項目の内容とその他の台帳キーは同一で、差は配列順と確定した。

前回のローカル確認は素材strict・Godot・R・保護照合等までで、この村再生成の全バイト検査を実行していなかった。今回、失敗したassets jobの同じ検査と後続を実行範囲に含めた。検査の比較範囲を縮めていない。

### 実修正と不変性

新5件の連続ブロックだけを既存村10件の直前へ移した。0始まり位置1154〜1158から1144〜1148への移動。既存1154件の内容と相対順、新5件の全フィールドと相対順、他の台帳キーは不変。JSON差分は95行の移動だけ（95追加・95削除）。

- 修正前registry SHA-256：`c00be4c2c82f324c568b07d3c23937242248fa1c273ef1872771e63c2e3df9ac`
- 修正後registry SHA-256：`81f9a9690551a5d9f7cbdebc2aa9d20e4041bc72ddaeb476deb0e86d4024b514`
- 修正後の原生成器2回のregistryも上記修正後SHAと一致。全38出力について、入力＝1回目＝2回目の全バイト一致を確認。
- assets配下PNG1380枚は正式headと全hash一致。採用5枚、原画、パレットは不変。既存生成器・検査器・validator・workflow・test・保護契約は変更なし。

### 修正後の実測結果

以下は今回の修正後コピーで実行した結果。CI上の新しい成功とは区別する。Godotは依存記録の4.7.2 ZIP SHAと実行ファイルを再照合し、`4.7.2.stable.official.ed1daf0bf` を使用した。原検査・期待値・各300秒のR上限・600秒のimport・120秒の村runtimeを維持。

| 実行コマンド | exit | 実測時間 |
| --- | ---: | ---: |
| `timeout 600 godot --headless --editor --import --quit` | 0 | 4.97秒 |
| `timeout 600 godot --headless --import` | 0 | 5.24秒 |
| `python3 tools/validate_assets.py --strict` | 0 | 7.79秒 |
| `python3 tools/check_region2_port_backdrop.py` | 0 | 36.74秒 |
| `python3 -B tools/check_region2_village_scope.py` | 0 | 0.11秒 |
| `python3 -B tools/check_region2_village_backdrops.py` | 0 | 35.95秒 |
| `python3 -B tools/check_region2_village_native.py` | 0 | 1.98秒 |
| `python3 tools/check_progress_docs.py` | 0 | 0.05秒 |
| `python3 tools/test_locked_check_reporting.py` | 0 | 0.19秒 |
| `python3 tools/check_acceptance_registration.py --proposal` | 0 | 0.12秒 |
| `python3 tools/run_locked_checks.py` | 0 | 126.43秒 |
| `timeout 120 godot --headless --path . --script res://tools/check_region2_village_backdrops.gd` | 0 | 3.08秒 |
| `python3 tools/check_frozen_files.py` | 0 | 0.05秒 |

村データは `VILLAGE_DATA_PASS: checks=244`、scope成功、nativeは既存保存画面25枚の独立画素照合成功。後続の進捗文書26件、検査結果判定23テスト、受入登録案11要件も成功。素材strictは1159件問題なし。保護26/26一致。

R-01〜R-08は全PASS。R-07はA01〜A14と最終PASS行を確認。R-08は25テスト・3046 assertion成功。村runtimeは2170検査成功。全生ログを別途監査し、修正後にSCRIPT ERROR・ERROR・WARNING・Parse Error・リーク警告・FAILマーカーなし。終了0だけを成功根拠にしていない。

### 自己点検・未確認事項・戻し方

- 最終提出は2ファイルのみ。正式headの他7728追跡ファイルは不変。既存追跡済みの検証生成物は提出しない。生成出力・原ログ・入力と再生成の台帳・manifest・不変性証明はcheckout外のLibrary引渡しZIPへ収録する。
- 3/4人・正順/逆順を含む既存受入と全ゲーム要件を保持。新しいGitHub CI全行列は親の正式保存後に確認する。今回のローカル結果で未実行のCIまで成功とは扱わない。
- GitHub書込み、push、PR作成、CI起動、merge、MSI、ローカルPC作業は未実施。main取込み保留は維持。親が公式接続で2ファイルを保存し、PR #49の新headでCIを確認する。
- 戻す場合は今回の2ファイル差分を逆適用する。registryを正式head93585b4のバイトへ戻すと、村再生成の全バイト不一致も再発する。原画・PNG・検査器を戻す必要はない。
