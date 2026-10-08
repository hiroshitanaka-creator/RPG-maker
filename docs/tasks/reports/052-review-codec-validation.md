# 052 装備保存 codec 検証修正の独立再レビュー

## 判定

**PASS。050 の F1〜F5 は独立再現と修正後の拒否・正常対照で解消を確認した。今回の検証範囲で差し戻し事項なし。** 051最終提出の全37 CI成功をGitHub jobs APIと原artifactで確認した。052提出後の同一最終SHAの全CIは、自己参照による再commitを避けて最終応答に完全SHA・各run・全job終了結果を記す。本報告時点でまだ存在しない提出CIの成功は先取りしない。

装備全体の通常公開、S3〜S5の完成を意味しない。本番・検査・workflow・fixture・過去証拠を修正せずレビューした。追加委譲、PR作成、main反映、ゲーム規則や将来係数の決定は行っていない。

## 対象・独立性・環境

| 区分 | 完全SHA |
| --- | --- |
| 052登録・開始 | `fe0a6d27fd2ef0db81cf36d952cd5f7d9224c737` |
| 051最終提出・レビュー対象 | `6cc19d158f974e2d97b8b3cab7a00f44b3f952a1` |
| 051完成コード固定 | `d813723b3acb2c77658317e7303c83f02f957a5b` |
| 051登録・変更監査基点 | `329567e79d2a6ace2e4c3b10b729f1e76cd27071` |
| 049当時完成コード・原検査固定 | `99e9d03d4e095b4627b510efd4806f82276617c9` |
| 049提出（修正版と別） | `a09809d56658686ea7bc200ee4014112e64cff3c` |
| 050登録・F1再現 | `138e45ec3e234c75300a12cd15536e957f92a42d` |
| 049担当範囲基点 | `5f5aab4fbe48e77f7e217b71672a043be2839d34` |

MSI上の `D:/codex/Documents-Codex/2026-10-08/task-3/qa052` を提出checkout、別 `qa-before` を049固定、`qa-after` を051最終提出へdetachした。既存task-2/fix051のGitオブジェクトを読取り専用のalternateとして利用し、新規clone側だけにfetch/checkoutした。GitHub指定branchは登録SHAと一致、提出checkout開始時の未commit0・未push0。既存checkout、実ユーザー保存、アプリ、PC設定を変更していない。

通常sandboxのGit TLS資格情報とartifact取得401は成功とせず、コマンド限定のホスト実行で取得した。SSL検証を無効化せず、global Git設定・資格情報変更なし。初回の大容量cloneと部分cloneは取得途中で中断し、既存オブジェクト読取り方式へ切り替えた。既存作業の削除・上書きなし。

AGENTS全文、052依頼、050報告・再現付録、051依頼・報告、040報告・技術計画のAPI/世代/受入境界、実コード差分、原検査・追加期待・世代対応を照合した。素材規約・台帳の関係箇所も読取り、素材変更なし。追加AGENTSは存在しなかった。

QA用Godotを今回の `qa-bin/godot.exe` へコピーし、さらに[公式4.7.2 release](https://github.com/godotengine/godot/releases/tag/4.7.2-stable)のWindows ZIPを独立取得してAPIのdigestと照合した。

- 公式ZIP SHA256：`731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953`。
- ZIP内実体と実行実体は同一：`ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`。
- 実版：`4.7.2.stable.official.ed1daf0bf`。Linux CI実体hash `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e` と混同しない。
- Godot子プロセスのAPPDATA/LOCALAPPDATA/USERPROFILE/HOME/XDG各変数を今回の `qa-profile/<変数名>` 配下へ向けた。OS.get_user_data_dir実測も `task-3/qa-profile/APPDATA/Godot/app_userdata/RPG-maker`。環境変更は子のみ。

## 全treeと原条件の保持

`git diff --name-status 329567e79d2a6ace2e4c3b10b729f1e76cd27071 6cc19d158f974e2d97b8b3cab7a00f44b3f952a1` の全51パスを051依頼の許可と照合。削除なし。変更は指定2本番、原codec検査への追加・証拠field、専用wrapper/追加期待/世代表、専用workflow、今回証拠・051状態行/報告・decision-log追記の範囲。decision-log旧本文はbyte prefix一致。

以下は登録051→対象のGit tree差分0：test/.scope-lock/assets/addons/data/world/scenes/scripts/combat、GameSession/IntegratedProgression/FirstRegion、SavedDocument/SavedValueTypes、S1 migration/validation/view/原検査/fixture、旧装備検査、既存他workflow、049証拠/依頼/報告、050報告、040依頼/計画。保護26件は今回実行でも26/26一致。原expectations.jsonもblob不変。

`git diff d813723b3acb2c77658317e7303c83f02f957a5b 6cc19d158f974e2d97b8b3cab7a00f44b3f952a1 -- scripts tools data` は空。049固定→051登録の同3領域も空。固定コードと報告追記/latestを分けた。

原検査diffを行単位で確認し、元112 IDを実行する関数・元assertを除去/緩和していない。run_caseへのdocument hash/size追加は判定の置換ではない。元集合照合後に元件数を採取し追加42件を実行する。追加件数は14 metadata負例＋1正常metadata＋15 context＋7位置形状＋2上限＋1進行加入＋2支給＝42。追加条件は36拒否×6＋6成功×4＋build二回の4＋上限/進行/支給の8＝252。723＋252＝975を手計算と固定期待に照合し、実出力から期待を生成しなかった。

今回Windowsの修正前112観測と修正後の先頭112観測は、追加document_bytes/document_sha256 fieldを除き全項目一致（ID/順/操作/成否/errors/caps/input hash・size/output hash）。修正後154全観測は051原tarのfixed051/codec.jsonと完全一致。Linuxでも固定049の112観測の同等比較、固定051/latestの154全観測が一致した。OS間のgzip byte完全一致は主張しない。

## F1〜F5の独立再実行

| 指摘 | 原版で再現した事実 | 修正版で確認した事実 |
| --- | --- | --- |
| F1 | 当時run_ci.pyのscopeブロックをそのままPythonで実行。99e9d03は成功、138e45eは050依頼書追加だけで「担当外差分:A docs/tasks/050-review-equipment-save-codec.md」。Linux専用main全体をWindowsで実行したとは扱わない | scope_targetはlatest/fixed051の当時scopeを完全SHA99e9d03へ向け、051実装scopeを登録→固定051で別監査。050/051名allowlistなし。無名後続文書treeはexit0、固定範囲外treeはexit1。原049 checkout・原wrapperの112/723/13は別に維持。052文書追加後のlatestは提出CIで確認 |
| F2 | 050付録のnull/version99/missing path/duplicate path/TYPE_OBJECT/unknown key/float path欠落の7件：encode拒否、prepareは全7成功してdocumentあり。23条件で拒否期待7失敗、exit1 | 同じ付録23条件すべて成功。追加14ケースでもprepare/encode双方invalid_types、パス付きerrors、document/bytes/candidateなし、入力native不変。正常metadata・上限上昇/下降後のmetadata再生成、HP0・回復/蘇生0を維持 |
| F3 | null catalogでSCRIPT ERRORを4回出した後ok/documentあり。付録5条件で拒否期待1失敗、exit1 | 同付録5条件すべて成功、警告/エラー0。原追加5context×decode/encode/prepareの15ケース全拒否。独立追加で正常実contextとsession null/int/Dictionary/RefCounted、abilities null/Array/空/不一致の9context×3入口、79条件も全成功。正常3入口は成功、異常24入口はパス付き拒否・document/bytesなし・入力不変 |
| F4 | room1/cell[1,1]でparty=nullとresidents=null：SCRIPT ERROR計9回。拒否は返り3条件assert成功・exit0だが検証失敗として記録 | 同じ付録3条件はexit0かつSCRIPT ERROR/警告0。原追加7形状負例も拒否。原M10位置差分は提示だけ、入力bytes・元値不変、通常位置処理は変更なし |
| F5 | 自作の独立変異で正常対照/同時checks・PASS log=1/空document/同長1byte改変がすべてexit0。不在documentだけexit1。原validatorの穴を再現 | 同じ5試行で正常対照だけexit0、4破損はexit1。別途未変更wrapper self_test全18（control0＋負17件1）、原13も原checkoutで全件一致。実document hash/正sizeと独立固定112/723・154/975の照合が拒否根拠 |

修正前の異常を期待どおり再現した結果と、正常受入のPASSを混ぜていない。全ログに `SCRIPT ERROR|ERROR:|WARNING:|Parse Error` を別走査し、exit0だけでは合格にしていない。修正前context/relocation以外の受入実行に該当なし。

合法進行・reserve加入・HP0・共通支給12→22は050付録progress 9条件と追加正例で維持。全値/型/配列順、元native入力/state/metrics/historyは不変。S1移行直後との差分検査は進行後候補を別拒否し、一般保存検証と分離。audit.generatedとinstancesの一致を外しておらず、future_exampleの任意追加はinvalid_audit。将来入手・倍率の規則を追加していない。

## 実コマンドと実測

cwdはqa-before/qa-afterの対応checkout。PythonはMSI既存runtime `D:/codex/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`、UTF8モード。原予算import600秒、codec/各独立probe120秒、装備240秒、validator子30秒を維持。run_locked_checks内部の各verify300秒も変更なし（外側プロセス全体の待機上限2600秒を、個別verifyの上限として扱わない）。

```text
godot --version
godot --headless --editor --import --quit
godot --headless --path . --script res://independent050.gd -- MODE
  MODE = metadata/context/relocation/progress/shape/catalog
godot --headless --path . --script res://tools/check_equipment_save_codec.gd
python tools/fixtures/equipment-save-codec/run_ci.py --validate-only --checkout QA --output EVIDENCE
  importlibで同じ未変更run_ci.pyをload: validate(QA,EVIDENCE), self_test(QA,EVIDENCE)
  修正版のみ scope_self_test(QA,専用出力)
godot --headless --path . --script res://tools/check_equipment_rules.gd
godot --headless --path . --script res://tools/check_equipment_save_migration.gd
godot --headless --path . --script res://tools/fixtures/equipment-save/legacy_equivalence.gd
python tools/run_locked_checks.py
python tools/check_frozen_files.py
python tools/validate_assets.py --strict
git diff --check
```

codecにはEQUIPMENT_CODEC_EVIDENCEを今回専用出力、旧比較にはRPG_LEGACY_EQ_OUTPUTを今回legacy.jsonへ指定。050付録のgdscriptコードは原報告からそのまま抽出し、QAだけへ配置。self_testは別Pythonプロセスの実exitを検証する。scope self_testはQA Gitの別index/新規未参照treeで実行し提出branchを動かさない。

| 実行ラベル | 上限秒 | 実秒 | exit | 警告/エラー |
| --- | ---: | ---: | ---: | --- |
| version | 30 | 1.079 | 0 | なし |
| import-before | 600 | 37.719 | 0 | なし |
| before-metadata | 120 | 6.266 | 1 | なし |
| before-context | 120 | 3.859 | 1 | あり |
| before-relocation | 120 | 2.547 | 0 | あり |
| import-after | 600 | 39.938 | 0 | なし |
| before-progress | 120 | 2.313 | 0 | なし |
| before-shape | 120 | 1.484 | 0 | なし |
| before-catalog | 120 | 2.219 | 0 | なし |
| before-codec | 120 | 14.359 | 0 | なし |
| after-metadata | 120 | 1.625 | 0 | なし |
| after-context | 120 | 1.625 | 0 | なし |
| after-relocation | 120 | 1.266 | 0 | なし |
| after-progress | 120 | 2.234 | 0 | なし |
| after-shape | 120 | 1.453 | 0 | なし |
| after-catalog | 120 | 2.188 | 0 | なし |
| after-codec | 120 | 16.328 | 0 | なし |
| equipment | 240 | 0.812 | 0 | なし |
| migration | 120 | 27.485 | 0 | なし |
| legacy | 120 | 2.125 | 0 | なし |
| frozen | 30 | 0.078 | 0 | なし |
| before-independent-control | 30 | 0.125 | 0 | なし |
| before-independent-checks-one | 30 | 0.141 | 0 | なし |
| before-independent-document-empty | 30 | 0.125 | 0 | なし |
| before-independent-document-modified | 30 | 0.141 | 0 | なし |
| before-independent-missing-document | 30 | 0.109 | 1 | なし |
| after-independent-control | 30 | 0.14 | 0 | なし |
| after-independent-checks-one | 30 | 0.14 | 1 | なし |
| after-independent-document-empty | 30 | 0.11 | 1 | なし |
| after-independent-document-modified | 30 | 0.109 | 1 | なし |
| after-independent-missing-document | 30 | 0.109 | 1 | なし |
| locked | 2600 | 90.937 | 0 | なし |
| assets | 120 | 6.36 | 0 | なし |
| extra-context | 120 | 1.75 | 0 | なし |

原codec112/723、修正版154/975（原112/723＋追加42/252）、原伝播13、修正版18、scope2が実測一致。S1=61ケース/2828条件、装備=5394＋93条件/400切替、旧比較=142検証/10更新。旧比較出力全byteは原本と一致しSHA256 `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea`。

R-01〜R-08は今回Windows実行で8/8 PASS、全tests_ran=true/parser_failed=false/timeoutなし。素材1154/音15/palette3/font2、問題0。旧異常定義202ケースはローカル再実行しておらず、対象同一SHAのLinux CIの成功確認と区別する。

## 原証拠・Git正規化hashの分離

6cc19dのartifact-sha256.jsonの40項目は、checkoutのCRLF byteをそのままhashせず、`git show 6cc19d158f974e2d97b8b3cab7a00f44b3f952a1:docs/verification/equipment-codec-validation/<path>` のGit blob bytesをSHA256し40/40一致。

| 原archive | file member数 | 原tar.gz SHA256 |
| --- | ---: | --- |
| local-original.tar.gz | 6254 | `ea851d2cf65a1634c4c18e1c8f655077988345ec7760b139e75b58f1311c745b` |
| codec-ci-original.tar.gz | 9294 | `83a42a102f1f10c6395cb2bbd92b509ef5c4f6575767fb4a47e38203dbf40bed` |

各tarを展開改変せず全file memberのraw bytesを読み、対応members.jsonと集合・全SHA256一致。raw-artifact-sha256.jsonの39項目も区別した。15項目はGit blobとraw hash同一、24項目は改行正規化差。そのうち18項目はtar原memberを直接突合し、CRLF→LF後にGit blobと一致。残るcases.md、ci-artifact-check.json、code-ci-all.json、両members.json、existing-checkouts.jsonの6項目はGit blobからCRLFを復元したhashがraw記録と一致したものであり、tar原memberを直接読んだと誤記しない。members.json自身の書式差と、member内容hash不一致を混同しない。

検査初稿でこの6項目すべてをtar内にも存在すると仮定して照合し未解決となった。原bytesとGit blobの対象分類を修正して上のとおり確認した。別の読取り初稿ではarchiveのfixed-codecという存在しないmember名を使いKeyErrorになったため、実一覧のfixed051/codec.jsonへ訂正した。いずれも製品・過去証拠の修正ではなく、失敗初稿を受入成功に数えていない。

今回再実行の生証拠はtask-3/evidence052配下。提出パス制限に従い追加artifactはcommitせず、本報告に実測・hash・再現法を残す。主要rawログSHA256：

- 修正前codec：`870dcd5e5a5cea72b4e13f6d21bbaf5160df048c12d140f3230cbefeacee75ef`
- 修正後codec：`3829b23fc8bf7d701f20827dd438058fb4646774d21a68700aeafc03be7a8c25`
- 修正後metadata：`d791ad4de3d399866c0de6c084e0e91cb277779c93b1db512aacd2dd49725e41`
- 修正後context：`59f6af45f3d6dcc5de756505174ef5d2193768f2c8840b7de36631f364e8e03d`
- 修正後relocation：`6171b95d5f38c23724938c25f8357f0dcc4a9d241a4a4bd8dcaa6f06593b2f72`

## 対象CIとWindows/Linuxの境界

以下は051提出branchの同一6cc19d push、**37/37 job completed/success** を自分でjobs API照合した結果。親の確認だけで代用していない。同じSHAで052branch作成時に生じた別pushはこの37件に混ぜない。

| workflow | run | job数 | 結果 |
| --- | --- | ---: | --- |
| CI | [37715879711](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37715879711) | 3 | 全success |
| 006固定受入と最新回帰 | [37715879701](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37715879701) | 17 | 全success |
| Equipment and Save CI | [37715879706](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37715879706) | 14 | 全success |
| Equipment Codec CI | [37715879724](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37715879724) | 3 | 全success |

`gh run download 37715879724 --repo hiroshitanaka-creator/RPG-maker --dir <今回QA>` で取得した3原artifactは、fixed049=139、fixed051=192、latest=192 manifest項目の全hash一致。各source SHA、公式Linux実体hash、version/保護前/import/codec/保護後の5コマンドの実exit0、予算以内、原log hash、警告/エラーなしを照合。fixed049112/723/13、fixed051とlatest154/975/18＋scope2を確認した。

Windowsは同版実GDScript・原probe・validator/self_test/scopeと回帰検査の実行。Linux実体hash固定wrapper main全体をWindowsで実行したとは扱わない。Linuxの3世代フルwrapperは上記CI原artifactの照合である。workflowはfixed049/fixed051を各完全SHAへcheckoutし、latestは当該提出SHA、contents:read、15分job、import600秒/codec120秒、fail-fast:false、失敗時も保護/証拠upload。skip/continue-on-error/時間上限延長は追加されていない。

## 追加context再現コード

050付録をQA rootのindependent050.gdへ保存後、以下だけを別independent052.gdへ置く。元_initializeがcontext_extraを呼ぶ。`godot --headless --path . --script res://independent052.gd -- context_extra`、120秒、実79条件/exit0/警告0。期待は異常contextの明示拒否と正常context成功という契約から固定した。

```gdscript
extends "res://independent050.gd"

func context_extra():
	var document=base()
	var raw=JSON.stringify(document).to_utf8_buffer()
	var original=var_to_bytes(document)
	for mode in ["normal","session-null","session-int","session-dict","session-object","abilities-null","abilities-array","abilities-empty","abilities-different"]:
		var custom=ctx.duplicate()
		match mode:
			"session-null":custom.legacy_session=null
			"session-int":custom.legacy_session=1
			"session-dict":custom.legacy_session={}
			"session-object":custom.legacy_session=RefCounted.new()
			"abilities-null":custom.abilities=null
			"abilities-array":custom.abilities=[]
			"abilities-empty":custom.abilities={}
			"abilities-different":custom.abilities={"two_handed":{}}
		for op in ["decode","encode","prepare"]:
			var result:Dictionary
			match op:
				"decode":result=C.decode_source(raw,custom)
				"encode":result=C.encode_candidate(document,custom)
				"prepare":result=V.prepare_candidate(document,custom)
			emit(mode+"-"+op,result)
			if mode=="normal":ck(result.ok and result.has("document"),"normal "+op)
			else:
				ck(not result.ok and not result.has("document") and not result.has("bytes"),"reject "+mode+op)
				ck(not result.errors.is_empty() and result.errors[0].target is String,"path "+mode+op)
			ck(var_to_bytes(document)==original,"input unchanged "+mode+op)
```

F5独立変異の再現は、正常codec出力を各回別コピーし、(1)codec.json.checksを1かつcodec.logの「975条件」（原版は723）を「1条件」へ、(2)M09-new-typed/document.gdvを空、(3)同fileの末尾1byteだけXOR 1して長さ維持、(4)同fileを別名へ移動。各コピーに上記--validate-onlyを別プロセスで実行する。元正常証拠・manifestは書き換えない。原版の実exitはcontrol/1化/空/改変/欠落=0/0/0/0/1、修正版=0/1/1/1/1。

## 提出・未実行

変更は052依頼書の状態行（報告済み）と本報告だけ。commit/push後の完全SHA、clean/未push0、同一SHA全CIとリンクは最終応答に記す。052文書でlatestが阻害されないこともそこで確定する。

S3保存I/O/中断復旧、S4通常runtime/報酬/戦闘接続、S5UI/通常公開、実ユーザー保存、電源断、手動legacy-campaign、人間の作品・操作体験の採否は未実施・範囲外。旧異常定義のローカル再実行とLinux wrapperのWindows実行も未実施。これらを今回のS2 F1〜F5の差し戻し事項や実装済みとして扱わない。
