# 064 第4地方の採用原画11枚の保管・記録 報告

## 変更したファイル（全14件）

- `assets/_incoming/owner-2026-10-10-grok-region4/region4-world-map.png`
- `assets/_incoming/owner-2026-10-10-grok-region4/region4-lake-town-exterior.png`
- `assets/_incoming/owner-2026-10-10-grok-region4/region4-room-inn.png`
- `assets/_incoming/owner-2026-10-10-grok-region4/region4-room-item-shop.png`
- `assets/_incoming/owner-2026-10-10-grok-region4/region4-room-weapon-shop.png`
- `assets/_incoming/owner-2026-10-10-grok-region4/region4-room-shrine.png`
- `assets/_incoming/owner-2026-10-10-grok-region4/region4-town-residents-10.png`
- `assets/_incoming/owner-2026-10-10-grok-region4/region4-flower-field-enemies-4.png`
- `assets/_incoming/owner-2026-10-10-grok-region4/region4-lake-enemies-4.png`
- `assets/_incoming/owner-2026-10-10-grok-region4/region4-battle-flower-field.png`
- `assets/_incoming/owner-2026-10-10-grok-region4/region4-battle-lakeshore.png`
- `docs/roadmap-v2.md`（今回の付録B新節のみ）
- `docs/tasks/064-record-region4-art.md`（状態欄のみ）
- `docs/tasks/reports/064-record-region4-art.md`（本報告）

## 基点・範囲・既存作業の保全

- main基点：`a6cb2ebd3d86100b20978bca3503e8ddd4a5d911`。登録commit：`0eb52e4af0d20ea298944713b6ecbaca6b1d6dec`。作業branch：`codex/task-064-record-region4-art`。登録commitは最新mainの直上で、064依頼書1件だけの追加と確認した。
- MSIの独立cloneで実施。063のローカルGitデータを `git clone --no-hardlinks --no-checkout` で独立コピーし、originを正式GitHubリポジトリへ設定して最新main・登録枝・15 incoming refを取得した。別checkoutの作業ツリー・未追跡ファイルをコピーせず、元checkoutへ書き込んでいない。読み取り時の063 checkoutはclean・未push 0。今回の開始時も登録commitと一致し、clean・未push 0だった。
- 最初のネットワーク全履歴cloneは認証制約を承認付き実行で解消したが時間を要したため、上記の独立コピー方式へ移行した。最初のcloneも後に正常終了したが、実作業・検証・pushには使っていない。Gitの所有者警告はコマンド単位の `-c safe.directory=<今回clone>` で扱い、グローバル設定やOS設定は変更していない。
- `AGENTS.md`、素材規約、職業・魔物化の企画書、素材台帳の規定、064全文・末尾の確定事項、062/063の付録B記録・依頼書・報告書を読んだ。今回checkoutのAGENTS/素材規約/先行報告が先行確認版と一致することもGit差分で確認した。指定モデルはGPT-6 Astra／Highだが、実行モデル設定はツールから独立確認していない。
- `gh pr view 34/35 --json state,mergeCommit,headRefOid,statusCheckRollup` で両方MERGED・各74件全SUCCESSを確認。PR #34最終headは `f34efde0fa31e158b2511251a806315af2491d91`、取込は `5116756c7b4814fd8cf5f0886983f1949a1ae6d9`。PR #35最終headは `48f66b5324fde4edcce362804e6f5aed0ca78bab`、取込は今回基点と一致。
- 原画の保管と文書記録だけを実施。ゲーム組込み・台帳追加・原画加工・改名・新設定なし。親担当のREADME・decision-log・063状態、本番code/data、registry、project.godot、CI・保護・検査器を変更しない。

## 原画11枚の実測・実閲覧

固定取出し元：`incoming/owner-2026-10-10-grok-region4-shrine-v2` / `bcac33726578b80d2ce3e9d0bd3678c306c6bf1f`。folder tree `5a9e80566b8982a419db9f0ba45dd90d4ffc7419` は指定11PNGだけだった。各blobを `git cat-file blob <blob>` のバイナリ出力で同一パスへ書き出し、原画のデコード・再エンコード・再保存をしていない。

全11枚の実画素を原ファイルから表示して閲覧した。下表のSHA-256とbytesは全件依頼提示値と一致。全枚1168×784（73:49、約1.4898:1）。2戦闘背景の提示3:2とは厳密に異なるため、付録Bにも実寸を併記した。16:9化は後の組込み時の想定のみで、切抜きは行っていない。

| 原画 | SHA-256実測 | bytes実測 | 幅×高さ | 閲覧結果 |
| --- | --- | ---: | --- | --- |
| `region4-world-map.png` | `f732c4ea34b63e9554eed19094b837e5b6c3ae87dce567abc90aae5898f33647` | 1726130 | 1168×784 | 夕空、紫と白の花原、白い幹の林、霧に隠れた湖の奥、湖畔の町と桟橋を確認。 |
| `region4-lake-town-exterior.png` | `8ec72d2497ded1ed1c60c80ebf8c975995aa3f9526090fabac4f39e54457012d` | 1842390 | 1168×784 | 左上の宿、左の道具屋、三日月の祠、下の武器屋、噴水と花壇・水場、右下の花畑と木工作業場、右上の桟橋、左下の花の門を確認。 |
| `region4-room-inn.png` | `5bbe986b3e58e7cae1ed910662c2608f8c139f429c194c464601c674368a71a1` | 901924 | 1168×784 | 奥の普通・幅広・巣・水を張った石の4寝床、左の受付、右の丸卓と4色の椅子、湖の窓、下中央の広い入口を確認。 |
| `region4-room-item-shop.png` | `5b6d56b2d21ae7f1995ed42c4fe0c4b5de7914a1feb8f0085638b0001e852330` | 964613 | 1168×784 | 奥の薬瓶と乾燥花の棚・受付、右の鉢植え・袋・籠の台、下中央の入口を確認。 |
| `region4-room-weapon-shop.png` | `dd618aeea7d71776ced9a2e3616047c23b449b4a6266f52b439e4fe4daa9af6b` | 1310750 | 1168×784 | 奥の剣・槍・盾・鎧、左の弓、右の大きな籠手と異なる形の鎧、中央の2台、下中央の両開き入口を確認。 |
| `region4-room-shrine.png` | `636ebaacaef8fcce7a0613ace584356fa040e3fd06f6de42eee4f45dfd0731f4` | 1165890 | 1168×784 | 奥中央の三日月の白い祭壇と掛け布、ろうそく、敷物2枚、壁沿いの鉢植えと壺、下中央の入口を確認。 |
| `region4-town-residents-10.png` | `cf79e9e12af2847759ede03aa7feb0eec9517180f3d4db704a7692daebac1fa3` | 860784 | 1168×784 | 横一列に10人。羽、獣の耳と尾、背中の殻、葉、うろこ・尾、透ける体、発光輪郭、青白い肌などを確認。名前・役割は決めていない。 |
| `region4-flower-field-enemies-4.png` | `2b9d4ba8c43cd5bc322102da479be7204305c535ab120bde0e4a18180faa9ceb` | 971134 | 1168×784 | 左から発光する蛾、花をまとった狼、目のある花、蝶の群れによる人影の4体を確認。 |
| `region4-lake-enemies-4.png` | `0d1ac4099b7c27f4ee1462f982cf0ac851d2b91ac437205eeac8d245313232f9` | 889700 | 1168×784 | 左から発光するクラゲ、睡蓮を載せたカエル、灯りを持つ霧の人影、葦の大蛇の4体を確認。 |
| `region4-battle-flower-field.png` | `1d45d98c0df92e9a4e3f6cdac2f9b2f20b0ecb266cbe77aa41e2cb392a26d259` | 1314939 | 1168×784 | 夕空、遠い丘、白い幹の林、手前の低い花原を確認。 |
| `region4-battle-lakeshore.png` | `9e25c8f438612780b0d906fb0e15707ed002d36476e5f58240b1f8321e336716` | 1270386 | 1168×784 | 夕空と霧の湖、建物なし、手前の短い草と小石、左右の葦と睡蓮を確認。 |

武器屋は完全値 `dd618aeea7d71776ced9a2e3616047c23b449b4a6266f52b439e4fe4daa9af6b` と一致し、誤った短縮表記は使用していない。入口の「幅2」・宿の「2倍の幅」は依頼時の想定として記録し、画像からマス単位の実装・通行を検証したとは扱っていない。名前・役割・正式名称は原画の採用とは区別する。

| 原画 | 採用Git blob SHA |
| --- | --- |
| `region4-world-map.png` | `c0630e4acffbb28c19baa9e37567707a4649e8ac` |
| `region4-lake-town-exterior.png` | `674ecc2f3877da2615ad6fb480e691e7748ffa0a` |
| `region4-room-inn.png` | `1355059389318d36481a11f7998a671933e28867` |
| `region4-room-item-shop.png` | `2aa513c0a9466f1a90794aa59ed89c275125bad2` |
| `region4-room-weapon-shop.png` | `e01341a27053a198332772ea10815ece2f449c89` |
| `region4-room-shrine.png` | `a4d2b753e0b58b4331b44d5468ca0f2f05000206` |
| `region4-town-residents-10.png` | `bf02444bcb69b94585c5e479f37cf4ed6f2c82ca` |
| `region4-flower-field-enemies-4.png` | `e6a883b1e328244bdf0575ea2a9ffd5d31721a27` |
| `region4-lake-enemies-4.png` | `6b7af68641acfd57984bce2184a37d099eb3dc5d` |
| `region4-battle-flower-field.png` | `a6a36b058634bf22f7e4742487e7fd6ed583fe87` |
| `region4-battle-lakeshore.png` | `20cdec9e3a8a9854ca9b9e6586aef93ce0d2e83e` |

## incomingの積層履歴と不採用4枚

`git merge-base <main基点> <固定元SHA>` は `87f4e66ed64f2ae9a92538acb9716c6a01f5cb27`。`git log --reverse --format='%H %P %s' --name-status <共通祖先>..<固定元SHA>` で15本の単一親の連続履歴を確認した。最初の11 commitは各PNG追加、最後の4 commitは室内の描き直し置換である。以下は履歴順の実在ref・完全SHA。旧室内4枚を含むため、どのincomingもmerge/cherry-pickしていない。

| 順 | incomingブランチ | 先頭完全commit SHA |
| ---: | --- | --- |
| 1 | `incoming/owner-2026-10-10-grok-region4-map` | `671c33c2f1aea8fda961c291dcb6080b7da7d117` |
| 2 | `incoming/owner-2026-10-10-grok-region4-town` | `a5be36b8ee6a9283d6e13d3dda9dc5f7150439a9` |
| 3 | `incoming/owner-2026-10-10-grok-region4-flower-enemies` | `fb95a902f798bad9130ef61490e3728dfb6741a5` |
| 4 | `incoming/owner-2026-10-10-grok-region4-lake-enemies` | `983cbc30aa90a865fafabbf882e449231798a7b5` |
| 5 | `incoming/owner-2026-10-10-grok-region4-battle-flower` | `56f7d70d24ea54828f0d036d19e9d7997c4d0cbd` |
| 6 | `incoming/owner-2026-10-10-grok-region4-battle-lakeshore` | `9447e69e70dc7ebcd7a7ba9b637d3b73d1babad5` |
| 7 | `incoming/owner-2026-10-10-grok-region4-inn` | `b040ee4ebda3bb113248b84a4875a0a793d4ca3c` |
| 8 | `incoming/owner-2026-10-10-grok-region4-item-shop` | `8b6201efd8777cb0b639461f3ac2a12ea66a9d8a` |
| 9 | `incoming/owner-2026-10-10-grok-region4-weapon-shop` | `373731eb5f1cda19bfc9a8d762e1a8f1655588bf` |
| 10 | `incoming/owner-2026-10-10-grok-region4-shrine` | `ccc2033f7a8ca3cb0dcd947c150505449ee0c68d` |
| 11 | `incoming/owner-2026-10-10-grok-region4-residents` | `23fec0558a494a369537f82d69af3a797316faed` |
| 12 | `incoming/owner-2026-10-10-grok-region4-inn-v2` | `446e01604fb3bb136915617054c92ecf45adef2c` |
| 13 | `incoming/owner-2026-10-10-grok-region4-item-shop-v2` | `577cb182d60d69df42f28fcf20f8348edd4938bd` |
| 14 | `incoming/owner-2026-10-10-grok-region4-weapon-shop-v2` | `548f95b4a8dfb8dd7d7dbc06d41500169dcc0d8b` |
| 15 | `incoming/owner-2026-10-10-grok-region4-shrine-v2` | `bcac33726578b80d2ce3e9d0bd3678c306c6bf1f` |

不採用の旧室内はGit blobを読み取り照合しただけで、作業ツリーへ保存・追加していない。

| 元ブランチ | 元完全commit SHA | 旧版SHA-256 | 旧版bytes | 採否 |
| --- | --- | --- | ---: | --- |
| `incoming/owner-2026-10-10-grok-region4-inn` | `b040ee4ebda3bb113248b84a4875a0a793d4ca3c` | `daa898e4ac839c77b2965b12f4b19b8c375298c79c64472f7ef6472da15321d3` | 1194852 | 不採用・未取り込み |
| `incoming/owner-2026-10-10-grok-region4-item-shop` | `8b6201efd8777cb0b639461f3ac2a12ea66a9d8a` | `2abafe5222b3c40a39153b3383c05b3eaba789f41574880729fe1e29053aa209` | 1335094 | 不採用・未取り込み |
| `incoming/owner-2026-10-10-grok-region4-weapon-shop` | `373731eb5f1cda19bfc9a8d762e1a8f1655588bf` | `cf3083f7c03d11bc5c6d655e8bf9cdf069617027b9e573c3b510ef1804d241ae` | 1306215 | 不採用・未取り込み |
| `incoming/owner-2026-10-10-grok-region4-shrine` | `ccc2033f7a8ca3cb0dcd947c150505449ee0c68d` | `714a555993e4a73b935bed0595521cda2fda413f3f7971cb00d194174a541662` | 1156000 | 不採用・未取り込み |

15 incoming commitについて `git merge-base --is-ancestor <commit> HEAD` を実行し、すべてexit 1（祖先でない）を確認した。採用11枚だけを固定先頭から抽出し、追加を1回のcommitへまとめる。全incoming枝のリモート先頭を `git ls-remote --heads origin 'refs/heads/incoming/*'` で保存し、push前後にも照合する。リモートへ書く対象は064の作業branchだけで、incomingを削除・上書き・改変しない。

## 文書記録

`docs/roadmap-v2.md` の「付録B追記：第4地方の採用原画（owner-2026-10-10-grok-region4）」を063の節に続けて追加。11パス・取出し元branch・固定完全SHA・SHA-256・bytes・寸法・内容・用途、描き直し4枚の採用と旧版4枝/完全SHA/旧hashを記録した。原画の採用日、入口の幅2という依頼、未決事項、後続の16:9化想定も残した。

既存roadmapは今回の追加節だけを除くと登録commitのbytesと一致。064依頼書も状態行の置換を戻すと登録commitと一致。町・地方の正式名、住人の名前・役割・台詞、敵の正式名・強さ、湖の奥の場所は未決のまま保持した。

## 実行コマンドと検証結果

2026-10-10、既存ローカルPython 3.13.5 / Godot 4.7.2を使用。Godotの既存実行体2本とself-contained指定 `_sc_` を専用checkout内の `.tools/godot/4.7.2/` へコピーし、ゲーム保存先も今回のタスク内へ分離した。主実行体SHA-256は `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`。新規ソフト導入・OS設定変更なし。

| コマンド・照合 | 結果 |
| --- | --- |
| `godot --version` | `4.7.2.stable.official.ed1daf0bf` |
| `godot --headless --editor --import --quit` | 初回でexit 0、SCRIPT ERROR / ERROR / WARNING / Parse Errorなし |
| `python tools/validate_assets.py --strict` | exit 0、画像1154件・音15件・パレット3件・字体2件、問題なし |
| `python tools/check_frozen_files.py`（検証前後） | 両方exit 0、保護26/26一致 |
| `git cat-file blob <blob>` とSHA-256/bytes/PNG寸法の読み取り | 採用11枚すべて指定値一致。旧4枚と区別 |
| `git ls-tree -r --name-only <固定元SHA> -- <folder>` | 指定11PNGだけ、folder treeも指定値一致 |
| `git merge-base --is-ancestor <incoming commit> HEAD`（15件） | 全件exit 1、祖先への混入なし |

R-01〜R-08は `.scope-lock/spec.lock.json` のverify文字列をそのまま、各300秒上限で順次実行した。既存 `tools/run_locked_checks.py` の `judge_output` で判定し、ログはタスク内の `local-evidence/` に保存。追跡済み検証JSON・条件・時間上限・判定器は変更していない。

| 要件 | verifyコマンド | 結果 |
| --- | --- | --- |
| R-01 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_job_data.gd -gexit` | PASS、exit 0、2 tests / 765 assertions |
| R-02 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_job_actions.gd -gexit` | PASS、exit 0、5 tests / 946 assertions |
| R-03 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_ability_slots.gd -gexit` | PASS、exit 0、2 tests / 73 assertions |
| R-04 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_monster_form.gd -gexit` | PASS、exit 0、1 tests / 293 assertions |
| R-05 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_battle_loop.gd -gexit` | PASS、exit 0、2 tests / 79 assertions |
| R-06 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_save_roundtrip.gd -gexit` | PASS、exit 0、2 tests / 87 assertions |
| R-07 | `godot --headless --path . --script res://tools/smoke_first_region.gd` | PASS、exit 0、A01〜A14全14件PASS |
| R-08 | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://test/unit -gprefix=test_ -gexit` | PASS、exit 0、17 tests / 2302 assertions |

全GUT結果はfailed_assertions=0 / pending=0 / invalid=false。全要件でparser_failed=false / timed_out=false / failure_messages=[]。importによって今回の専用checkoutに生成された追跡外UID2本だけを除去した。ユーザー既存ファイルは削除していない。

commit前後に14パス限定・原画元bytesとステージ/commit blobの一致・11枚追加が単一commit・既存文書不変・祖先非混入・`git diff --check` を再点検し、push/PRの実測結果と完全headをPR本文および親への引継ぎに記録する。

## 未達・未検証と引継ぎ

この報告commit時点では最終headのGitHub CIは未実行。最終headのdraft PRを1件作成して返し、全CIの長時間監視・mainマージ・READMEとdecision-logと063状態の親担当更新・main取込後の再照合は親へ引き継ぐ。過去headのCI成功を今回headの成功として扱わない。

原画保管・文書記録・ローカル検証の範囲に追加承認を要するブロッカーはない。今回の全14ファイル以外は変更しない。ゲーム組込み・人間プレイテスト・未決事項の決定は今回の範囲外。
