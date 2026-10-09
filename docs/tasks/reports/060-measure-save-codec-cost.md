# 060 装備保存codec専用計測報告

2026-10-10 JST。専用計測と根拠付き候補を提出する。本番最適化は未実装・効果未検証。F1解消、保存全体成功、S3受入とは判定しない。全取引6試行のうち3試行に既存検査の失敗があり、専用比較器は正しく `INCOMPLETE / exit 1` を返した。証拠整合性は成功している。

## 範囲と版

- 登録 `e37ddbaf4e84526c8e3f2816438dc9626875c00e`、固定基点 `6695d7b802137e9d6b7e468a1414c04d658a5380`。登録の親が基点であることを照合した。AGENTS.mdと060依頼書は全文確認し、「未採番」「正式時」等は冒頭と正式化補足を優先した。実作業を妨げる矛盾なし。
- 保存済みクラウドで実施。依頼のモデル指定は GPT-6 Astra／High。実行基盤内部のモデル名はこの証拠から独立検証できない。追加委譲なし。
- 採取開始版 `c126bc84870225b38842054f20e1784b023384d6`、最終集計コード `43fa030d9500bf1414673c5c857ea96ee5ec1f4f`。最新回帰の実checkoutは `2c6fef966576bb38fcaa0863b3982b1777c4fdff`。最後のコード変更は集計対象区間の再計算照合のみ。本番bytesは全版で基点と同一。
- 変更は専用コード5ファイル、060状態行、本報告、専用証拠だけ。scripts、既存driver/fixture/原証拠、保護26、CI、assets、native/addons、project.godot、decision-log、tasks READMEは不変。PR/main反映なし。新規CI接続なし。
- Linux 6.18.44 / AMD EPYC 9V45、可視CPU5、cgroup CPU 4相当・メモリ16GiB。Godot `4.7.2.stable.official.ed1daf0bf`、実行体SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。既存launch.pyに固定された公式ZIPとhashを用いて一時領域に取得。既存4.6.3は検証に使用していない。OS設定変更なし。原run_ci同様のprocess専用profileを使用。

## 再現と証拠

開始計画とCLIは [証拠README](../../verification/task060-save-codec-cost/README.md)。

```sh
python tools/check_equipment_save_codec_cost.py --godot /tmp/qa060/engine/Godot_v4.7.2-stable_linux.x86_64 --base-sha 6695d7b802137e9d6b7e468a1414c04d658a5380 --output <新しい専用QA先>
python tools/fixtures/equipment-save-codec-cost/compare_results.py --output docs/verification/task060-save-codec-cost --self-test
```

各runは指定された10ファイルのみ。results.jsonの `archive` にgzip/base64 TARとして原ログ・元JSON・入力bytes・型付きgdv・出力/backup/historyの原物を保存。各memberのサイズ/hashも保存。最上位inventoryは準備コマンド、各実行一覧、候補区間、059の全CI終了記録、最新回帰の原archiveを含む。実argv・cwd・実秒・exit・timeout・終了監督・stderr・生成差分・前後hashは各runから追跡できる。既存transaction子ログは元の結合出力仕様を維持し、最外層stdout/stderrを分離した。

原archiveの取り出しは `base64.b64decode(archive['data'])` をgzip展開してTARとして読む。SHA256をarchive/memberの記録と照合する。最新回帰の原archiveは `inventory.latest_regression.raw_archive`。16伝播負例は同archiveのpropagation-deltasとoff-07の元証拠から再構成できる。

採取後に、同じbatchログのケース別projectionとprofile複製を重複加算していた集計を修正した。projection bytesと元batch bytesの一致を確認し、元batchのみ一度集計する。原証拠・試行順・予算・実行本体は変更していない。採取中にPython集計ファイルの改訂があるためファイル全体不変とは主張しない。code-inventoryは採取関数6個とexec dispatchの開始版/最終版同一性、両版のblob/hashを記録し、inventory.reaggregationには旧集計hashと再集計理由を残した。旧集計は開始版コードと保存原物で再現可能。

## 入力と測り方

既存codec全154件/975条件、既存取引全172件/2178条件・97killをそのまま使用。全172件のseed・分類・期待条件・source形式・metadata有無はcases.json、実入力サイズ/hashと操作後原物は各inputs.json/results.jsonに列挙した。初期seed分布はtyped167、granted/trial-missing/trial-corrupt/trial-unclean/plain各1。初期sourceはplain172、gzip0、metadataあり171/なし1。異常化後のsourceは別原物であり、初期分布を全操作の入力分布と同一視しない。正常6seedだけで全体を代表させていない。

off/onを各条件3回、順番はoff/on → on/off → off/on。試行間並列なし。取引内部は既存Linux worker16・再開4・batch最大4。codec120秒、取引外180秒/内174秒/子30秒、import600秒を維持。子の残余予算による早いtimeoutも失敗として保持。全体172件を成功するまで回し直して選別していない。

4本番ファイルの固定hashを確認した専用一時checkoutだけに観測wrapperを生成。元body逆変換一致を確認。関数結果をそのまま返し、検査回数・条件・順序は維持。入口/出口とparse・展開・複製式の対応はinstrument_copy.pyと各generated-diff.patchにある。

呼出関係は概ね `decode_source → outer parse / packed検査 → inner展開・parse → SavedDocument.decode → 再展開・parse → 型復元 → validate`、`encode_candidate → candidate複製/describe → native_metadata_errors → document複製/describe → validate/encode → decode_source・全文比較`。native_metadata_errors内でもencode直下の対象だけを候補区間として切り出した。

時間はprocess内の単調microsecond。inclusiveは子を含み、exclusiveは**観測した直接子**のみ差し引く。非観測の再帰same_types/_collect等は親に含まれる。並行processの合算はCPU時間でも全体wallでもない。根span出力のJSON/log費用はspan外だがprocess wallに含まれる。kill/timeoutで完結せず出力されないspanは未測であって0ではない。

## 全試行値と同等性

秒は最外process wall。実秒の全桁はexit.json、元suite秒はresults.jsonに保存。

|順|条件|wall秒|exit|元検査|
|---|---|---:|---:|---|
|01|codec off|7.582622|0|154件/975条件 PASS|
|02|codec on|7.434148|0|154件/975条件 PASS|
|03|codec on|7.583414|0|154件/975条件 PASS|
|04|codec off|7.482269|0|154件/975条件 PASS|
|05|codec off|7.582425|0|154件/975条件 PASS|
|06|codec on|7.535348|0|154件/975条件 PASS|
|07|取引 off|86.659922|0|172件/2178条件 PASS|
|08|取引 on|87.554811|0|172件/2178条件 PASS|
|09|取引 on|92.354004|1|172件/2178条件、inspect-committed:specific_invariant|
|10|取引 off|88.222933|1|171件/2163条件、kill-candidate.store.after timeout、inspect-prepared:specific_invariant|
|11|取引 off|86.996085|0|172件/2178条件 PASS|
|12|取引 on|92.358508|1|172件/2178条件、inspect-committed:specific_invariant|

|条件|中央値秒|最小〜最大秒|
|---|---:|---|
|codec off|7.582425|7.482269〜7.582622|
|codec on|7.535348|7.434148〜7.583414|
|取引 off|86.996085|86.659922〜88.222933|
|取引 on|92.354004|87.554811〜92.358508|

codecは変動から計測負荷を分離できず、速くなったとは言えない。取引の中央値差はon側+5.357919秒（約6.16%）だが、失敗・未完了ケースを含むため純粋な計測費用でも改善見込みでもない。

codec3組は受理拒否/reason/errors、input・encoded bytes、型付きgdvが全件一致し、元検査のcontext/メモリ不変条件も成功。取引第1組は172件完全一致。第2組はoffにkill-candidate.store.after欠落、共通171件のうちinspect-prepared/committedの元条件が不一致。第3組は172件中inspect-committedの元条件が不一致。共通ケースの操作結果・reason/errors・source/converted/backup/history bytesは対応一致。正規化は実argvで確定した試行root、診断pid/user_dirだけで、errorsの相対target/reasonを捨てていない。全取引同等性は未成立として拒否した。

inspectの元条件はsourcehash・decode・phase・QA root全ファイル不変を含む。失敗ケースの他の8条件は成功しているが、元検査は直前全ファイルsnapshotを永続化しないため、この試行で変わったファイルの特定は未検証。059のQA log事例から同じ原因と断定しない。inspect条件の変更なし。子timeoutは元30秒枠の残余27.793117秒で発生し、原因の特定は未了。

## 観測区間と候補

同じ行の数値は各on反復1/2/3。単位はmicrosecondの**並行累積**。原spanから候補区間を再計算しinventoryと一致することを専用比較器で確認。

|区間|codec回数/回|codec累積us（3回）|全取引回数/回|全取引累積us（3回）|
|---|---:|---|---:|---|
|SavedDocumentの2回目展開|2|1226 / 1276 / 1237|0|0 / 0 / 0|
|SavedDocumentの2回目parse|2|36593 / 36491 / 36363|0|0 / 0 / 0|
|encode配下のmetadata再生成|11|3606 / 3673 / 3633|1351|612685 / 670128 / 661269|
|同じ照合内のdocument複製|11|450 / 453 / 480|1351|111737 / 78834 / 95105|
|元metadata照合全体（削除不可）|16|5200 / 5281 / 5265|1352|969160 / 980679 / 1062602|

全取引第1onの参考内訳：decode_source3583回/inclusive110.542秒/exclusive16.323秒、encode_candidate1358回/102.336秒/1.604秒、validate4936回/142.941秒/112.578秒、context_errors12590回/45.873秒/45.873秒、describe10337回/4.561秒。重なりを含むため合算してwall寄与率を作れない。約98%という過去のplan+verify比率をこの候補2箇所の寄与率へ転用しない。

正常・注入異常・中断前・再開は `scope-results.transaction_breakdown` で元configのoperation/kill_point/fail_pointにより分離。3回とも12672完結root group、割当不明0。第1onのdecode_sourceは正常54回/1.085秒、注入異常130回/2.787秒、中断前631回/28.326秒、再開2333回/68.627秒、special435回/9.718秒。fixture生成は別区分。batchに入っただけで再開とは分類していない。codec単体154件の正常/拒否別時間は個別分離しておらず未測（成否・原物の対照は全件実施）。

候補A：equipment_save_codec.decode_sourceのpacked経路で、同一呼出し内ですでに確認したinner bytes/解析値を再利用する。SavedDocument.decodeの入れ子_storage_format拒否を明示的に保ち、gzip構造・長さ/hash・UTF-8・重複キー検査と型復元を維持する。SavedDocument単独APIの拒否契約も維持。実測対象はcodecの約0.038秒累積/回で、今回の全取引には呼出0。F1解消を支持する実測ではない。

候補B：encode_candidateで同じcandidate複製から生成したmetadataを、同一呼出し内の元metadata照合へ渡す。元metadataの未知キー・path・型の照合とreason/errorsをそのまま残す。不正metadataを生成し直して隠さない。実測した再生成+複製は全取引で0.724422 / 0.748962 / 0.756374秒の並行累積。元metadata照合全体を削除する案ではなく、wall短縮量は未証明。

どちらも実装未試行。初回plan、prepare、prepare末recover、commit入口、rename直前、rename後の6境界で現在データを再読取・再検査する。境界間cache、検査削減、encode後decode/全文比較や実tmp/converted照合の削除は候補にしない。validate等の大きい親区間をさらに細分する場合は別の具体範囲として発注する。

候補ごとの採否比較は、同一環境で旧/候補を同じ全入力・反復順・worker・予算で実施し、受理/拒否・reason_code/errors（target含む）、出力bytes/hash、値/型/配列順、入力/context/session/metrics不変を対照する。Aはgzip不正構造/長/hash/UTF-8/重複キー/入れ子とSavedDocument単独契約、Bは未知metadata/path/型・欠落・重複の拒否を重点照合する。両案ともcodec154、取引172/2178/97kill、16伝播、6境界、固定版/最新回帰を保持する。現段階で採用承認を求めていない。

## 検証結果と未達

固定基点のcodec全6回成功、取引3成功/3失敗。証拠整合性成功、codec全3対照成功、取引全対照は未成立。専用比較器exit1は失敗を隠さないための結果。欠落input、native値、reason、取引case欠落、error target、memory条件、出力bytes、archive改変の8負例を拒否。さらに実Git treeの担当外変更6負例（本番、旧証拠、decision-log、workflow、未列挙code、依頼本文）を別process exit1で拒否した。

最新回帰は専用checkoutでimport（29.962秒）、R-01〜R-08、素材strict、codec154/975、既存16伝播、前後保護26/26を成功。R項目はexitだけでなく元judge_outputでtests_ran=true、parser_failed=false、PASSを確認した。16伝播はcontrol0と15負例1の期待exitが全一致。原コマンド/出力/判定はinventory.latest_regressionに保存。全取引の最新版を別に6回再実行したとは主張しない。本番/原検査の基点からの不変と、上記固定計測・最新回帰を分けて扱う。

059元提出の全CIは独立取得し51完了・47成功/4失敗を確認、inventory.baseline_ciへ保存。最終提出SHAの既存全CIはpush後に全終了を確認し、SHA・各結果・失敗stepとclean/未pushを最終応答で確定する（この報告自身のcommit SHAを自己包含できないため）。旧固定版の失敗を最新回帰成功で置き換えない。専用060検査はCI未接続。

未検証はWindows専用060計測、実ENOSPC/nested別volume環境、codec単体の成否別時間、未完結span、局所改善効果、inspect/子timeoutの厳密原因。F4準備・既存条件変更・通常UI接続は行っていない。

残判断は、(1) 本計測を未達付き調査報告として受け取るか、(2) 候補A/Bの別発注またはvalidate細分の別調査が必要か、(3) 既存inspect/timeoutとF4の未達をどの別依頼で扱うか、の3点。受入はルッカが担当する。
