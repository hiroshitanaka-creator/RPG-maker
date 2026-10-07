# 049 保存codec・新版全状態検証（S2）報告

## 開始点・契約・依存

登録 `5f5aab4fbe48e77f7e217b71672a043be2839d34` から指定branch `codex/task-049-equipment-save-codec` を作成。開始時の未コミット変更0、担当外未push0。親確認済みmain `3273fa4d788fb8d4e0e2d6ef209a70f029d257e2` は変更・mergeしていない。追加委譲なし。

AGENTS、asset-spec、企画/装備仕様、040計画全文、041/042の実装/証拠、043〜046の専用CI/報告と現行保存実装を確認。catalogでverification-before-completionを使用。checkoutおよびworkspaceに関連 `.agents/skills` は存在しなかった。

S1 `validate_new(document,source,hash,context)` は元保存から移行直後の完全一致のみを保証するAPIとして不変。S2は原bytesの復元、新版の全状態検証、上限だけの候補準備、型保持の再符号化を担当する。通常新版は元保存不要、移行差分保証だけは元保存とraw hashが必要。共通検証は実GameSession/IntegratedProgression、所有検証は既存EquipmentRules/View、型/包みは既存SavedValueTypes/SavedDocumentを使用する。固定期待は手書きファイルと以前の原本からの入力であり、実装出力から生成しない。

## 変更ファイルと関数契約

| ファイル | 内容 |
| --- | --- |
| `scripts/game/equipment_save_codec.gd` (+uid) | `decode_source(bytes,context)` はUTF-8、重複JSONキー、gzip5field/size/hash、型metadata、旧新形式、位置・補助情報を検証し、原bytes/原SHA/document/観測を返す。`encode_candidate(document,context)` は既存metadataも照合後に再生成し、同じdecoderへ戻して全値・型・配列順を比較。失敗はreasonとpath付きerrorsのみで成功document/bytesを返さない |
| `scripts/game/equipment_document_validation.gd` (+uid) | `validate(document,context)` は進行後新版のparty/reserve、進行・所持品・修練・能力・上限・所有/袋・監査/支給・metrics/trialIDを検証。`prepare_candidate` はコピー上で全人物max再計算と現在値minだけ、別戻り値caps_changesで差分を示す。`compare_migration` はS1再計画→S2準備→全差分照合 |
| `scripts/combat/battle_catalog.gd`, `data/equipment_abilities.json` | 採用済みtwo_handedのpassive/selfを実catalogへ検証付き登録。旧abilitiesは保持し、内部 `equipment_context_abilities()` だけが合成辞書を渡す。壊れた定義/重複/旧定義上書きは拒否。通常修練報酬/戦闘へ未接続、両手持ち倍率を決めない |
| `scripts/game/game_session.gd` | `validate_state_common`, `validate_actor_common` は明示contextのみ新装備検証を選ぶ。`equipment_stats(actor,document)` は引数と実定義だけを使い、現在_stateを参照しない。通常 `_valid_state`/import/save/loadは旧契約を維持 |
| `scripts/game/integrated_progression.gd` | 人物/世界の非装備共通検証を抽出。旧入口は元の武器/armory検証も継続 |
| `tools/check_equipment_save_codec.gd` (+uid) | 新規112ケース・723条件。state/metrics/history/catalogとnative入力不変、失敗の成功値不在を全ケース検査 |
| `tools/fixtures/equipment-save-codec/` | 旧固定raw、手書き派生、独立固定期待（全ID・reason・4人stats）、原検査/証拠照合/実exit伝播wrapper |
| `.github/workflows/equipment-codec.yml` | 明示承認済み新規専用CI、fixed049/latestの2job、各15分、import600秒/原検査120秒。既存workflow不変 |
| `docs/verification/equipment-save-codec/` | 当時/完成原証拠、全ケース入出力・log・hash・失敗伝播、R/旧比較、固定↔最新対応 |
| 本報告、自身task状態、decision-log末尾 | 今回分だけ追記/状態更新 |

未知キーを削除して受理しない。欠けているmetrics/trialID/first_regionを永続documentに補わない。型なしJSONの整数正規化は観測として型あり復元と区別する。位置補正はコピー上で前後差分を示して拒否し、原入力を動かさない。9007199254740993のJSON精度損失を拒否し、型なしfallbackを使わない。

監査の一般検証は台帳内部の完全性/相互参照/会計を保証する。元保存との真正な差分の保証には `compare_migration` を使う。この2つを混同しない。両APIともファイル、archive、通常load/save、実ユーザー保存、取引ディレクトリへ依存しない。

## 固定コードと原証拠

完成コードSHA: `99e9d03d4e095b4627b510efd4806f82276617c9`。初回コード `93031f9154c82afde4c0d27a8ac9b4eed8221536` の106ケース/689条件と伝播13件の原証拠は `attempt-93031f9-original.tar.gz` に不変保管。最終点検でencodeの既存metadataを無条件再生成する欠点を修正し、正1/負5を追加した。完成側は112/723。

開発初回の包みstorageformat型不正が旧SavedDocumentのfloat/String比較エラーを誘発した記録も `development-first-failure.log` に保管。新codec内の事前検査で修正し、旧SavedDocumentは変更していない。NaN入力の不変比較はNaN同士の値等価ではなくnative bytesを照合する。失敗を無視した成功集計はしていない。

完成証拠は `fixed049-original.tar.gz` に全実物を保存し、読取り用に `fixed049/{execution,codec,sha256}.json` と原logを併置する。dict入力のinput.bin/document.gdvはGodot `var_to_bytes` の型付きnative表現、decode入力とencoded.binは実JSON/gzip bytes。archive内の全memberのSHA256はmanifestで照合する。期待/実結果/全IDは `cases.md` とcodec.jsonに記録。

実体はGodot `4.7.2.stable.official.ed1daf0bf`。公式ZIP hash `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、展開engine hash `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。全実行は隔離XDGと別checkout（素材検査のみroot読取り）。標準環境の別版Godotは合否に使用していない。

## 実行コマンド・結果

| コマンド（Godotは上記実体） | 結果/証拠 |
| --- | --- |
| `python tools/fixtures/equipment-save-codec/run_ci.py --profile fixed049 --source-sha 99e9d03d4e095b4627b510efd4806f82276617c9 --godot /tmp/task049/bin/godot --output /tmp/task049/fixed-final/results` | 完成checkoutの原検査112ケース/723条件、実exit伝播13件（正常1、異常12）。各argv・予算・時間・exit・hashはexecution.json |
| `timeout 240 godot --headless --path . --script res://tools/check_equipment_rules.gd` | exit0、5394条件/400切替 + 93追加条件、失敗0、regression/core.log |
| `timeout 120 godot --headless --path . --script res://tools/check_equipment_save_migration.gd` | exit0、61ケース/2828検査、失敗0、regression/s1.log |
| `RPG_LEGACY_EQ_OUTPUT=/tmp/task049/legacy-latest.json timeout 120 godot --headless --path . --script res://tools/fixtures/equipment-save/legacy_equivalence.gd` | exit0、固定142検証/10更新。以前のlegacy-before全文と全bytes一致。展開SHA `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea`。regression/legacy-comparison.jsonと実物gzip |
| `python tools/run_locked_checks.py` | exit0、R-01〜08すべてPASS。R-08は17tests/2302assertions、pending/failed0、regression/scope-lock.jsonとR全8生log |
| `python tools/check_frozen_files.py` | before/after exit0、保護26一致、完成executionとfrozen log |
| `python tools/validate_assets.py --strict` | exit0、画像1154・音声15・palette3・font2、問題0 |
| `git diff --check` / Python compile | 成功 |

旧比較/R/装備/S1の上記local実行は93031f9 checkout。この後の99e9d03はcodecと新検査/固定期待のみに変更し、上記旧検査と呼出し先は同じGit blobである。最終SHAの既存CIではこれらも再実行する。完成固定wrapperは99e9d03を実際にcheckoutして実行する。

保護と旧契約の原本hashは `regression/preserved-source.json`。S1 validation/migration/View、SavedDocument/ValueTypes、旧装備/S1検査、旧比較、R wrapper/保護検査に変更なし。旧142/10期待全文、test/、.scope-lock/、addons/、素材、040計画、他task/報告、過去証拠、既存3workflowは不変。scope diffはregression/scope-code.diff.txt。生成された担当外uidは作業tree外へ移して非commit、R自動報告は別checkoutから今回証拠へコピーし既存報告を上書きしていない。

## M09〜M12と固定/最新CI対応

全ケースID/固定期待/実結果/操作/件数は `docs/verification/equipment-save-codec/cases.md`。M09は旧/新plain・gzip10000履歴・typed配列/空/float、M10は全人物stats・reserve・進行後新版・上限上下/死亡維持・未知keys/位置/非装備進行、M11は形式/所有/袋/監査/支給/catalog、M12は5field・metadata・精度/非有限/builtin/typed辞書・UTF-8/JSON・metrics/trialIDを検査する。修練済みtwo_handed受理/未修練拒否も固定。入力不変等の横断条件を省略しない。

| job | checkout/検査原本 | 継続する条件 |
| --- | --- | --- |
| `equipment-codec (fixed049)` | 完全SHA99e9d03の本番・原検査・fixture・wrapper | 当時112/723、通常新入口拒否/未接続、旧能力辞書維持を含む全条件 |
| `equipment-codec (latest)` | push github.sha / PR head完全SHAの本番・原検査・fixture・wrapper | 原bytes/型/順序/純粋性/進行後新版/非回復/S1差分/全112条件を現時点でも継続 |
| 既存Equipment and Save CI（14job） | 従来036/038/041の固定原本および最新 | 全既存条件、旧3対象の原142/10全文比較・旧失敗伝播を維持 |
| 既存CI（3job）・006回帰（17job） | 従来設定のまま | R・保護・asset・各固定/最新描画回帰を維持 |

新専用wrapperの正常1/異常12は実Python子プロセスのexitを固定期待と比較する。FAIL/警告/ケース欠落・重複/actual偽造/原入力欠落・hash不一致/成功doc・encoded欠落/summary・PASS欠落・件数偽装を拒否。原検査失敗時もfinallyで保護照合し、原入力・logを残す。workflowもalwaysで保護/証拠upload（欠落error）。固定成功だけで最新版成功を代用しない。

最終コミットはコード固定後の今回証拠/報告/専用CIだけを追加する。本番・新旧原検査・fixtureのcode SHA以降不変を最終確認する。同一最終SHAの全36job（既存34+新2）の結果、完全最終SHA、実CIリンクは自己参照を避け最終応答とdraft PRへ補う。未完走/失敗jobがある間は完了扱いしない。初回コードのCIと最終SHAを混同しない。

## 未実装・未実行・判断事項

S3のI/O取引/実保存移行、S4通常runtime/戦闘/修練報酬接続、S5UI/公開は依頼範囲外として未実装・未実行。ユーザー保存へのアクセス、取引ディレクトリ作成、通常保存形式切替なし。未決の両手持ち倍率等のゲーム数値・商品/名称/効果を追加決定していない。判断依頼なし。提出はdraft PR #32、mergeなし。
