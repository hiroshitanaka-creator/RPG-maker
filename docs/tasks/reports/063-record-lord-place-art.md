# 063 4体の主の居場所の採用原画保管・記録 報告

## 変更したファイル（全7件）

- `assets/_incoming/owner-2026-10-10-grok-lord-places/lord-place-undead-archive.png`
- `assets/_incoming/owner-2026-10-10-grok-lord-places/lord-place-bird-snow-peak.png`
- `assets/_incoming/owner-2026-10-10-grok-lord-places/lord-place-spirit-frozen-lake.png`
- `assets/_incoming/owner-2026-10-10-grok-lord-places/lord-place-dragon-sky-island.png`
- `docs/roadmap-v2.md`（今回の付録B追記節だけ）
- `docs/tasks/063-record-lord-place-art.md`（状態欄だけ）
- `docs/tasks/reports/063-record-lord-place-art.md`（本報告）

## 基点・作業範囲

- main基点：`5116756c7b4814fd8cf5f0886983f1949a1ae6d9`。依頼登録：`6105c0e43493cdbbbb86564c5d432d0f66553a41`。作業branch：`codex/task-063-record-lord-place-art`。
- MSIのWindowsローカル環境で独立cloneを使用。開始時HEADは依頼登録と一致、未コミット変更なし・未pushコミット0。元の既存checkoutには変更・未追跡ファイルがあることを読み取り確認したが、この作業では書き込んでいない。元branchにはupstream設定がなく、未push数は取得不能だった。
- 依頼指定はGPT-6 Astra／High。実行モデルの設定はこの作業のツールから独立確認していない。
- `AGENTS.md`、`docs/asset-spec.md`、職業・魔物化の企画書、素材台帳の規定、063依頼書全文と末尾の確定事項、062付録B・報告、`docs/design/monster-job-unlock.md` を確認。checkout内に `.agents/skills` はない。
- 先行PR #34はMERGED、取込commitは上記main、最終head `f34efde0fa31e158b2511251a806315af2491d91` の74 checksがすべてSUCCESSと `gh pr view 34 --json state,mergeCommit,headRefOid,statusCheckRollup` で独立確認した。062の親受入と取込完了を優先して開始した。
- 採用PNGのGit blobだけを同じパスへ書き出した。画像加工・改名・ゲーム組込み・命名・仕様変更・地域4原画の取込みは行っていない。`docs/tasks/README.md` と `docs/decision-log.md`、registry、project.godot、保護・CI・検査器は不変。

## 原画の実測・閲覧

4枚すべての実画素を表示して閲覧した。指定内容と矛盾なし。全件1168×784。元Git blob・保管後PNG・ステージblobのbytesは一致し、SHA-256・バイト数とも依頼提示値と一致した。

| 原画 | SHA-256実測 | bytes実測 | 閲覧で確認した内容 |
| --- | --- | ---: | --- |
| 不死の主の書庫（描き直し版） | `fa64f976a79736c0084fc41eeaa5ac98b3e0c748fff3c206116b84d4a880b4af` | 1349538 | 下中央の崩れた入口、砂色の床、壁沿いの本棚と崩れ、開いた本の石机、散らばる紙と巻物、奥の円い跡。主は描かれていない |
| 鳥の主の雪山の頂 | `fee0b810ddb04bef46126e99c4dd2a9ed6cf2f9dd1a5c69da877ab530bccacf2` | 1714744 | 下中央の山道、雪の広場、奥中央の段付き氷台、崖と雲海、左上の火山。主は描かれていない |
| 精霊の主の凍った湖 | `71dde1c4300826cf444f65f06b8907c55fe051f8ca8d89b029f3ff8b07f23ee4` | 2068322 | 下中央から円い氷へ続く白い道、暗青色の薄い氷、周囲の針葉樹。主は描かれていない |
| 竜の主の空に浮かぶ岩の島 | `bdf3eaf320df2d8b793367b43f7a5f6981e0eee1d52b1b955c3f306bd2860fe7` | 1541367 | 手前の広い草地、奥へ続く土の道、上へ突き出た岬、周囲の浮き岩と雲。主・飛行船は描かれていない |

## 出典と除外履歴

`git fetch` で5つのincoming refを取得し、完全SHAを固定した。各refと指定commit・blobが一致。`git merge-base <main基点> <commit>` は全5本とも `87f4e66ed64f2ae9a92538acb9716c6a01f5cb27`。この共通祖先から各先頭への `git diff --name-status` は、指定folder内のPNG1枚の追加だけだった。

| 元ブランチ | 完全commit SHA | blob SHA | 採否 |
| --- | --- | --- | --- |
| `incoming/owner-2026-10-10-grok-lord-undead-archive-v2` | `018df0a75711e68743835a7a0045723c954870b9` | `d57777e3f454179ebdc98e4bede9b25119f052dc` | 採用・原bytes保管 |
| `incoming/owner-2026-10-10-grok-lord-bird-snow-peak` | `7a6bebd7b6eda5ff5431d45b891ae585401c0028` | `66ffacedc6ab2c31dbe945b5c04ab549d4c9d852` | 採用・原bytes保管 |
| `incoming/owner-2026-10-10-grok-lord-spirit-frozen-lake` | `3ddfa356650221a4dfe7a28c58b38db290ce4537` | `1dc052f9138aa09e09e7cf7162efc47f3f46d799` | 採用・原bytes保管 |
| `incoming/owner-2026-10-10-grok-lord-dragon-sky-island` | `f0c32aeef5d97facbe70b8151968733fde50cb0a` | `767bac061c9e72ec336324d6447baa3c20f8c8bb` | 採用・原bytes保管 |
| `incoming/owner-2026-10-10-grok-lord-undead-archive` | `046de0555195ababbf98ea0baa6a8b540c98ee4e` | `5f37366a4236ec27e6d5aa5910f96b33570fd7fe` | 不採用・未取り込み |

旧書庫の先頭blobは読み取りだけで照合し、SHA-256 `06ad087c7c06d5f8595210dea0b24b4563c8c6830a6978127eac2cbff7bc0e82`、1,426,975 bytes、1168×784を実測した。旧画像は作業ツリーへ保存せず、閲覧もしていない。

旧branchの履歴は先頭の正味差分と分けて確認した。`4f08671170ddb6340e432c1ad1cb897ca2f2082a` で同名ファイルを追加（`git cat-file -s <commit>:<path>` は200 bytes）、`2b79145b699e7110b471d2c1708fe9780896d619` で削除し、`046de0555195ababbf98ea0baa6a8b540c98ee4e` で旧PNGを追加していた。これらの履歴をmerge/cherry-pickしていない。旧先頭は作業HEADの祖先ではなく、元refを削除・変更していない。

保管folderとステージの対象は採用4枚だけ。書庫は `fa64f976…b4af`、旧 `06ad087c…0e82` と異なる。200バイトファイルは混入していない。

## 文書記録

`docs/roadmap-v2.md` の「付録B追記：4体の主の居場所の採用原画（owner-2026-10-10-grok-lord-places）」を062の節の後へ追加。4パス・元branch・完全commit・SHA-256・bytes・内容・一枚絵背景の用途・採用日・書庫redo採用と旧版除外を記録した。

主の絵は採用済みbatch4から別に重ね、鳥・竜の主に付属する岩も主の絵ごと重ねる。空の島には飛行船も重ねる前提を記録。空に浮かぶ岩の島はClaude案を依頼者が採用したこと、4場所の呼び名・3場所への行き方・戦闘実装時期は未決であることを保持した。新しい命名やゲーム実装済みの主張はしていない。

登録commitのroadmap bytesから今回の追加節だけを除くと完全一致。063依頼書も状態欄の置換を戻すと登録commitと完全一致する。

## 実行コマンドと結果

2026-10-10、既存ローカルPython 3.13.5とGodotを使用。Godot実行体2本と既存のself-contained指定 `_sc_` を専用checkoutの `.tools/godot/4.7.2/` へコピーした。実行体SHA-256は `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`。OS設定変更・新規ソフト導入なし。Godotのエディタ保存先・ゲーム保存先はタスク内へ分離した。

初回importはexit 0だったが、エディタキャッシュの保存先へ書き込めずERRORが出たため不合格とした。062と同じ `_sc_` を補って再実行し、下記の成功を確認した。エラーの無視や検査の変更では解決していない。初回ログは作業ディレクトリの `local-evidence/import-initial-failed.log` に保存した。Git fetchのloose object書込みエラーも、同じrefsをpack形式で取得することで解消した。

| コマンド・照合 | 結果 |
| --- | --- |
| `godot --version` | `4.7.2.stable.official.ed1daf0bf` |
| `godot --headless --editor --import --quit`（再実行） | exit 0、SCRIPT ERROR / ERROR / WARNING / Parse Errorなし |
| `python tools/validate_assets.py --strict` | exit 0、画像1154件・音15件・パレット3件・字体2件、問題なし |
| `python tools/check_frozen_files.py`（検証前後） | 両方exit 0、26/26一致 |
| `git diff --check` | exit 0 |
| `git cat-file blob <blob>` とSHA-256・bytes照合 | 採用4枚と除外1枚を実測。採用4枚は保管後・ステージblobも一致 |
| `git ls-files assets/_incoming/owner-2026-10-10-grok-lord-places/` とfolder件数 | 指定4枚だけ |

R-01〜R-08は `.scope-lock/spec.lock.json` のverify文字列そのままを各300秒上限で順次実行。追跡済み検証JSONに書き込まず、062と同じ方式でログをタスク内に保存し、既存 `tools/run_locked_checks.py` の `judge_output` を使った。条件・時間上限・判定器は不変。

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

全GUT結果は failed_assertions=0 / pending=0 / invalid=false。全要件でparser_failed=false / timed_out=false / failure_messages=[]。importが生成した追跡外UID2本は、この専用checkoutで生成されたものだけを除去した。

## 未達・未検証と引継ぎ

最終headのGitHub CIはこの報告commit時点では未実行。push後の最終head・draft PR URL・clean/未push数はPR本文と親への引継ぎに記載する。過去headのCI成功で今回headの成功を代用しない。

CI監視とmainマージ、親担当のタスク表・決定ログ更新、main取込後の4枚のhash・bytes・folder件数・記録・旧branch残存確認は親担当。長時間のCI監視は行わず返す。ゲーム組込み・人間プレイテスト・未決事項の決定は今回の範囲外。追加承認を要するブロッカーはない。
