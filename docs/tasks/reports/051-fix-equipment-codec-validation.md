# 051 保存codecの不正入力・証拠検証 修正報告

## 開始状態と実行環境

051登録 `329567e79d2a6ace2e4c3b10b729f1e76cd27071`、050提出 `05b6cb9ef4dc0072803824d4808014f1af049d1a` から指定branchで実装・修正区分だけを実行。追加委譲、親の監督・依頼書作成の代行なし。既存050 checkoutは開始・終了観測とも050提出、未commit差分0、追跡refに対するahead0。既存checkoutは読取りだけ。050報告に挙がった既存10/04 task/repo（main 4f5568e）とtask-3/repo（main 5f1c2ba）も自分で読取り確認し、未commit0・追跡refに対するahead0/behind0。existing-checkouts.jsonに観測を保存した。remote全branchの最新性をこの観測だけで断定しない。

新規 `task-2/impl051`（既存050オブジェクトを読取り利用）と独立remote clone `task-2/fix051` を用意。両方の開始HEADは051登録、未commit/未push0。fix051で修正前専用QA、修正後は別 `qa-fixed051` を完成コードSHAへdetachして実行した。既存アプリやユーザー保存を操作せず、APPDATA/LOCALAPPDATA/USERPROFILE/HOME/XDG各変数は子プロセスだけ `task-2/qa-profile/` へ指定。実Godotのuser dirもこの配下とlogで確認した。

MSIのQA専用Godotを自分で実在・hash・版確認後、今回workspaceのqa-binへコピーした。版 `4.7.2.stable.official.ed1daf0bf`、Windows実体SHA256 `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`。Linux専用wrapperのmainをWindowsで全実行したとは扱わない。ローカルは同版Windowsの実GDScript、証拠validator、別Python実exit伝播、Git scope検査。Linux実体・全wrapperは後述の実GitHub CIとartifactで確認した。

通常sandboxのGitHub資格情報エラーはホスト側の既存資格情報による接続で解消。Git object書込みが一度Permission deniedとなったcommitも、コマンド限定safe.directoryのホスト実行で完了。グローバル設定・資格情報は変更していない。途中の環境切断通知後もシェル/Git/ファイル実アクセスを確認して継続した。

AGENTS全文、051全文、050報告全文、049依頼/報告、040設計のAPI・型・検査世代・M09〜M12、S1実API、素材規約・台帳・体験仕様の関係箇所を確認。checkoutの追加AGENTS/.agents/skillsはなし。catalogのverification-before-completionを使用し、実結果確認前に成功としない。素材・作品規則・物語は変更していない。

## F1〜F5の変更前／後

| 指摘 | 自身の修正前再現 | 修正後の保証と証拠 |
| --- | --- | --- |
| F1 範囲監査の世代混同 | 原wrapperの同じpredicateと定数を登録SHAの全tree差に適用し、050依頼/報告と051依頼の追加を担当外として拒否。これはscope部分の再現で、WindowsでLinux専用mainを実行したものではない | 当時scopeを完全SHA99e9d03へ固定。固定049は当時本番・原検査・期待・wrapperを一切変えず実行。latestは現在の全動作/件数/警告/証拠/伝播を検査。別051 scopeは登録→固定051の許可範囲を監査。無名の後続文書追加を含む実Git tree正例exit0、当時側の担当外追加tree負例exit1。050/051名のallowlist追加なし |
| F2 不正metadataをprepareが消す | 050付録のnull、version99、欠落path、重複path、TYPE_OBJECT、未知キー、float記述欠落の全7件。encode拒否、prepare成功documentあり。拒否期待7失敗、exit1 | metadata構造検証をS2 validatorへ共通化し、native値のdescribeとの一致をprepareの変更前に照合。全7をprepare/encodeともinvalid_types、パス付きerrors、document/bytesなし。050付録23条件exit0。上限変更後の再生成は維持し、型付き上限上下・HP0・回復/蘇生0を追加正例で確認 |
| F3 catalog=nullでSCRIPT ERROR後に成功 | 050付録null-catalogで4回SCRIPT ERROR、ok/documentあり、exit1 | sessionとcatalogの有効性、BattleCatalog型、既存定義/errorsを参照前に確認。null含む5context×decode/encode/prepareを明示拒否、SCRIPT ERRORなし。通常入口/旧catalog定義は変更なし。050付録5条件exit0 |
| F4 形状検査前の位置処理 | room=1/cell=[1,1]にparty=null、residents=null。拒否は返るがSCRIPT ERRORあり。exit0を成功に数えない | 新codecでschemaと位置処理が使う人物ID/住人cellの形状を先に確認。元2件＋5形状負例をパス付き拒否、成功document/bytesなし、警告/エラーなし。位置処理・FirstRegionは不変。原位置補正差分と原入力不変も維持。050付録3条件exit0 |
| F5 証拠完全性 | 原正常対照、checksとPASS logを同時に1条件へ変更、M09-new-typed/document.gdvを空に変更、全3件が原validator exit0 | 原112/723と追加42/252を独立固定期待で照合。producerが返されたnative documentのhash/sizeを観測し、wrapperが実bytesと照合。元13実exit伝播に同時条件偽装・空・同長改変・size・hashの5件追加、計18件（control0/負17件1）を全実行。欠落は元13でも拒否。後付けmanifestで破損を追認しない |

prepareの入力は変更前metadataとnative値が整合した候補に限り、コピー上で上限だけを再計算する。encode/decodeは元の型・値・配列順比較とraw bytes保持を維持。S1 validate_newは元保存→移行直後の差分照合として不変で、進行後一般検証と分離している。

## ケース・期待・原条件の保持

元expectations.jsonはblob/SHA256不変（`04798ce7395d0952cdbfb19f37cc2e5c49090def2b51805384aa511dda29d3ab`）。元112ケースを先に実行して723条件を別に採取し、原ID/順序/操作/成否/errors/caps_changes/input hash・size/output hashが修正前と全一致した。producer証拠のdocument hash/sizeの追加だけを別fieldとして比較した。

修正版は追加42ケース/252条件、合計154/975。追加期待は手書き `validation-expectations.json`、全ID・操作・固定期待・実成否・各入力hash/sizeは [cases.md](../../verification/equipment-codec-validation/cases.md) と原codec.json。成功document20件、encode実物9件を保存。全成功・全拒否でnative入力/state/metrics/history/catalog不変を検査する。

050の合法進行・reserve加入・HP0・全値/型/順序往復、共通支給12→22も追加正例と付録再実行で成功。audit.generatedと現在instancesの集合一致は維持し、future_example任意個体はinvalid_auditで拒否。未採用の将来入手経路や係数は追加しない。

追加検査の初稿は共通支給に元保存にないmetricsを混ぜてS1の厳密差分契約に拒否され、条件数の手計算にも誤りがあった。正規の元保存対応候補に直し、各checkを数えて独立期待を252へ訂正した。製品のS1を緩めたり実出力から期待を再生成したりしていない。失敗初稿logもarchiveに保管した。

世代分類の全群対応は [generations.md](../../../tools/fixtures/equipment-save-codec/generations.md)。原112/723・原13伝播・通常未公開条件は当時固定049にも全て残る。修正版固定051とlatestにも動作継続を個別に適用し、固定成功で最新成功を代用しない。

## 固定コード・実コマンド

- 固定049：`99e9d03d4e095b4627b510efd4806f82276617c9`（当時wrapperを含む原本）。登録051のscripts/tools/dataはこのSHAと同一blob。
- 固定051完成コード：`d813723b3acb2c77658317e7303c83f02f957a5b`。
- 専用CI接続提出：`361009af03205c969ced2b33495444df2882c655`。完成コード→このSHAのscripts/tools/data差分0。最終報告/証拠追加後も同じ不変照合を行う。

WindowsのGodotは上記qa-bin実体。全実argv・cwd・時間・exit・log hashはcommands.jsonl/local-summary.json、各原logを保管した。

| コマンド | 予算 | 実結果 |
| --- | --- | --- |
| Godot `--headless --editor --import --quit` | 600秒 | 登録QA36.281秒、固定051 QA80.422秒、exit0・警告/エラー0 |
| Godot `--headless --path . --script res://tools/check_equipment_save_codec.gd` | 120秒 | 変更前112/723 exit0、固定051154/975、16.391秒、exit0・失敗0・警告/エラー0 |
| 050付録 `--script independent050.gd -- metadata/context/relocation/progress/shape/catalog` | 各120秒 | 変更前不備再現。変更後23/5/3/9/17/36条件、全exit0・失敗0・警告/エラー0 |
| Python原/修正版run_ciの`--validate-only`とself_test | 各子30秒 | 原13保持、修正版18すべて期待exit一致。scope2件も一致 |
| Godot `res://tools/check_equipment_rules.gd` | 240秒 | exit0、5394＋93条件、400切替 |
| Godot `res://tools/check_equipment_save_migration.gd` | 120秒 | exit0、61ケース/2828条件 |
| 専用出力指定Godot `res://tools/fixtures/equipment-save/legacy_equivalence.gd` | 120秒 | exit0、142検証/10更新、以前の原全文とbyte一致。SHA256 bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea |
| Python `tools/run_locked_checks.py` | 各verify300秒 | exit0、R全8 PASS、tests_ran=true/parser_failed=false/timeoutなし。各生logとscope-lock-current.jsonを今回証拠へコピー |
| Python `tools/check_frozen_files.py` | 30秒 | 固定QA前後exit0、保護26/26一致 |
| Python `tools/validate_assets.py --strict` | 120秒 | exit0、画像1154/音15/palette3/font2、問題0 |
| `git diff --check`、新wrapper Python compile | — | 成功 |

## 変更一覧と保護

変更は `scripts/game/equipment_document_validation.gd`、`scripts/game/equipment_save_codec.gd`、`tools/check_equipment_save_codec.gd`、`tools/fixtures/equipment-save-codec/run_ci.py`、新validation-expectations.json/generations.md、`.github/workflows/equipment-codec.yml`、新今回証拠、本報告、051状態行、decision-log今回末尾だけ。

test/.scope-lock/addons/原画・素材/data、既存他workflow、旧043〜046 wrapper、S1公開API/原検査/fixture、SavedDocument/ValueTypes、GameSession通常入口、FirstRegion、049過去証拠/報告、040計画/他依頼は変更なし。全tree差の限定と保護26、旧比較全文、完成固定→最終scripts/tools/data不変をsource-preservation.jsonで確認。importで生成された担当外uidは今回workspace内の一時証拠へ退避し、成果物としてcommitしていない。

## CIと証拠

専用CI接続提出 `361009af03205c969ced2b33495444df2882c655` のpush全4workflow・**37/37 job completed/success** をGitHubから確認。PR実行は今回作っていない。

| workflow | run | job数 | 結果 |
| --- | --- | --- | --- |
| 006 固定受入と最新回帰 | [37714045060](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37714045060) | 17 | 全success |
| CI | [37714045047](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37714045047) | 3 | 全success |
| Equipment Codec CI | [37714045106](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37714045106) | 3 | 全success |
| Equipment and Save CI | [37714045067](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37714045067) | 14 | 全success |

専用codecの3原artifactを取得し、公式Linux実体hash、原5コマンドの実exit/log hash/予算、全結果、manifestを自分で照合。固定049139、固定051192、latest192エントリの全hash一致。固定049の112/723全結果は049保存原本と一致。固定051/latestの154/975全結果とソースhashが一致し、元112観測は追加document証拠fieldを除いて原本と一致。原13、修正版18、範囲2件の全実exitが期待に一致する。

最終報告/証拠commitのpush全CIは最終応答で完全SHA・各run・全job終了を改めて確認する。完成コード/fixture/wrapperはd813723から変更していない。

ローカル生証拠はlocal-original.tar.gzに原入力・全document/encoded bytes・結果・log・実exit・付録・scope・R・旧比較を保存し、各tar.gz.members.jsonで全memberを照合する。原codec結果と読み取り用summary/logも併置する。CI原artifactは別archiveとして保存し、Linux実行とWindows実行を混ぜない。

## 未実行・境界

S3保存I/O取引・復旧、S4通常runtime/報酬/戦闘接続、S5 UI/公開、実ユーザー保存、電源断、手動legacy-campaign workflowは今回範囲外・未実行。WindowsでLinux hash固定wrapper main全体を実行していない。旧異常定義202のローカル再実行はしておらず、同一提出SHAの既存実CIで確認する。人間による作品・操作体験の採否はこの機械検証から推測しない。main書込み/merge、新PR、強制push、削除、履歴改変なし。
