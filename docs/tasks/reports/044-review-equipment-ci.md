# 044 装備専用CIの独立レビュー

## 開始状態・計画

開始／登録SHA `c7368265c8a6156cb84f78ac7911a937dc9f6030`、branch `codex/task-044-review-equipment-ci`。開始時の未コミット・未pushは0。remote同名branchと一致を確認した。レビュー対象043は `73e09c7714ad3766ea6dfdc04c19cca57e4c1231`、PR #30、全tree基点は `a5cbeb0bb6f239958b2330d414afc0752c4fe36a`。登録SHAと対象043の差は044依頼書の追加だけで、実装・検査器・workflowは同一。

計画は (1) AGENTS・043依頼／報告・原検査・固定証拠を照合、(2) 全wrapperと14jobの実行対象・上限・失敗伝播を監査、(3) 35fixtureと独自反例・代表固定／最新原検査・旧比較を独立実行、(4) 対象043と提出044の全CIを照合し、担当2文書だけcommit/pushする、の順。

AGENTS、素材規約、職業・魔物化企画、素材台帳の構造／全1154画像・15音・2字体登録、036/038/041/042報告、043/044依頼、新workflow全文、新wrapper438行全文、原検査3本と旧fixture／期待JSONを確認した。checkout `.agents/skills` は存在せず、`/workspace/.agents` にskillなし。catalogの [verification-before-completion](skill://plugins~Plugin_60aea7460bd4819199fd97a9553a5e12/verification-before-completion/SKILL.md) を適用した。追加委譲・本番修正・main書込み／マージなし。

## 判定

**要対応：P2を1件。P0/P1なし。** 実際の043最終CIは全68jobが成功し、全28専用artifactにも原検査の正常実行を確認した。一方、旧比較wrapperのartifact検証に、原コマンドの欠落／重複や偽の比較結果を受理する反例がある。成功した原検査の結果と、破損したartifactを拒否する能力は別の判定である。043全体を無条件PASSとはしない。

### F1 / P2：旧比較で原検査実行の欠落・重複を拒否できない

対象 `tools/run_equipment_ci.py:192` の `compare_legacy`、特に204〜214行、および `check_legacy`（148〜155行）。実行記録については「5件／exit0／timeoutなし／警告なし」とlog hashしか調べず、必須コマンドの集合・一意性・原検査PASS行を確認していない。fixture hashは3artifact間の相互一致だけで、固定041の5原本hashとの一致を確認しない。旧JSONは件数と一部boolのみで、固定ケースIDや比較対象の値／型／metrics/history等の必須フィールドの存在を検証しない。

実際のPR側3artifactをコピーし、最新版の `commands` をversionコマンド5件に置換すると、原検査記録なしでもexit0／comparison.status=PASSとなった。原検査のcommandだけ `['true']` に置換、または `legacy.log` をPASS行のない文にして当該log hashだけ更新してもexit0。さらに3版のfixture hashを空辞書へ揃えても受理し、3版のlegacy.jsonを値・型・入力・出力を持たない142＋10件のboolだけへ置換し、各legacy.jsonのmanifest hashを更新すると受理した（付録の全文で再現）。

これはネットワークからの任意artifact混入や現在CIでの原検査省略を示す指摘ではない。現在workflowは同runのlegacy producerを使い、producer自身の失敗はworkflowの失敗になる。実際に取得した全6旧artifactには5種の正しいコマンド、正常PASS行、固定fixture hash、完全な値出力がある。ただし、比較入力の記録欠落・取り違え・将来のproducer回帰に対して「原検査実行を検証してから比較する」という043の契約を満たさない。

修正案（未実装）：version／前保護／import／原legacy／後保護のコマンドを種類・一意性・予算・実ログのPASS行で確認し、fixture5件を固定041 blobのhashへ照合する。legacy出力の固定ケースIDと必須フィールドを検証する。以下の受理された反例を失敗伝播fixtureに追加する。修正権限は044にないため実装・既存検査は変更しない。

## 全tree・workflow・assert対応

`git diff --name-status a5cbeb0 73e09c7` は547件（A546/M1/D0）。うち新証拠542件、残りは新equipment-save.yml、新run_equipment_ci.py、043依頼／報告、decision-log追記のみ。既存3workflow・本番・data・assets／原画・test／.scope-lock・addons・既存検査・既存証拠は全blob不変。decision-logの既存本文もprefix一致。既存workflow SHA256は043 start.jsonの3件と一致した。

全14job＝core4＋invalid3＋migration2＋legacy3＋comparison1＋failure-propagation1。push／pull_request／手動で実行、PRのcheckoutはmerge refではなく `github.event.pull_request.head.sha`。権限contents:read、全job15分、matrix fail-fast:false、continue-on-errorなし。保護照合とuploadはalways、artifact欠落はerror。Godot取得ZIPは既存指定SHA256で照合する。固定版もdetached worktree、XDG隔離、出力先は新規限定。coreの古い固定名JSONを先に消し、最新と固定の成功を混同しない。

| 原検査 | 固定対象 | 最新 | 原件数／予算 |
| --- | --- | --- | --- |
| core | 036 `dbceae8f68e18939a40ace71f3a24a1a1953e653` | 同一旧全本文を038追加版で実行 | 5394／400切替、240秒 |
| core追加 | 038 `45a58b7faf09809d916954353a3a1fe0c3d2d035`、041 `8d3c1848d09b588fa41bcf6345d3aab6e12a5347` | HEAD原検査 | 旧5394＋93＝5487／400、240秒 |
| invalid | 038、041 | HEADの原ハーネス／対象SHA | 202ケース／1576条件、各子30秒 |
| migration | 041 | HEAD原検査 | 61ケース／2828条件、63観測、120秒 |
| legacy | 基点 `821448b384d37edc041152beb5d6b6f560ad771d`、041 | HEAD実装＋041同一fixture | 142検証／10更新、120秒 |
| comparison | 上記基点／041 | 最新との全出力byte比較 | F1の検証不足あり |
| self-test | 専用合成fixture | HEAD wrapper | 35件（対照5 exit0、拒否30 exit1） |

import600秒、版／保護各30秒を保持。invalidの外側timeoutはNoneだが、既存原ハーネスの子30秒とjob15分が作用する。時間延長や原assert省略はない。

assertion-mapの原ソース5件の固定hash、全323行の原statement／行番号／omitted=falseを機械照合した（036 core106、038 core114、invalid14、migration83、legacy6）。静的呼出し位置と展開後件数を区別する。038の旧関数本文は036とbyte一致し、038以降core・invalid・041 migration／legacyの最新原本は固定版とbyte一致。固定036/038/041のscope確認も独立実行した。

期待はcoreの手書き職／装備／数値表、invalidの固定境界値と理由、S1 expectations.jsonの数量／所有／JP／固定ID、旧入口の基点実出力にある。被検査実装から期待を再生成していない。invalidの元dataからのfixture変異と、期待値の生成は区別した。取得したCI証拠では異常202件のfixture hash／観測全文、S1全63観測全文も固定原証拠と一致。旧fixtureの5原本hashを041 blobへ独立照合した。

S2で置換される `M07現GameSessionは新保存を拒否` は固定041で保持し、最新側を新版codec／全状態受理の正負検査へ移行する必要が043報告に記載されている。今回最新はS1のため原assertを全実行。当時の範囲／未接続条件を最新への永続的な接続禁止へ転用していない。042付録59条件・91型ケース／273条件は今回専用CI外であり追加していない。

## 独立実行

ローカル既定Godot4.6.3は版確認だけ。公式4.7.2を別取得し、ZIP SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、実体 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e` を照合。実行対象latestは登録c736826（対象043から依頼書追加のみ）。出力は `/tmp/review044/`、wrapperが別checkoutとXDGを作成し、原証拠は上書きしない。

共通実行コマンド：

```sh
python tools/run_equipment_ci.py --suite SUITE --profile PROFILE \
  --latest-sha c7368265c8a6156cb84f78ac7911a937dc9f6030 \
  --godot /tmp/review044/bin/Godot_v4.7.2-stable_linux.x86_64 \
  --output /tmp/review044/equipment-SUITE-PROFILE
```

| suite / profile | 原検査の実秒／import秒 | 結果 | 出力JSON SHA256 |
| --- | --- | --- | --- |
| core / 036 | 0.565 / 69.867 | exit0、5394条件／400切替 | `d6fcec3060432492ee78705079b7b11783040a4181d853b7926a38da689c8b4d` |
| core / latest | 0.615 / 130.557 | exit0、5487条件／400切替 | `1ad52c7843eaeb6f290eb36a0e090838dd2cd97b22a6fda2105e36c2529085c5` |
| invalid / 038 | 62.349 / 不要 | exit0、202/202／1576条件 | `d36cd934f6797998542f544029f24fc73b30266c72f01ba85c67c5bad1071ccf` |
| invalid / latest | 72.477 / 不要 | exit0、202/202／1576条件 | `745ee6f45c1ecc51e5ec9cfd25849b59b3e6e6ddceb9274f01b023862a1b005f` |
| migration / 041 | 15.559 / 62.239 | exit0、61ケース／2828条件／63観測 | `635b4f4ce3535b77d25d54e2660308cc30ff8ef00dd4c8191683c4505f7dbbaf` |
| migration / latest | 16.496 / 62.224 | exit0、61ケース／2828条件／63観測 | `e399122438ce0ba968de9757373acb0df683813afd01c5a1cd10858f6c334f17` |
| legacy / baseline | 1.87 / 55.234 | exit0、142検証／10更新 | `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea` |
| legacy / 041 | 1.969 / 73.477 | exit0、142検証／10更新 | `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea` |
| legacy / latest | 1.969 / 56.276 | exit0、142検証／10更新 | `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea` |

旧比較も `--suite compare --latest-sha c7368265c8a6156cb84f78ac7911a937dc9f6030 --inputs /tmp/review044 --output /tmp/review044/local-comparison` でexit0。基点／固定041／最新の全出力byte一致、上表の3 hashが一致。各wrapperの前後保護26件、全原ログの警告／失敗0、各予算内を確認した。ローカルcore038/core041/invalid041は別途重複実行せず、当該固定版は043両イベントの原CI artifactで確認した。


35fixtureは `--suite self-test --latest-sha c7368265c8a6156cb84f78ac7911a937dc9f6030 --output /tmp/review044/self-test` で再実行し、対照5件exit0／拒否30件実exit1を確認。別プローブでJSON重複キー、S1観測欠落／重複／理由改変／leaf件数改変も拒否した。coreの偽Godot（版と成功行だけを出し、原検査もJSON生成もしない）を別出力で起動すると、古いJSONは利用されずFileNotFoundでwrapper exit1／execution.status=FAIL。公式CIはZIP hashでも偽engineを排除するため、このプローブをengine差替え可能性の指摘には使わない。

`python tools/check_frozen_files.py` は26/26一致。`python tools/validate_assets.py --strict` は画像1154／音15／字体2／パレット3、問題0。

## 043最終CIの直接観測

GitHub接続済みAPIで6runの全job終了を取得した。ghのREST／GraphQLはForbiddenだったため成功した接続済みツールへ切替。親報告やPR本文の成功表示だけを根拠にはしていない。

| event | workflow | run | 終了したjob |
| --- | --- | --- | --- |
| push | CI | 37613507787 | 3/3 success |
| push | 006固定受入と最新回帰 | 37613507814 | 17/17 success |
| push | Equipment and Save CI | 37613507949 | 14/14 success |
| pull_request | CI | 37613514075 | 3/3 success |
| pull_request | 006固定受入と最新回帰 | 37613514094 | 17/17 success |
| pull_request | Equipment and Save CI | 37613514157 | 14/14 success |

| 全job名 | push | pull_request |
| --- | --- | --- |
| Godot・凍結受入テスト | success | success |
| acceptance-and-regression (fixed) | success | success |
| acceptance-and-regression (latest) | success | success |
| equipment-core (036) | success | success |
| equipment-core (038) | success | success |
| equipment-core (041) | success | success |
| equipment-core (latest) | success | success |
| equipment-failure-propagation | success | success |
| equipment-invalid (038) | success | success |
| equipment-invalid (041) | success | success |
| equipment-invalid (latest) | success | success |
| equipment-legacy (041) | success | success |
| equipment-legacy (baseline) | success | success |
| equipment-legacy (latest) | success | success |
| equipment-legacy-comparison | success | success |
| equipment-migration (041) | success | success |
| equipment-migration (latest) | success | success |
| lifecycle-audit | success | success |
| normal-input-and-rendering (fixed, details) | success | success |
| normal-input-and-rendering (fixed, journey) | success | success |
| normal-input-and-rendering (fixed, restart-0) | success | success |
| normal-input-and-rendering (fixed, restart-1) | success | success |
| normal-input-and-rendering (fixed, restart-2) | success | success |
| normal-input-and-rendering (fixed, restart-3) | success | success |
| normal-input-and-rendering (fixed, restart-4) | success | success |
| normal-input-and-rendering (latest, details) | success | success |
| normal-input-and-rendering (latest, journey) | success | success |
| normal-input-and-rendering (latest, restart-0) | success | success |
| normal-input-and-rendering (latest, restart-1) | success | success |
| normal-input-and-rendering (latest, restart-2) | success | success |
| normal-input-and-rendering (latest, restart-3) | success | success |
| normal-input-and-rendering (latest, restart-4) | success | success |
| 素材検査 | success | success |
| 試遊前の通常戦闘・案内・画面・復帰検査 | success | success |

専用artifact全28個をダウンロードしてZIP digest、全1922 member、各sha256.json、executionの最新／固定SHA、終了コード、timeout、警告、公式engine hash、原コマンド、個別予算を直接照合した。原ケース／観測全文も上記のとおり照合し、両イベントの旧比較をローカルで再実行してbyte一致を確認した。旧出力SHA256は3版とも `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea`。F1の反例はダウンロード原本を保ち、別のコピーにだけ適用した。

| event | artifact ID／名前 | ZIP SHA256 |
| --- | --- | --- |
| push | 11479726256 / equipment-invalid-041 | `84d63c809cab170e66e647ab161dbff71ae04052aac7d851e6ad9aaec23e9f07` |
| push | 11479721749 / equipment-core-036 | `0ff36d5f81182fb61ff66a7441de62677bdb129a2b1cc0ab95e96bbf512d5f5d` |
| push | 11479486019 / equipment-failure-propagation | `933cd0e9bf7ff236d0e532e204ddce88ade5de3473dda72b942d4eb88903a10f` |
| push | 11479257245 / equipment-migration-041 | `99cf49cf69b91c3d9b3ab0d0d92c7020828098099656e4632da3fafaf14c6021` |
| push | 11479237060 / equipment-core-041 | `4da9812e64dbb2d188fee9b549528b2ea15abd8f7e6837c0890357a491d1bd59` |
| push | 11479216930 / equipment-legacy-latest | `b63b0e94d12f1049c8371d494bab55005366cb3796ebcca6373aecd0d2818d86` |
| push | 11479202070 / equipment-legacy-baseline | `990d78393beb883846c6e02cbbe27c9ba56863cab8ceb027607ed5e48aad7d56` |
| push | 11479147668 / equipment-legacy-041 | `5f3e2ea6e1b5b71f7b1a53ca9ed1f9590abdd145289a6eee83c077bee7e315c8` |
| push | 11479051846 / equipment-invalid-latest | `4ae2058fceda9b54bbac48e83bd7952c8cc9d673020670cc17c3b41308a614d9` |
| push | 11479026473 / equipment-core-latest | `91bef4d614aeec158ba8ec7ea7d1c72b26493cfab0879526a1b7b61bb90bf59f` |
| push | 11478926440 / equipment-invalid-038 | `2ecf2c5487b28003ac32379031cf471d92e43c8e2d4a8163756b08cf74c836e8` |
| push | 11478722314 / equipment-core-038 | `1efb44d6607959233e9033e336a7618a3ee9aecf06ee7fb5d0f0464036034fa8` |
| push | 11478682301 / equipment-migration-latest | `3244cd60affd07a3f2a05138b0a5c011ac14f076dcac20e4f47a63d3f34f9b0c` |
| push | 11478677703 / equipment-legacy-comparison | `f7a3a8e6c45e0b9556b687b66e5a8519db8e27ecd224e2d4d957c420b2c1fafa` |
| PR | 11479672510 / equipment-invalid-latest | `fb7a93d8fb3da8ff386c2eb0813c16a9273244b6d9147f16d5d29e245d4a923b` |
| PR | 11479397318 / equipment-migration-041 | `bbd3eb095300983151895de851d671b9e7cf572e97d42d4af05c791756bc8705` |
| PR | 11479261678 / equipment-failure-propagation | `c92015cd60a80c2309843d4c9af9aca63e8b5def847285cae48f662f29648d2f` |
| PR | 11479191869 / equipment-core-041 | `0be01a95fe808d7843911c92ac49ff09f1e3cb84e509d66a9f17028fa9ef3a42` |
| PR | 11479127408 / equipment-core-latest | `373f6732a6417c235a2a70ef7d09d288c5e0d99ebf9c987b9ea9f3c5051aa80d` |
| PR | 11479052160 / equipment-core-036 | `6f9aa8d1191883c5873151d7d6c8bd675142a5ad6581b7f7c4d30980dc990000` |
| PR | 11479047425 / equipment-core-038 | `0e613d6d015f2169669707a14db71f723646ea46ceb464d82c0d67ec5bec642f` |
| PR | 11479027587 / equipment-migration-latest | `1d9ff24868200b51bec61c0da235e3854e508d0a9099b4eb7819dce5f9a64c7a` |
| PR | 11478988309 / equipment-legacy-041 | `fccce17c8448418d39a216ad7abb5135ed1606d4d6e04330efbb93e2f38596e9` |
| PR | 11478812039 / equipment-legacy-latest | `69906c83bc397c6f904b46713d98fd0578ec9e085319291672d3ddc8358c1d66` |
| PR | 11478742156 / equipment-legacy-baseline | `2e220a36a1601bac99f168be55f9676ca2e228286237f769ba034498df7c4b94` |
| PR | 11478722768 / equipment-invalid-041 | `61b855fcb5664d8643d827ff4988b123e456807d1ec43b03e229e56d0bcb1448` |
| PR | 11478492941 / equipment-invalid-038 | `30010c914ad56ed8f94c4b97ac450b091ccf15520b2386d77df5a43ba38dc7aa` |
| PR | 11478438337 / equipment-legacy-comparison | `0d6c0ee860729762a552855dbe575e37160fb3133d69a0711a9e5a06d534e43d` |

既存artifact38個も全取得し、対象SHA／有効期限／ZIP digestを照合した。うち残り36 ZIP（14398 member）は全CRCも検査し破損なし。既存描画画像の目視再評価や各過去JSONの意味検証は今回行っていない。godot-import-logの両原ZIPからR-01〜R-08の全PASS／exit0／tests_ran=true／parser_failed=false／timed_out=false／failure_messages空を確認。R-08は17テスト・2302assertion・失敗／保留0。これはCI証拠の読取りでありローカルR8再実行ではない。

| 既存artifact | ID | ZIP SHA256 |
| --- | --- | --- |
| 37613507787 / godot-import-log | 11479694874 | `54c1dcbfa634362743cea8cef0c914c554a5f626ef8e5d992513d899e1000951` |
| 37613514075 / godot-import-log | 11480820023 | `f9f58aa023b53ded7781983e75af9cf70328e06b4e62e23711dc38d9e8f94031` |
| 37613507787 / preplay-checks | 11479186867 | `a96468edda97b41ee7dfb1361dcd0543174dd4704b364abdc9bbb6fbf3a89de8` |
| 37613507814 / village009-runtime-fixed | 11479686117 | `295dffabdc05414b2fbc23490615dd448e33dff72990abe5b840c8e5ec59c4e5` |
| 37613507814 / village009-render-fixed-journey | 11479606748 | `7ade13b1d53f83a0740548559daa4ec8beaea061dd33ff80b74075a783c2ca78` |
| 37613507814 / village009-render-latest-journey | 11479552187 | `982665423b478fab5101a021730eb729d9a96e78ad10637abea429de3fe6fd3c` |
| 37613507814 / village009-render-latest-restart-1 | 11479552003 | `7ce03c7d44f877b0dd2cd3ad378813f371d673af3f89ee3e98e25a921e5bc8d8` |
| 37613507814 / village009-render-latest-restart-2 | 11479452845 | `af6f5c85b251dcb3ff246790ecf8361a732c2d60b89355e7de135af860c7146d` |
| 37613507814 / village009-render-latest-restart-4 | 11479441694 | `0ab0d8d06bd2ec75644060529797ae932eccdc807cd9a826242ac1cbe29af671` |
| 37613507814 / village009-lifecycle-audit | 11479439247 | `d3ffc467b0607c5b9704f007a1d40e420c5b0054551560b4769d8f39e2ec14d3` |
| 37613507814 / village009-render-fixed-restart-3 | 11479331545 | `2fc7c5e9aebc770b738872dedf9b2561d5859026c0be3a56250b59373fc99577` |
| 37613507814 / village009-render-latest-restart-0 | 11479227866 | `31ae8c0a6d000ed7f6cb0a5643b195596d668fbea490c103f591be385701319a` |
| 37613507814 / village009-render-latest-details | 11479153066 | `84868cfb55f7ce4c50121c1463baa0b6adac38acea9f374139a04a8faff0d67a` |
| 37613507814 / village009-render-fixed-restart-1 | 11478996611 | `d2e0246988b43c0ea8d6c8771d27c274d0f545bbc2f61b77597844771a41939d` |
| 37613507814 / village009-runtime-latest | 11478921261 | `5e9604d910a510c36e3dffc9aa571d5e7c7aa353c2782c5e31906d02f127eed5` |
| 37613507814 / village009-render-latest-restart-3 | 11478857615 | `bfea5a069c5a1576bdbec8349ea17a123333117a6d765a7ab84c56626370da1b` |
| 37613507814 / village009-render-fixed-restart-2 | 11478761635 | `c130d4554dec2c8aeaf1079591bc5bcfa74c47b84b3a8d5cd3bf8fd0dcd1a58b` |
| 37613507814 / village009-render-fixed-restart-4 | 11478666758 | `0bef1c284f63921a45e483e4a5d3f6c69737950e834c004c3251094ebb330077` |
| 37613507814 / village009-render-fixed-restart-0 | 11478632604 | `46e4968dd257213e6501dbec5527d567f5279f9a371116f9640119769211b808` |
| 37613507814 / village009-render-fixed-details | 11478607830 | `e98fde2d4d1cb853e50031de7596643d1d0fb3bed48035d5c349eb75a15e44e6` |
| 37613514075 / preplay-checks | 11479242291 | `9185e3b00b98e9c54b6f082c9872bc3fc1eaafbb1015b91e9398a4b67e8e1e99` |
| 37613514094 / village009-runtime-fixed | 11479732117 | `a763f4650bc92d1d41b8dd3baacd5cf919fea6b265984ebede51da1ddb2e6d08` |
| 37613514094 / village009-render-fixed-restart-1 | 11479722925 | `338ee46fcba749b65fdb59a792fcdf12e2bde044d0a5d2751802f5b8ed7e1f2a` |
| 37613514094 / village009-render-latest-journey | 11479627617 | `22212189809a5942b4832fe53c524aaf83e30e522846d07e86ca53c7b6fb2f77` |
| 37613514094 / village009-render-latest-restart-0 | 11479528170 | `fce4f7da66e459bb67878fd7631e3122beb102779589e97e76efb60164f4f383` |
| 37613514094 / village009-render-latest-restart-4 | 11479478228 | `f62c9b064f8be5d0f506fe423dc9d56c003fac182ddf18fbb843c24c41517301` |
| 37613514094 / village009-lifecycle-audit | 11479398209 | `19fa69d2b929ba9e3794b144f8c0240f02cd5e8cce8bbda73ca5bc674441a59b` |
| 37613514094 / village009-render-fixed-restart-2 | 11479233114 | `8555131eed21a085b3c826b556839663782be587d229a7a6684949b396331f71` |
| 37613514094 / village009-render-latest-restart-2 | 11479203032 | `371c926bac61747ec8207f2e234eae1ef9bc6e16d29818c6a7be1c9015dd91b3` |
| 37613514094 / village009-render-fixed-restart-3 | 11479202382 | `e8b6f185384fcc55c64865c10f6650bade6696b1f7bc3f0391c45779fb66d211` |
| 37613514094 / village009-render-fixed-details | 11479073191 | `99924fc31f672f2679f27d04117e6b69831d207896a7135f26555cb5192d8bff` |
| 37613514094 / village009-render-fixed-restart-0 | 11478998351 | `3bbe090c0b277c20e108d0bd2a74de4e88f0564361ac49a546544661897cf763` |
| 37613514094 / village009-render-latest-restart-3 | 11478992433 | `4b59bbfb4e93261c312ba9070075e4bbbd90600ad72f376bf0c6cd1412512402` |
| 37613514094 / village009-runtime-latest | 11478836572 | `f279015ccd92638ffeddfa310a820d2d2de6912039c4bf0e0d8e5aea0b8a9166` |
| 37613514094 / village009-render-latest-details | 11478638379 | `288b781e4f92ee4038e85d7d939cc06607de06f2d537c151b3de8de4e011bdb4` |
| 37613514094 / village009-render-latest-restart-1 | 11478538401 | `8794d7e7d66d13e897f098ba3c476139194af0ad6097d5d04defb16bae1f0778` |
| 37613514094 / village009-render-fixed-journey | 11478518610 | `a61752af05cdd9f6b240c3695030273a30a63f196a034d99c27bccb6b5a1a669` |
| 37613514094 / village009-render-fixed-restart-4 | 11478462784 | `314cb099a306ac045ec3a415c81cfcfc22ac22668dd19117835a2ab6d54d3703` |

## 未実行・提出

既存R-01〜R-08／描画／ライフサイクルの全ローカル再実行はしていない。既存CI全20jobは043の両イベントで直接観測した。手動旧本編workflow、042独立付録、S2〜S5・新版codec／通常保存／復旧I/O／実ユーザー保存／通常戦闘UI接続は未実行・保証外。F1の修正・修正後再検証は今回行っていない。

変更は044依頼書の状態行と本報告だけ。最終提出SHAとそのpush後の同一SHA全CI終了結果は、自己参照による本文更新を避け最終応答に記載する。未終了CIを成功とは扱わない。PR #30やmainは更新しない。

## 再現付録

次のスクリプトを `/tmp/review044/probes.py` として実行した。レビューcheckoutを `/workspace/RPG-maker` とし、PR run `37613514157` の3artifact `equipment-legacy-baseline`（11478742156）、`equipment-legacy-041`（11478988309）、`equipment-legacy-latest`（11478812039）を `/tmp/review044/ci/37613514157/<artifact名>/` へ展開する。認証済みghを使える環境なら `gh run download 37613514157 --repo hiroshitanaka-creator/RPG-maker --pattern 'equipment-legacy-*' --dir /tmp/review044/ci/37613514157` で用意できる。各probeディレクトリは新規にする。各ケースは新Pythonプロセスの実exitを記録する。

```python
import copy,hashlib,importlib.util,json,pathlib,shutil,subprocess,sys
R=pathlib.Path('/workspace/RPG-maker');T=pathlib.Path('/tmp/review044');SHA='73e09c7714ad3766ea6dfdc04c19cca57e4c1231'
source=T/'ci/37613514157'; names=['baseline','041','latest'];outcomes=[]
def save(p,v):p.write_text(json.dumps(v))
for name in ['control','missing_artifact','wrong_source','stale_artifact','failed_log','duplicate_command','no_original_command','no_pass_line','timeout_record','missing_commands','empty_fixture_hashes','fake_success_json']:
 d=T/('probe-'+name);d.mkdir();i=d/'inputs';i.mkdir();o=d/'out';o.mkdir()
 for profile in names:shutil.copytree(source/('equipment-legacy-'+profile),i/('equipment-legacy-'+profile))
 p=i/'equipment-legacy-latest';ep=p/'execution.json';e=json.loads(ep.read_text())
 if name=='missing_artifact':shutil.rmtree(p)
 if name=='wrong_source':e['source_sha']='0'*40
 if name=='stale_artifact':e['latest_sha']='0'*40
 if name=='failed_log':
  c=e['commands'][3];(p/c['log']).write_text('ERROR: independent fixture\n');c['log_sha256']=hashlib.sha256((p/c['log']).read_bytes()).hexdigest()
 if name=='duplicate_command':e['commands']=[copy.deepcopy(e['commands'][0]) for _ in range(5)]
 if name=='no_original_command':e['commands'][3]['command']=['true']
 if name=='no_pass_line':
  c=e['commands'][3];(p/c['log']).write_text('original check not executed\n');c['log_sha256']=hashlib.sha256((p/c['log']).read_bytes()).hexdigest()
 if name=='timeout_record':e['commands'][3]['timed_out']=True
 if name=='missing_commands':e['commands']=[]
 if name=='empty_fixture_hashes':
  for profile in names:
   q=i/('equipment-legacy-'+profile)/'execution.json';v=json.loads(q.read_text());v['fixture_sha256']={};save(q,v)
  e['fixture_sha256']={}
 if name=='fake_success_json':
  fake={'validation_count':142,'upgrade_count':10,'failures':[],'validation':[{'case':str(k),'unchanged':True} for k in range(142)],'upgrades':[{'case':str(k),'imported':True,'saved':True,'loaded':True,'roundtrip':True} for k in range(10)]}
  for profile in names:
   q=i/('equipment-legacy-'+profile);save(q/'legacy.json',fake);man=json.loads((q/'sha256.json').read_text());man['legacy.json']=hashlib.sha256((q/'legacy.json').read_bytes()).hexdigest();save(q/'sha256.json',man)
 if p.exists():save(ep,e)
 code="import importlib.util,pathlib;s=importlib.util.spec_from_file_location('m',%r);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.compare_legacy(pathlib.Path(%r),pathlib.Path(%r),%r)"%(str(R/'tools/run_equipment_ci.py'),str(i),str(o),SHA)
 with (d/'result.log').open('w') as f:r=subprocess.run([sys.executable,'-c',code],stdout=f,stderr=subprocess.STDOUT)
 outcomes.append({'case':name,'exit':r.returncode});print(name,r.returncode)
save(T/'probe-results.json',outcomes)
```

| 独自比較プローブ | 実exit | 判定 |
| --- | --- | --- |
| control | 0 | 正常対照 |
| missing_artifact | 1 | 欠落拒否 |
| wrong_source | 1 | 別対象SHA拒否 |
| stale_artifact | 1 | 古いlatest SHA拒否 |
| failed_log（hash更新済み） | 1 | ERRORログ拒否 |
| timeout_record | 1 | timeout記録拒否 |
| missing_commands | 1 | 全コマンド欠落拒否 |
| duplicate_command | 0 | F1：versionだけ5件を受理 |
| no_original_command | 0 | F1：原コマンドをtrueへ置換しても受理 |
| no_pass_line（hash更新済み） | 0 | F1：原PASS行欠落を受理 |
| empty_fixture_hashes | 0 | F1：3版共通の空fixture hashを受理 |
| fake_success_json | 0 | F1：値・型を欠いたboolだけの偽結果を受理 |

core原検査未実行プローブの偽実行ファイル全文（実本番・原検査は改変しない）：

```python
#!/usr/bin/env python3
import sys
if '--version' in sys.argv:print('4.7.2.stable.official.ed1daf0bf')
elif '--script' in sys.argv:
 print('EQUIPMENT_CORE_PASS: checks=5394 transitions=400 failures=0')
 print('EQUIPMENT_VALIDATION_PASS: additional_checks=93 failures=0')
```

上記を `/tmp/review044/no-original-godot` に保存してchmod +xし、共通コマンドのsuite=core/profile=latest、godotをそのパス、outputを新しい `/tmp/review044/no-original-run` にする。実測exit1、`core-checks.json` 不在、最終 `EQUIPMENT_CI_FAIL`。これはF1のcompare入口と異なり、producer入口では原結果欠落を正しく拒否した対照である。
