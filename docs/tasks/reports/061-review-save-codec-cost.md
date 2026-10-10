# 061 保存codec計測の独立レビュー報告

2026-10-10 UTC。判定：**部分確認**。060のローカル原証拠、再集計、失敗を保持する結論は独立照合できた。060提出の全CIおよび061最終提出のCIはアクセス拒否により直接確認できない。保存全体・F1・S3を受入とはしない。本番最適化へ直ちに進む実測根拠はない。

変更は061依頼書の状態行と本報告だけ。mainの取り込み、PR作成、他タスクへの委譲、環境設定変更、本番・検査・CI・保護・原証拠・予算の変更は行っていない。モデル指定はGPT-6 Astra／Mediumとして受領したが、実行基盤のモデル名・effortを独立取得する手段はなく、内部実行値の確認済みとはしない。

## 固定対象と資料

|用途|完全SHA|
|---|---|
|061登録・作業開始|ef261f5397412dde35e11fec9bd8884c7d4cc8f8|
|060登録|e37ddbaf4e84526c8e3f2816438dc9626875c00e|
|060固定基点・059提出|6695d7b802137e9d6b7e468a1414c04d658a5380|
|060採取開始|c126bc84870225b38842054f20e1784b023384d6|
|060最終専用コード|5d941bfe23715be0c2300b0263fcbea7ae7059fe|
|060の最新回帰実checkout|2c6fef966576bb38fcaa0863b3982b1777c4fdff|
|今回のレビュー対象・別checkout|4ec85645d883897a5c1c18e2b53f60a7818710d5|
|059完成コード|41a34ea33fe184274e6722c88cdbca2a7ffd3708|

対象側AGENTS.md、061全文、060依頼・報告全文、tasks README、059報告の固定55/41・実行ac768de/8f03・旧351の世代境界、専用5コード、cases.jsonと原期待集合・原証拠を確認した。asset-spec、職業・魔物化企画、素材台帳も参照した。checkoutに`.agents/skills`は存在しなかった。060が保存全体未受入でも独立レビューを進める明示指示を適用し、READMEの一般的な前提確認規則を理由にレビューを止めていない。

最初の環境は`work`の74c656bac5494ce55176853531926f7cce38b261、clean、upstreamなしだった。初回fetchを約80秒で自主中断したことは取得拒否の証拠ではない。再試行を明示許可された後、同じ`git fetch origin codex/task-061-review-save-codec-cost`を一度実行し、約2分半でexit0、FETCH_HEAD=061登録SHAを確認。途中の一時pack増加も確認した。通信経路・認証・proxy設定は変えていない。

## 範囲・版・生成差分

060登録→提出の差分132ファイルは専用コード5、本報告の対象である060文書2、専用証拠125の許可集合内で、削除・担当外差分0。060依頼書は状態行を除いた全文bytesが登録時と一致した。したがって本番、既存検査、旧原証拠、CI、保護、assets、native/addons、project.godot、decision-log、tasks READMEは不変。採取開始・最終コード・回帰実checkout・提出の各版についても、固定基点からscripts/native/addons/test/.scope-lock/.github/assets/project.godotに差分がないことを照合した。

`code-inventory.json`の開始5件・解析5件を`git show SHA:path`のSHA-256と`git rev-parse SHA:path`のblob IDで独立再計算し、10/10一致。採取関数run/command/environment/profile/archive/inputsのASTから原文を切り出して6/6の同一性とhashを確認し、exec-json分岐のASTも一致した。Pythonファイル全体やexec dispatch全体が不変とは扱っていない。fixtureのfixed_sources全11件も一致。

4本番ファイルを固定基点のblobから読み、生成器の逆変換条件を通して計測差分を再生成した。全on6試行のpatchと生成後hashに一致、off6試行のpatchは空。patch SHA-256は`1840159c390f15920d2ed76b0f96feda392896d601a348f832b4eebb622d0e4d`。wrapperは元関数を一度呼んで結果を返し、元検査の条件式・returnを残している。本番transactionは不変で、初回plan、prepare、prepare末recover、commit入口、rename直前、rename後の6境界を削っていない。UTF-8、重複キー、gzip構造/長/hash、入れ子、metadataの未知キー/path/型、encode後decode/全文比較、実tmp/converted照合を最適化名目で削除していない。

## 原archiveと全12試行

証拠の入口は[060証拠README](../../verification/task060-save-codec-cost/README.md)、[inventory](../../verification/task060-save-codec-cost/inventory.json)、各runのresults.json。060固定checkoutから読み取り、一時コピーだけに検証出力を書いた。

専用比較器のunpack/summarize/candidate_costsを使わない独立Python処理でも、base64厳格decode、gzip/TAR、member名の重複・絶対パス・親参照・非regularを検査し、archive全bytes/hash、member全bytes/hashと集合を照合した。12試行44,785member、準備2件と最新回帰1件を含め15archive/45,141memberすべて一致。各run10ファイル、hashes.jsonの9件、inventoryのhashes索引、原execution/summary/stdout/stderrと外側JSON、入力索引のsource/input原bytesも一致した。

|run（接頭辞run-linux-）|member数|圧縮bytes|archive SHA-256|
|---|---:|---:|---|
|off-01|191|184585|`ccff4c9069b2b3318644f6b0b6590bdb7af4a76459a144f2975c3684fd0f7f11`|
|on-02|191|219222|`b04a015802f7be2a4a8fb7d77638cc0933f7e0e24b19e6da8344910961ce93dd`|
|on-03|191|219114|`da83f9102dadad9b186e03a1f6af6ff997312e4a41753affaa57ff8d58110662`|
|off-04|191|184586|`cc621fb6e499aca188073764596b0b008b54e2ed48c04e3f1ce489a5f74077c6`|
|off-05|191|184578|`b36386421c5f3060a3b1d9b10776943cd1b30f3f767b4b0a5d889c768c304981`|
|on-06|191|219280|`62e7549318ae26bcec392086b7cf4f7b57c273b9116cf108fe058d5e39c9553b`|
|off-07|7272|2186533|`5c5e509c247148701c74657dd5140cd3ece23c4e78a52f0fd485cd42ad77669f`|
|on-08|7274|8629925|`39720ebd0e62b7c0eeb8767fb8ac84635e3cea4183b0c8d95ca3a088631f8b96`|
|on-09|7287|8647462|`2d47748dd206e49a83fe60f969ce1ce59aeeee086c2f733ad61deebcfa125936`|
|off-10|7257|2180981|`a912298adf550d771f43546b2fa3a9923cf53e7750fa4c533d049c3f6ef56599`|
|off-11|7274|2191850|`a0251879ed2c5fe6f71ab5de93c24f143b6a7d8a84596670cdd2019f1a51379a`|
|on-12|7275|8659635|`46cd5c4c499bc01d95511c8204d18c9359384357665183b80b524b290823e332`|

以下は既存原試行の再照合値であり、061で新しく性能試行を実行した値ではない。wallは最外processの実秒。

|順|条件|wall秒|exit|原判定|
|---|---|---:|---:|---|
|01|codec off|7.582622|0|154/975 PASS|
|02|codec on|7.434148|0|154/975 PASS|
|03|codec on|7.583414|0|154/975 PASS|
|04|codec off|7.482269|0|154/975 PASS|
|05|codec off|7.582425|0|154/975 PASS|
|06|codec on|7.535348|0|154/975 PASS|
|07|取引 off|86.659922|0|172/2178 PASS|
|08|取引 on|87.554811|0|172/2178 PASS|
|09|取引 on|92.354004|1|172/2178 FAIL（inspect）|
|10|取引 off|88.222933|1|171/2163 FAIL（子timeout、inspect）|
|11|取引 off|86.996085|0|172/2178 PASS|
|12|取引 on|92.358508|1|172/2178 FAIL（inspect）|

原期待集合とcases.jsonは172件/2178条件/97kill、各caseのkind/point/checks等が一致。seedはtyped167と他5種各1、初期sourceはplain172/gzip0、metadataあり171/なし1。元configを各原ログの実argv・root・operation・kill_point・fail_pointと対応させた。異常化後のsourceを初期sourceと混同していない。

原accepted/ended単調時刻で12試行の重なりなし。codec・取引それぞれoff/on、on/off、off/onの3組で、Linux worker16・再開4・batch4、codec120秒、取引外180/内174/子30秒、import600秒を保持。失敗後の選別再計測はしていない。

|条件|中央値秒|最小～最大秒|
|---|---:|---|
|codec-off|7.582425|7.482269～7.582622|
|codec-on|7.535348|7.434148～7.583414|
|transaction-off|86.996085|86.659922～88.222933|
|transaction-on|92.354004|87.554811～92.358508|

codecの差から負荷を分離できない。取引onの中央値差+5.357919秒（約6.16%）は失敗・未完了を含み、純粋な計測費用や短縮見込みではない。30秒枠内の残余27.793117秒でoff-10の子timeoutが発生しており、全体wallが174秒より短いことだけで当該試行を成功にはできない。

独立した別の意味比較でもcodec3組は各184のevidence原物（入力、出力、型付きgdv、codec.json）が全bytes一致。取引は実argvの試行rootと診断pid/user_dirだけを対応させ、actual、expected、全commandのresult/exit/timed_out/kill_point、checksを比較した。共通caseのsource/converted/source.bin/history.binの集合とbytesは全一致した。差異は次のまま残り、error target/reasonやmemory条件の値は落としていない。

- 第1組：172件、差異なし。
- 第2組：共通171件。offのkill-candidate.store.after欠落、inspect-preparedとinspect-committedのspecific_invariant差異。
- 第3組：172件、inspect-committedのspecific_invariant差異。

## 集計・候補・後処理の独立再現

元batch-recordから対応するcanonical logを求め、投影の原bytes一致を確認してから除外した。取引off-07/on-08/on-09/off-10/off-11/on-12の投影は222/222/222/221/222/222件。一意な(pid, sequence)、親index、子区間の包含、非負のinclusive/exclusiveを独立に検査し、labels/parents/roots/group_countを保存measurementsと照合した。onのcodecは各208、取引は各12,672完結root group。取引の元configへの割当不明0、正常/異常/中断前/再開/special/fixtureの内訳も保存集計と一致した。

profile内のCOST060複製行も調査した。codecは全行がcanonical側に存在した。取引on-08/on-09のwriter-busyのgodot.logに各1行、JSONとして不正な混在行があり、profile側全行がそのまま原ログと一致するとは言えない。それ以外のprofile採取行はcanonical側に存在する。採用したcanonicalの原JSONは全て解析可能で、上記12,672群が一致した。profileの不正行を新しい有効spanとして補完していない。

採取開始c126の旧summarizeも同じ12archiveから再実行し、inventory.reaggregationのoriginal_measurements_sha256が12/12一致。修正後の結果だけを信じた再計算ではない。

|候補区間|codec回数/回|codec累積us（反復1/2/3）|取引回数/回|取引累積us（反復1/2/3）|
|---|---:|---|---:|---|
|A・SavedDocument再展開|2|1226 / 1276 / 1237|0|0 / 0 / 0|
|A・SavedDocument再parse|2|36593 / 36491 / 36363|0|0 / 0 / 0|
|B・encode配下metadata再生成|11|3606 / 3673 / 3633|1351|612685 / 670128 / 661269|
|B・同照合内document複製|11|450 / 453 / 480|1351|111737 / 78834 / 95105|
|元metadata照合全体（削除不可）|16|5200 / 5281 / 5265|1352|969160 / 980679 / 1062602|

候補区間は原spanのlabelと親・祖父関係から別実装で抽出し、inventoryと全一致。Bの合計は0.724422/0.748962/0.756374秒。これらは完結したprocess内wall区間の並行累積で、CPU時間でも試行wall短縮量でもない。inclusive同士は入れ子が重なる。exclusiveも観測した直接子だけを引いた値で、未観測の処理や計測器の費用が残る。根spanのJSON/log出力は根区間の外だがwallには含まれる。kill/timeoutの未完結・未出力spanは未測で、Aの呼出0も観測できた完結区間の範囲を超えて一般化しない。

CLI後処理は原証拠コピーからcode-fixed-sha.txt、code-inventory.json、inventory.candidate_costsを除去し、固定版のfinalize_outputを実行した。code-fixedと開始5ファイルのblob/hashが再生成され、candidate_costsは完全一致、比較器も手動補完なしで同じINCOMPLETE/exit1になった。**ただし提出code-inventory全体の完全再生成ではない。** 自動生成されるキーはcode_sha/filesだけで、analysis_code_sha、analysis_files、measurement_functions_unchanged、exec_dispatch_unchanged、exec_json_branch_unchanged、dispatch_changeは再生成されない。これらは本レビューでGit実物から別途照合した。比較器mainはcode-inventory自体を読んで検証する実装ではなく、比較器成功だけで版の来歴が検証済みとはしない。

## 検証結果と保証の範囲

|検証|061での確認方法|結果|
|---|---|---|
|専用比較器|060固定checkout、一時証拠コピー、--self-test|INCOMPLETE/exit1、evidence=valid、codec3組一致、取引未達保持|
|比較器8負例|元のself-testを再実行|入力欠落/native改変/reason改変、取引case欠落/error target/memory/output改変、archive改変を全拒否|
|scope6負例|元のself-testの別processを再実行|本番/旧証拠/decision-log/workflow/未列挙code/依頼本文の全6件exit1|
|codec154/975|6原試行と最新回帰archiveのsummary/log|全成功を照合。今回Godotでの再実行ではない|
|取引172/2178/97kill|原期待集合・6試行の原summary/case/bytes|3成功3失敗。off-10は171/2163、全体成功扱い不可|
|16伝播|原off-07＋propagation-deltasで全16証拠集合を再構成、変更bytes/hash・件数・原log hash/exitを照合|control0、15負例1の保存証拠が整合。validatorの新規実行ではない|
|R-01～R-08|最新回帰原stdout/stderr/exitを元judge_outputで再判定|全PASS、tests_ran=true、parser_failed=false、保存判定と一致|
|保護26|原回帰前後ログ＋今回check_frozen_files.py|26/26一致|
|素材strict/import|最新回帰の原実行・原log・警告検査|記録上exit0、警告なし。今回の新規実行ではない|
|Windows専用060|Windows採取archiveなし|未実施、Linuxで代替不可|

元回帰の14コマンドは保存executionとinventoryの対応が一致、全exit0・監督stopped=true・timeoutなし、原stdout/stderrに禁止警告なし。R-01～06/R-08のGUT assertionsは765/946/73/293/79/87/2302、R-07は専用判定を適用した。今回`godot --version`は4.6.3とFontconfig cache警告を返した。4.7.2の代わりには使わず、導入・設定変更も行っていない。したがって4.7.2実行体の現環境bytes、新規R/Godot/取引試行、新規16伝播実行は未検証である。

## CIと059世代問題

060の51終了・43成功・8失敗は061依頼書と親からの情報であり、061による直接取得ではない。060報告のinventory.baseline_ciは059提出のCIで、060最終CIへ転用しない。GitHub APIへの既存実行は次のとおり。

```sh
timeout 30s gh api repos/hiroshitanaka-creator/RPG-maker/commits/4ec85645d883897a5c1c18e2b53f60a7818710d5/check-runs --paginate --jq '.check_runs[] | [.name,.status,.conclusion] | @tsv'
```

実行結果はexit1、`Get "https://api.github.com/repos/hiroshitanaka-creator/RPG-maker/commits/4ec85645d883897a5c1c18e2b53f60a7818710d5/check-runs?per_page=100": Forbidden`。数値HTTP status・応答本文・発生元は未取得。再試行・代替API・別経路の取得はしていない。061最終SHAの全CI終了も同じ制約で未確認とし、成功や終了を推測しない。

依頼書のnative run38006271798について、固定055/057の両OS取引時間未達、最新Windows本体時間未達、最新4jobのscope059失敗を別事象として保持する。親によるUbuntu latest/primitives artifact11651858421とWindows latest/transaction artifact11652390544のraw archive/member照合・scope059確認は親の証拠であり、当方の直接照合と記さない。他2jobの個別失敗原因は未確認。

固定対象ローカルで以下を実行した。前者exit0、後者exit1・`SCOPE059_FAIL: 完成後担当外:`を再現した。

```sh
python tools/fixtures/equipment-save-transaction-platform/scope059.py --code-sha 41a34ea33fe184274e6722c88cdbca2a7ffd3708 --source-sha 41a34ea33fe184274e6722c88cdbca2a7ffd3708
python tools/fixtures/equipment-save-transaction-platform/scope059.py --code-sha 41a34ea33fe184274e6722c88cdbca2a7ffd3708 --source-sha 4ec85645d883897a5c1c18e2b53f60a7818710d5
```

scope059.pyの41行付近は完成後差分を059専用文書/証拠に限定している。diagnostic_ci057.pyは最新sourceへこの検査を適用し、workflow latestでは両OS・両phaseがその診断を実行する。060で新しい依頼書・計測codeを追加するとこの条件に抵触する。本番や059の監督修正が再故障した証拠ではなく、059段階の変更範囲を後続最新へ適用する世代問題である。これはローカルに再現した機序であり、未取得の全job原物の原因を確定したものではない。

## 指摘と次の最小範囲

1. **高：059範囲検査の世代境界が最新CIを拒否する。** 対象はscope059.py:41、diagnostic_ci057.pyのscope059呼出し、equipment-transaction-platform.ymlの最新診断配線。再現と証拠は前節の固定SHA正負。別件で、完成範囲は059完成SHA/当時checkoutに固定して全正負を残し、継続する監督・bytes・回収の不変条件は最新HEADで別に検証する。旧assertion→固定側/最新側/後続条件の対応表と正負例を用意する。単純な許可パス追加・skip・失敗無視では解決しない。既存検査/CIの変更になるため別の明示承認が必要。061では変更しない。
2. **中：取引on/off全同等性は未成立で、inspect・子timeoutの原因を特定できない。** 対象は060のrun-on-09/off-10/on-12と既存driverのinspect分岐（553～558行付近）。再現は原証拠コピーへの比較器と上表。inspect直前のbefore全file bytesは永続化されていないため、059で観測したQA log原因を060の原因へ転用できない。最小案は専用一時checkoutだけでbefore/afterのpath/hash/bytesと子の残余予算・終了経過を採取し、既存assertion・予算を一切変えず調べる別依頼。今回の局所計測を全取引受入へ昇格しない。追加採取コードは別承認、既存条件の変更はさらに明示承認が必要。
3. **低・再現性の限定：CLIの最小生成と詳細な版監査は別。** 対象はcheck_equipment_save_codec_cost.py:200～213とcompare_results.py:203以降。再現は上記finalize_outputのコピー再生。候補値と比較結果には手動補完不要だが、詳細6キーとcode-inventoryの検証まで自動再現されるという保証はない。今回の10 blob・6関数・分岐一致には問題を認めなかった。詳細監査も自動化する場合は別件で明示的な解析SHAと実blob再計算・欠落/改変負例を追加する。現060のデータ改ざんや誤計測の指摘ではない。専用code変更を伴うため別承認が必要。

性能面の次の最小案は、まずvalidateのexclusiveを専用一時計測で細分する調査である。取引第1onのvalidateは4936回・inclusive142.941秒/exclusive112.578秒、context_errorsは12590回・45.873秒の並行累積。validate内のschema、equipment_layer、session.validate_state_common、validate_actor_common等の未観測区間を区別し、正常/異常/中断/再開別・全12試行方式・同一予算で寄与と計測負荷を確認する。これもwall寄与や主因の確定ではない。Aは取引の観測呼出0、Bは累積1秒未満であり、F1解消を狙う本番最適化の即時採用は支持しない。6境界の再読取、元metadataの不正拒否、SavedDocument単独の入れ子拒否、全出力bytes/値/型/不変条件を維持し、境界間cacheや検査削減を提案しない。

F1、F4実ENOSPC/nested別volume、inspect原因、子timeout原因、Windows060未測、旧351診断失敗原因、通常UI未接続は未解決。電源断・未完結span・codec正常/拒否別時間・候補の改善効果もこの照合で実測済みにはならない。

## 実行した再現手順と提出

```sh
git worktree add --detach /tmp/qa061-fixed-060 4ec85645d883897a5c1c18e2b53f60a7818710d5
# 060証拠を /tmp/qa061/evidence へコピー後、060固定checkoutで実行
python tools/fixtures/equipment-save-codec-cost/compare_results.py --output /tmp/qa061/evidence --self-test
python tools/check_frozen_files.py
```

追加の一時Python監査は、`/tmp/qa061/audit.py`（原archive/全hash、Git blob/AST、scope、元configとspan独立集計）、`replay.py`（原回帰判定、16差分再構成、finalize、計測patch、旧集計再現）、`semantic.py`（独立した意味/bytes対照）を実行し、全exit0。前述の比較器exit1とscope059対象exit1は、未達・範囲拒否を保存する結果であり成功へ書き換えていない。一時スクリプトとJSON/logは許可された一時領域だけに置き、元の証拠は変更していない。集計方法は、原JSONのend-startをinclusive、そこから同じspanをparentに持つ直下の子duration合計を引いてexclusiveとし、候補Bはencode_candidate→native_metadata_errorsの直下だけを抽出した。元bytes、期待値、版、結果の数値は本報告とリポジトリの固定証拠で追跡できる。

提出変更は次の2ファイルだけ。最終commit SHAとpush/remote一致・clean/未push状態はcommit後の最終応答で記録する。CIは直接取得できず全終了未確認のまま親へ引き継ぐ。「CI緑を含む完了」とは宣言しない。

- docs/tasks/061-review-save-codec-cost.md：状態行のみ。
- docs/tasks/reports/061-review-save-codec-cost.md：本報告。
