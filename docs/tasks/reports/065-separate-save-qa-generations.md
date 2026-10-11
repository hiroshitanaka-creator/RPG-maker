# 065 保存QAの世代分離・pins修正報告

2026-10-11 UTC。**pins修正をローカルで検証済み。修正後の全CIは親確認待ち。保存全体・F1/S3は未達を残す。**

|対象|完全SHA|
|---|---|
|承認済み065登録|520169e72fd5a86d485bbf29577a9a22f34e96c8|
|修正前の提出|37be1af2eea8f8612033607faed67e8a33eb94db|
|修正後の完成コード|7aa7c6ff6eba620b93b741d58290fb698fb7cf5e|
|修正後の実行HEAD|b04ffade8faf3a722dac35d072dba50818d50cec|
|059固定検査|41a34ea33fe184274e6722c88cdbca2a7ffd3708|

最終提出SHA・remote一致・clean/未pushは最終応答で確定する。20許可パスのうち19パスだけを使用し、README本体・tasks README・decision-log・CI YAML・本番・監督・原検査・原予算は変更していない。main取込み・PR作成はしていない。

## 親が確認した初回CIの失敗

親から、初回提出37be1afの全51 jobが41成功・9失敗・1取消で終了したと連絡を受けた。最新4 jobは065完成SHAを追加fetchするgeneration-pinsが30秒でtimeoutし、stopped=false、後続Gitが128になった。これは新設065配線の問題として修正した。親のメッセージを証拠へ保存したが、生ログbytesを当方で受領・照合したことにはしない。

本体のUbuntu168ケース/2118条件/130.467秒・4 kill子timeout、Windows49/735/174.813秒、別途報告の108/1548/174.093秒は別の失敗として残す。Windows primitivesの旧診断は固定059全10・capture12/27が通った一方、既存PowerShell Get-CimInstance/Get-Volumeが30秒timeoutし12sampleがない。担当外diagnostics057.pyは変更しない。旧041 invalidは固定SHA取得中14分54秒で取消、202ケースNOT_RUN・artifactなし。取消主体/原因は未確定である。

## 修正

065の新規ネットワークfetchを廃止した。既存CLIの`--fetch-pins`は互換名のまま、[hashes.json](../../verification/task065-save-qa-generations/hashes.json)の`pin_objects`から元Git objectを照合して復元する。065登録・完成の元commit、全tree、必要な4コード・依頼・対応表blobの計1128 objectについて、型・長さ・原bytes・完全Git SHAを検証する。Gitへ一括保存後に全objectを再読取りして一致を確認する。元treeにある全path/mode/blob IDを保持し、巨大な過去証拠blobを取得せず完成差分を判定する。065全体をcheckoutする資料ではない。既存workflowが取得する059の3 SHAは引き続き必須で、欠落時の新fetchや代替経路はない。

pinsの元30秒内を実行25秒・回収5秒に分けた。process_captureと既存予算は不変。pins失敗時は依存する世代契約・専用正負をNOT_RUNとし、予定argv・阻害理由を残す。未起動のpid/実argv/exitを補完しない。監督停止が未確認なら後続の子を起動しない。停止を確認できたpins失敗では、依存しない元5診断は継続し、全体FAILと非0を保持する。

旧112 assertionの対応は維持し、新条件は14、専用正負は56へ増やした。独立した空のGit DBで復元/範囲違反拒否、元objectの欠落・重複・改変・SHAすり替え、実timeout回収、依存未起動と停止未確認を検査する。旧45正負も削除していない。新fixtureの反例commitは元tree全項目を保持して対象leafだけを変更し、旧範囲assertionの期待値は変更しない。

## 修正後の検証

alternatesなし・depth=1の独立cloneを使用した。開始時に065登録/完成objectの欠落（cat-file 128）を確認し、外部fetchなしで0.115秒で復元した。clone/既存059資料の準備にはローカルfileリモートを使用したため、GitHub通信速度の証明ではない。

- 公式Godot4.7.2 import: 31.022秒、exit0、禁止警告/ERRORなし。
- 診断全体: 72.598秒、exit0。pins0.116秒、全processの終了/監督停止を確認。
- 固定059全10正負、最新capture12/27、6seedのoff/on計12sample、058反例を保持してPASS。
- 新世代契約exit0、専用56正負すべて期待exit一致（3.226秒）。
- 独立証拠集約: exit0、原証拠3175 member（索引込み3176）、ZIP 9,281,179 bytes、SHA-256 `98eef4533870f5b7591e19c8eded9ee04962d49c5d81529a7db4660869f19af7`。全member原bytes/hashを再読取り照合。
- 実30秒枠: 専用の長時間親子処理を25秒で停止、25.120秒で検査終了。timeout/非0を保持し、監督停止・wait成功・約4.9秒の回収残量・無関係sentinel生存を確認した。
- pins資料破損の実CLI: 全体exit1/FAIL、依存2件NOT_RUN、元5診断はPASS。独立collectorもexit1、Git128の連鎖なし。原記録と全memberを保存。

実30秒枠の初回は自己終了10秒の既存fixtureを使用し、timeoutにならず検査exit1になった。その失敗を保存し、新専用長時間fixtureで測定した。旧fixtureを変更したり、初回結果を成功へ書き換えたりしていない。修正前の期限同値による停止未確認は縮尺1秒で再現し、その原記録も保存した。

R8・保護26・原取引172/2178/97kill・16伝播・codecの初回ローカル原結果は下の履歴と`prior37`内へ保持する。対象実装/検査/予算の不変は最新の範囲検査で再確認した。本体を成功するまで再実行して今回のCI失敗を取り消すことはしていない。

提出全体の書式検査は原stdoutの末尾空白163行でexit2。原bytesを保持した。原stdout以外のcode・文書・JSON等はexit0。

## 証拠と残る出口

[証拠README](../../verification/task065-save-qa-generations/README.md)から元bytes・実argv・exit・時間・親CI連絡・全member manifestを追跡できる。初回37の証拠はGitから元bytesで保存し、元archiveを内包した。旧失敗/初回結果と修正後結果を区別する。

当環境のGitHub API Forbiddenは迂回/再試行していない。修正後の全CI/Windows両phase/15分job全体は未確認。Windowsの既存環境取得timeout、取引本体の未達、旧041取得中取消、従来F1/F4/060/元351/UI接続などは未解決で親へ引き継ぐ。PR・main・README・decision-logは親担当。

---

## 初回提出37be1afの報告履歴（下記SHA・結果は修正前）

以下は初回報告の原文。ここにある追加fetch・45正負・03f完成SHA・CI未確認は初回時点の状態であり、現在の方式と結果は上記の追補による。原文bytesはarchiveの`prior37/065-separate-save-qa-generations.md`にも保存した。

# 065 保存QAの世代分離報告

2026-10-11 UTC。**ローカル実装・検証済み、CI受入は未確認。保存全体・F1/S3の受入完了とはしない。** 指定ブランチへcommit/pushし、最終SHAとremote一致・clean/未pushは最終応答で確定する。

## 対象と範囲

|用途|完全SHA|
|---|---|
|指定061提出基点|6ca6ccea70491cf66c8a4f478b142f1137f23874|
|065登録|520169e72fd5a86d485bbf29577a9a22f34e96c8|
|059固定検査対象|41a34ea33fe184274e6722c88cdbca2a7ffd3708|
|065完成コード|03fbc3e0f19f32b303bf53d11a84f9302cdbc29c|
|最終ローカル実行HEAD|3fe9d836efcc818230bca321eca4293db44669ef|

初期checkoutはworkの74c656bac5494ce55176853531926f7cce38b261、clean、upstreamなし。通常fetchはmainだけを取得する既存設定だったため、設定を変更せず指定branchのrefspecを明示した。約3分強の無出力を中断せず取得し、登録SHAとその親の指定基点を確認した。追跡設定を自動設定するswitchは既存refspecとの不一致で拒否されたため、取得済みrefから同名branchを作成した。mainの取り込み、履歴書換え、PR作成、main反映はしていない。

AGENTS全文（当該checkoutの追加承認を含む）、065全文、tasks README、061/059の依頼・報告全文、指定scope/runner/collector/fixed helper/run_ci/workflow、素材規約・企画・台帳構造を確認した。checkoutとworkspaceに関連する`.agents/skills`はなかった。GPT-6 Astra／High指定は受領したが、実行基盤のモデル名/effortを独立取得する手段はなく、確認済みとはしない。

変更は許可20パスのうち19パス。未実行Windowsの架空archiveは作らず、windows-results.jsonへNOT_RUNを記録した。変更一覧・Git差分は[scope-diff.json](../../verification/task065-save-qa-generations/scope-diff.json)、全hashは[hashes.json](../../verification/task065-save-qa-generations/hashes.json)。root README、tasks README、decision-log、AGENTS、CI YAML、本番、監督、取引driver、旧検査/固定SHA/証拠、test、保護契約、素材は不変。依頼書は状態行だけ変更した。

## 実装

`diagnostic_ci057.py`の既存CLI・task059出力先を保持し、scope059だけを059完成SHAの別checkoutで実行する。基点579ca1f463aaf9e93275039a59cf9d1ffb86adb5、登録a6022f1e4a7689440928efe65db444336e9128e4、完成41a34ea33fe184274e6722c88cdbca2a7ffd3708を区別する。当時のscope059を改変せず、全10正負と原logを毎回実行する。固定checkoutの前後clean、HEAD、検査器の原bytes/hashも確認する。

最新側にはcapture-tests12、capture059追加27、6seedのoff/on計12sample、058反例を残した。世代契約と専用正負を追加し、schema3は診断7件・準備3件を固定する。既存の5診断と058準備を削らず、それぞれの180/30/180/30/180秒と準備30秒を保持。新準備/検査も各30秒。固定055/057、本体transaction/primitives、15分job、既存artifact先は変更していない。

`generation_contract.py`は065登録→完成コードの差分を20パスだけに限定し、本番/監督/原検査を含む担当外変更を拒否する。提出時の文書・証拠追記検査（`--scope-only --source-sha`）と、最新実行側の照合を分離した。最新へ065の全パス許可集合を無制限に適用せず、後続の独立文書や新しい独立codeの追加を一律に拒否しない。一方、今回の完成配線、既存本番/監督/原検査の継続不変を照合する。将来これらを変更する際は、その承認範囲に対応した次の契約/回帰へ明示的に移す必要がある。

[assertion-map.json](../../verification/task065-save-qa-generations/assertion-map.json)は固定059にあるassert/raise/失敗追加112箇所を、周囲の条件式・AST hashとともに一意に列挙した。「当時だけ」は固定scope059、「最新でも継続」は最新capture/計測/実行・証拠判定に配置し、新しい配線・証拠契約11条件も別に列挙する。固定Git blobから再計算して、対応先の変更、欠落、重複を拒否する。最新実装から旧期待値を生成しない。

`diagnostic_evidence059.py`は旧schemaの診断5件/setup1件条件を保持し、schema3では完全SHA・実argvと予定argv・cwd・実exit・原process記録・終端/監督停止・原予算・原log hash・全member集合を照合する。Linuxの既存process_exec059 wrapperは正規の完全argvだけを許し、実argvを正規化して書き換えない。全原bytes、directory、link targetをZIPと内部manifestへ保存し、ZIPを再読取りして全memberを照合する。旧schemaへの格下げで最新追加条件を落とす入力も拒否する。

既存workflowは059完成/基点/登録をfetchする。新しい065登録・完成SHAは監督付きgeneration-pins処理で存在確認し、不足時だけ完全SHAのdepth=1 fetchを行う。YAMLの変更は不要だった。両OS・両phaseの既存latest呼出しへ同じCLIで接続しているが、Windows実動作とGitHubの15分job全体は未確認である。

## 実行結果

原argv、stdout/stderr、exit、秒、全bytesと内部manifestは[証拠README](../../verification/task065-save-qa-generations/README.md)から追跡できる。完成コードと後続文書・証拠を分離し、以下は実行HEAD3fe9d836efcc818230bca321eca4293db44669efでの結果（import/素材の採取時点は各原記録に記載）。

|検査|結果|
|---|---|
|059固定scope全10正負|正例0、9負例各1、1.070秒|
|最新capture-tests|12/12、31.089秒、exit0|
|最新capture059|27/27、5.927秒、exit0|
|058反例|0.716秒、exit0。過去の欠落/誤完全・孫継続を再現|
|最新計測|6seed/12sample、20.973秒、exit0。全取引受入とは別|
|世代契約|0.165秒、exit0|
|専用正負|45例、1.931秒、全期待exit一致|
|準備を含む直接起動の診断全体|67.754秒、exit0。全原processの終了・監督停止を確認|
|独立証拠収集|exit0、1949 member、ZIP 5,831,118 bytes、全bytes/hash一致|
|Godot import|公式4.7.2、31.120秒、exit0、禁止警告/ERRORなし|
|素材strict|1154画像・15音・2字体、6.460秒、exit0|
|R-01〜R-08|全PASS、tests_ran=true、parser_failed=false、全体71.035秒|
|保護26|26/26一致、exit0|
|原全取引|172ケース/2178条件/97kill、suite86.780秒・外87.204秒、exit0|
|原validatorと16伝播|control0・15負例各1、8.907秒。全16集合を原bytes+deltaから再構成照合|
|codec|154ケース/975条件、7.333秒、exit0|
|depth=1 Git|065範囲・必要SHA存在・059全10正負、exit0。ローカルobject referenceを使用|

既設Godotは4.6.3で契約版とは異なった。既存launcherと同じ公式URLから4.7.2を一時領域へ取得し、固定ZIP SHA-256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、実行体 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`を照合した。OS設定やインストール先を変更していない。専用process内の一時profile環境は既存QAと同じ扱い。importが生成した未追跡UID3件は一時証拠側へ移し、commitしていない。

R8は凍結契約の各verify文字列を変更せず実行し、既存judge_outputで判定した。各300秒上限も保持し、追跡中の過去scope-lock-current.jsonを書き換える代わりに一時出力へ記録した。16伝播は既存run_ci.propagationをそのまま実行し、原結果と各negative-deltaで全file hash一致を確認後、一時的な重複コピーだけ後始末した。原証拠・差分bytes・原ログ・復元索引はarchive内に保持する。

## 失敗の保持と未確認

旧scope059を061提出へ適用すると、今回も`完成後担当外`でexit1となった。原検査を成功へ書き換えていない。専用テスト追加中、最新記録をschema2/診断5件へすり替える入力が修正前に誤受理された。実exit0の元fixture/出力をlocal archiveへ残し、修正後は専用負例collector-downgradeでexit1を確認した。途中39/40/44例の成功を完成45例の結果へ転用していない。

depth1確認の最初の手入力では存在しないsource SHAを渡し、bad object/exit1となった。実HEADのrev-parse取得に直して確認した。これは実装の修正や成功までの性能再試行ではない。全取引の今回実行は1回だけである。

GitHub取得は`gh api .../commits/3fe9d836efcc818230bca321eca4293db44669ef/check-runs --paginate`がexit1、`Forbidden`。数値HTTP statusや応答本文は得られていない。再試行・代替API・別経路は使わず、最終提出の全workflow/job終了数・成功/失敗数は未確認として親へ引き継ぐ。対象SHAはpush前のローカル採取HEADであり、存在確認やCI実行済みを示す取得ではない。

未達・未検証は、Windows今回実行、両OS/両phaseの最終CI原物、GitHub shallow fetch通信、15分job全体の成立。Linuxでの67.754秒をWindowsやnative buildを含むjob全体の証明へ転用しない。Windows結果はNOT_RUN、archiveなし。

過去のF1時間未達、F4実ENOSPC/別volume、inspect/子timeoutの原因、Windows060採取、元351の原因、通常UI接続は未解決のまま。今回のLinux1回の取引成功は過去失敗の取消しでも本番最適化の効果でもない。6安全境界、元172/2178/97kill・16伝播・保護26・R8・予算・worker/batch・旧証拠は保持した。

親への引継ぎは、push後の最終SHAについて全CI終了とWindows/両phase原証拠を取得・独立確認すること。新規の範囲拡大や設定変更を求める事項はない。PR作成・main反映・tasks README/decision-log更新は親担当のままとする。

提出全体の`git diff --cached --check`は原stdoutの末尾空白81行を検出してexit2。既存検査が出力した原bytesのため修整せず保持した。原stdout以外のcode・文書・JSON等を対象にした同じ書式検査はexit0で、設定変更はしていない。2archive/18,498 memberと提出18fileのhashを独立に再読取りして一致確認した。
