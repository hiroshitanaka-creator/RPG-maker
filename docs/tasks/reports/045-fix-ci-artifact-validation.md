# 045 CI比較の原検査記録検証の修正

## 開始状態・変更範囲・独立固定期待

開始／登録SHA `5899ee42c60495135f1187561bef248d2d9a92bd`、branch `codex/task-045-fix-ci-artifact-validation`。044基点 `9010b9b18e468e5e03c47ac285d4d1ad80045660` の継承を確認。開始時の未コミット／未pushは0。開始時checkoutのworkはmainへ書かず、指定remote branchをfetchして専用branchへ切り替えた。

変更は `tools/run_equipment_ci.py`、新 `.github/workflows/equipment-save.yml` の固定原本fetch、`docs/verification/equipment-ci-fix/`、045自身の状態行／本報告、decision-logの今回追記だけ。追加委譲・main書込み／マージ・PR30変更・別PR作成・強制pushなし。

AGENTS、素材規約、職業・魔物化企画／体験仕様、素材台帳、043/044依頼・報告全文、044再現付録、wrapper／新workflow全文、原旧入口検査と固定証拠を読んだ。checkout `.agents/skills` はなく、`/workspace/.agents` は空。catalogの systematic-debugging、test-driven-development、verification-before-completion を適用。開始時の読取りhash／計画は `start.json` に記録。

実コードを **`858164c25224ff8467b75a3d9044f00b6c0ccb05`** に固定した。以降のローカル原検査とCI artifactはこの完全SHAの証拠である。

独立期待は対象最新版から生成しない。fixtureは固定041 `8d3c1848d09b588fa41bcf6345d3aab6e12a5347` の5原本blob。旧出力は証拠保存コミット `ddf2153e0f47513eb7906ddd68ab03b645edacd7` の `docs/verification/equipment-save-migration/legacy-before.json.gz` を展開した、041当時の旧基点実出力。展開後SHA256は `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea`。固定142検証ID／10更新ID、全必須フィールド／型／値を照合する。元の原検査器／期待／証拠は変更していない。

## F1対応表

| 044 F1の反例／不足 | 修正 | 修正前 → 修正後の実exit |
| --- | --- | --- |
| versionだけ5記録 | version／前保護／import／legacy／後保護の全5種を順・一意性・argv全文・log名で確認 | 0 → 1 |
| 原コマンドをtrueへ置換 | 同一公式Godot実体・同一checkout・原scriptをargvで確認。別実体への見かけだけの置換も拒否 | 0 → 1 |
| PASSなしlegacy.log、hash更新済み | 公式版の実行冒頭と原PASS行1件・142/10/失敗0を確認 | 0 → 1 |
| 3版共通の空fixture辞書 | 5件のキー／hash全文を固定041 blobへ照合。欠落・改変も拒否 | 0 → 1 |
| 3版共通のboolだけ偽成功JSON | 元の成否／副作用／往復チェックを保持し、固定旧出力へ再帰的にキー・順・型・値を照合 | 0 → 1 |
| 記録の版／予算／結果／log不足 | 各cwd・source hash・profile・wrapper hash・公式engine hash、30/30/600/120/30秒、有限実時間、int exit0、timeout=false、警告なし、manifest/log hashを照合 | 全追加不正ケースexit1 |
| JSONのID／valid／state／型／metrics／履歴不足 | 固定ID・必須キー・全入力／純粋upgrade／前後state・input/pure/after_types・前後metrics/events履歴・upgraded/second等も照合。int/float/boolを区別 | 全追加不正ケースexit1 |

versionは公式版文字列、前後保護は対象完全SHAの凍結台帳件数に対応する全一致行、importは公式版冒頭とeditor読込み終了を確認する。ログにPASSという語があるだけでは受理しない。原legacyの全結果が固定旧期待と一致した後も、3版の生JSONを基点へbyte比較する。

JSONの重複キー拒否を保持し、非有限数も拒否する。未知／壊れた記録型・欠落要素は実exit1とexecution.status=FAILへ伝播する。原検査の終了値／警告検査／各個別予算は維持。

## 修正前後の実証・失敗伝播

`docs/verification/equipment-ci-fix/probes.py` は保存済み043コードSHA `f8ae80b34589f2c0f2c3b5ef3b6d9ddd2e86c94a` の旧3artifact ZIPを展開し、各プローブの別コピーにだけ変異を適用する。044と同じ12ケースすべてを含む。元ZIPは不変。log／JSON変異ではhashも更新して、単なる破損hashの拒否だけを成功としない。値／型／fixture変異は3版とも同じ変異にし、相互一致だけによる偽成功を反証する。

```sh
# 登録SHAのwrapperで実行：期待した拒否が不足しexit1
python docs/verification/equipment-ci-fix/probes.py \
  --output /tmp/task045-before-probes-full --require-rejection

# コードSHAのwrapperで同じプローブを実行：全期待一致しexit0
python docs/verification/equipment-ci-fix/probes.py \
  --output /tmp/task045-code-probes --require-rejection

python tools/run_equipment_ci.py --suite self-test \
  --latest-sha 858164c25224ff8467b75a3d9044f00b6c0ccb05 \
  --output /tmp/task045-code/equipment-self-test-latest
```

修正前：42プローブ中、正常対照1件exit0、不正41件のうち32件をexit0で誤受理、9件だけexit1。044のF1反例5件はすべて誤受理。修正後：正常対照1件exit0、不正41件すべて実exit1。

元35失敗伝播fixtureは修正前に別実行して成功。修正後も全35のID・順序・拒否変異・終了期待／実exitを維持し、30拒否／5対照を確認した。旧正常対照のboolだけの入力はF1修正後には不正になるため、正常対照には固定旧原本の省略フィールドと正しいIDを補った。旧missing/failure/duplicate/roundtripの変異と拒否は保持し、元の不完全JSON自体は追加 `comparison_fake_success_json` で拒否を検証する。省略／期待exit変更による成功はない。

追加比較42fixtureをwrapperのself-testへ収録。**全77件＝対照6件exit0＋拒否71件実exit1**。各子の生log／hash／実exitと全入力を保存。合成比較fixtureを実Godot実行の証拠とは扱わない。実artifactの正常対照・反例は別の独立プローブで確認した。

## コードSHAの原検査

共通コマンドは次のとおり。各wrapperが完全SHAのdetached checkout・新出力・XDG隔離を用意し、公式版確認、前保護、必要なimport、原検査、後保護を実行した。

```sh
python tools/run_equipment_ci.py --suite SUITE --profile PROFILE \
  --latest-sha 858164c25224ff8467b75a3d9044f00b6c0ccb05 \
  --godot /tmp/task045-bin/godot \
  --output /tmp/task045-code/equipment-SUITE-PROFILE

python tools/run_equipment_ci.py --suite compare \
  --latest-sha 858164c25224ff8467b75a3d9044f00b6c0ccb05 \
  --inputs /tmp/task045-code --output /tmp/task045-code/comparison
```

| 原検査／profile | ローカル結果 |
| --- | --- |
| legacy / baseline, 041, latest | 全3版exit0、142検証／10更新、失敗0、固定旧出力と全文一致 |
| compare | exit0、3版byte一致、全出力SHA256 `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea` |
| core / latest | exit0、5394＋93＝5487条件／400切替、失敗0 |
| invalid / latest | exit0、202/202ケース／1576条件、失敗0 |
| migration / latest | exit0、61ケース／2828条件、63観測、失敗0 |
| self-test / latest | exit0、全77件の期待終了値一致 |

公式ZIP SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、実体 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e` を実物照合。全import600秒内、core240秒内、S1／旧入口120秒内。元異常検査の各子30秒を保持。各実コマンド／秒数／対象SHA／終了値はlocal-codeのexecutionに保存した。

別checkout `/tmp/task045-locked` で公式Godotの `godot --headless --editor --import --quit` を先に実行し、`python tools/run_locked_checks.py` はR-01〜R-08全8件PASS、exit0、tests_ran=true、parser_failed/timed_out=false。生ログとscope-lock-currentをlocked-codeへ可逆保存。証拠集約の初回copyは元ログの保存先を誤認して失敗したため、実際の `.tools/verification/current-*` から回収した。検査本体のexit0と証拠集約の失敗を区別している。

`python tools/check_frozen_files.py` は26/26一致、`python tools/validate_assets.py --strict` は画像1154／音15／字体2／パレット3、問題0。`python -m py_compile tools/run_equipment_ci.py`、`git diff --check` 成功。既存3workflow・本番・data・素材・test／.scope-lock／addons・既存原検査／旧証拠は全blob不変。decision-log旧本文prefix一致、削除／scope外変更0。

## CI構成・原artifact・提出

新14job＝core4＋invalid3＋migration2＋legacy3＋comparison1＋failure-propagation1、既存20jobを維持。push/PR対象SHA指定・contents:read・全job15分・個別上限・fail-fast:false・失敗時保護／artifact保存は不変。今回の新workflow変更はcomparison／failure-propagationで固定基点・041・当時証拠を完全SHAでread-only fetchする2stepだけ。

コードSHAの新専用CI run `37622919751` は全14job終了・success。14原ZIPを取得し、GitHub digest、全2028 memberのCRC／hash、executionの固定／最新SHA、wrapper hash、原コマンド／予算／終了値／警告、正常4・異常3・S1 2・旧3の全原結果、77失敗伝播結果を再検証した。比較artifactもローカルで再実行して完全一致した。

```sh
python docs/verification/equipment-ci-fix/verify_evidence.py \
  --sha 858164c25224ff8467b75a3d9044f00b6c0ccb05 \
  --inputs docs/verification/equipment-ci-fix/ci-code \
  --output /tmp/task045-ci-code-reverified
```

`ci-code/artifacts.json` に全ID・run／SHA・digest、`ci-code/verification.json` に全member数／対象SHA／実原コマンド／秒数を記録。原ZIPは `.zip.gz` としてbyteを可逆保存。`before-*.tar.gz`／`code-probes.tar.gz`／`local-code.tar.gz`／`locked-code.tar.gz` は入力・生JSON・logを省略せず保存した。展開後hashと保存後hashは `evidence-sha256.json`。

`ci-code/results.json` は提出文書作成時点の中間観測で、新14＋既存19job成功、通常CIの1jobが実行中。全34成功とは扱わない。本報告・状態行・新証拠を含む最終提出SHAは追加pushで全34jobを終了まで確認し、その完全SHA／3run／全job結果を最終応答に記載する。自己参照で本文を書き換え続けず、最終応答を最終SHA結果の正本にする。

未実装／保証外：S2〜S5、新版完全codec／通常保存・復旧I/O／実ユーザー保存／通常戦闘UI接続、手動旧本編workflow、042独立付録。今回の045修正範囲に未達はない。新CIに未実装機能の空jobを作らず、固定原assertの意味／件数を維持した。判断事項なし。
