# 038 装備基盤の不正入力処理の修正

## 作業前計画と固定点

開始ブランチは指定の `codex/task-038-fix-equipment-validation`、登録完全SHA `2547e91d36c59ed6d59f46be15c5c40b20a6b184`。指定ブランチとこのSHAをfetchしてcheckoutした。開始時の未コミット変更・未pushコミットはゼロ。037提出 `b7c025afd5a700cbfa576534aa7dcece5995b45a` と036対象 `dbceae8f68e18939a40ace71f3a24a1a1953e653` を履歴に含む。mainは `98290621204a16cbd7b4f35155edde35a153728d`。main・036/037ブランチ・PR27を更新せず、追加委譲しない。

AGENTS.md、034設計、035候補の採用追記、036依頼とAPI契約、037報告・最小再現、素材規約、職業・魔物化企画、現行体験仕様、素材台帳を確認した。checkoutに `.agents/skills` は存在せず、`/workspace/.agents` も空。適用するローカルskillはない。

担当パスは `scripts/game/equipment_rules.gd`、`tools/check_equipment_rules.gd`、必要最小限の新 `tools/check_equipment_invalid_definitions.py`、decision-logの今回追記、038自身の状態行、本報告、新 `docs/verification/equipment-validation/` に限定する。

F1は固定SHAの定義コピーだけから必須キーを削除・型を置換し、全公開APIの失敗と半完成カタログの非公開を確認する。F2は同じ正規化stateにkindの欠落・null・各不正型・未知文字列を渡し、拒否理由・candidateなし・入力不変と正常3操作を確認する。F3は巨大値・表現域の両端・JSONのfloat丸め・負値・合算overflowを固定期待で再現する。その後に型検証、原子的公開、変換前・加算前検証を実装し、同じ期待で再実行する。

標準Godotは4.6.3だったためゲーム検査には使用しない。公式4.7.2 ZIPを取得し、CI指定SHA-256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` を照合した。実体は `/tmp/equipment038-bin/Godot_v4.7.2-stable_linux.x86_64`、版は `4.7.2.stable.official.ed1daf0bf`。PATH先頭を `/tmp/equipment038-bin`、XDGのcache/data/configを `/tmp/equipment038-xdg/` 内へ設定する。

## 修正と実証

| 指摘 | 修正 | 固定期待と実測 |
| --- | --- | --- |
| F1 | 参照・比較・変換より先にroot、商品、旧weapons要素、職規則、職原本の必須キーと型を検証。ファイル読取り・JSON解析も明示エラーへ変換。items/jobsは局所候補の全検証後だけ公開 | legacy_source欠落/null、job値null、旧weapons要素nullを含む不正定義で、definition_errorsとvalidateが非空、catalog空、plan/bonusはinvalid_state、can_equip=false。修正後は実行時エラーなし |
| F2 | request.kindをStringと確認してから3操作と比較 | 欠落/null/bool（真偽）/int（0・1）/float/Array/Dictionary/未知文字列の10入力がinvalid_request、candidateなし、state/request不変。正常3操作成功。修正前はSCRIPT ERROR7件、修正後0件 |
| F3 | intをfloatへ往復させず、floatは有限・整数性・[-2^63,2^63)を確認後にint化。加算はINT_MAX/INT_MINを越える前に拒否。計画は前後いずれの補正失敗も伝播 | ±1e30、2^63、上下の域外隣接floatをinvalid_bonusで拒否。native int両端、合法負値、整数相当float、通常仮値は保持。合算の上下overflowと候補だけのoverflowはnumeric_overflow、成功値・candidateなし |

ゲームの数値上限・商品・装備規則は追加していない。新public APIも追加していない。`numeric_overflow` は既存失敗結果のreason_codeで、正常成功結果の構造は維持する。通常ゲーム・保存・戦闘・支給・能力習得へ接続していない。

### 修正前後の再現

本番ソースは修正前 `2547e91d36c59ed6d59f46be15c5c40b20a6b184`、修正後 `ada5c87e3aa660a8f04ed92b0c68348e3da9c633`。異常fixtureハーネスは修正後固定版の同一スクリプトを使い、両実行のcase名・固定期待・fixture SHA-256が完全一致することを照合した。各ケースは30秒以内、別一時プロジェクトへ無改変の固定本番GDScriptとdataコピーを展開する。原本への注入はない。

- `before-final/results.json`：202ケース、1576assertion、39成功・163不合格、全体exit1。F1/F3の誤成功と型エラーを検出した。
- `after-final/results.json`：同じ202ケース・1576assertion、202成功、全体exit0。全ケースで終了0・観測結果1件・失敗0・SCRIPT ERROR/ERROR:/WARNING:/Parse Errorゼロ。
- `before-core.log`：修正前本番に最終追加検査を適用。既存5394項目/400切替は成功、追加は117assertion/失敗6、exit1。F2のSCRIPT ERROR7件もあるため成功とは扱わない。
- `after-core.log`、`after-core-checks.json`：修正後の既存5394項目/400切替と追加93assertionが成功、exit0、エラー警告ゼロ。追加件数の差は、修正前の誤成功で成功candidate用の検査も実行されたためで、caseや期待の省略ではない。
- 元の036検査器もGit blobそのままで修正前後に別実行し、双方5394項目/400切替成功・exit0・エラー警告ゼロ。`before-original-core.log` と `after-original-core.log`。

既存検査の全関数本文（旧_initializeより前）は追加版でもbyte一致。自動選択、同点順、所有総数、party/reserve、元state/request/台帳/他人物、deep copy、現在HP/MP、補正の従来期待を全て維持している。新しい結果の出力先だけを今回の証拠へ移し、036証拠の上書きを避けた。

JSONは数値をfloatとして解析する。`9223372036854775807` は2^63へ丸まるため拒否し、その直下の表現可能float `9223372036854774784` はその整数値で保持する。`-9223372036854775808` は正確に表現でき受理する。`-9223372036854775809` は解析時に同じ-2^63へ丸まるため、解析後の値として受理されることも固定ケースで明示した。元の十進表記の任意精度保持を追加した検査ではない。native intの上下端は別のAPI検査でfloatを経由せず保持した。合法負値や採用仮値をclampしていない。

## ソース同一性と証拠

| パス | 修正後SHA-256 |
| --- | --- |
| scripts/game/equipment_rules.gd | `abdf6e33c78939b0706b6c1d385007923646a99f6261ec0067879bda014d3b52` |
| tools/check_equipment_rules.gd | `9dd861a51f4170041e5f5bc94e0ebede2c2bb5460cf9eba14513880276b236f6` |
| tools/check_equipment_invalid_definitions.py | `ce42568f246aeacfe081c9a34283f4f46279d2846e2e6792914d56e0dc333445` |
| data/equipment_rules.json（不変） | `9e52fb78f74834382c50671da1a6c4de01fe377017b78ae64db8ab0871e91892` |

`identity.json` に版ZIP/実行ファイル、importログ、ソース、固定期待の照合結果を保存。`execution.json` に実行SHA・コマンド・所要時間・終了値・エラー検出・生ログhashを保存。異常fixtureごとの生ログと観測値はbefore-final/after-final配下にある。

先行試行も別に保持した。`before/` の初回172ケースでは検査器のroot=null注入が元データへ戻る誤りが1件あり、これを直して正規の202ケースを再実行した。初回を確定再現の件数へ含めない。`after-probe/` の先行本番版a117d14ではJSON floatとArray内intの厳密一致により正常防具が拒否され、10正常対照が不合格だった。検証後のint照合へ直し、最終版で全正常対照が成功した。空のafter-initial領域は誤った完全SHA指定をGitが拒否した未実行試行で、成功証拠ではない。

今回のR-01〜06/R-08生ログは末尾空行も含めてgzipへ可逆圧縮し、`compressed-logs.json` に展開後hashを記録した。これは証拠のbyte保存で、検査出力や検査内容の変更ではない。036の既存生ログ・過去差分は触れていない。

## 実行コマンドと結果

修正前通常検査用checkoutは `/tmp/equipment038-before` の固定 `98a48207e9c640b2483f7d5f244b02e8a365faec`（検査追加のみで、本番とdataは登録2547e91とbyte一致）。追加検査だけを最終固定版から外部スクリプトとして実行した。修正後通常/R検査は `/tmp/equipment038-after` の完全SHA ada5c87へdetach。import後に検査を実行する。Rや旧検査が書く履歴記録はこの一時checkoutだけに置き、担当外の原本へ書かない。

| コマンド | 結果 |
| --- | --- |
| `timeout 600 godot --headless --editor --import --quit`（前後） | 両方exit0、エラー警告なし |
| `python tools/check_equipment_invalid_definitions.py --source-sha 2547e91d36c59ed6d59f46be15c5c40b20a6b184 --godot /tmp/equipment038-bin/godot --output docs/verification/equipment-validation/before-final` | exit1、202ケース中163不合格を再現 |
| 同じコマンドのsource-shaを `ada5c87e3aa660a8f04ed92b0c68348e3da9c633`、outputをafter-finalへ変更 | exit0、202/202成功・1576assertion、エラー警告0 |
| `timeout 240 godot --headless --path . --script res://tools/check_equipment_rules.gd`（修正後） | exit0、旧5394項目/400切替＋追加93assertion成功、エラー警告0 |
| `timeout 240 godot --headless --path <固定checkout> --script /tmp/equipment038-original-check.gd`（036のGit blob、前後） | 各exit0、5394項目/400切替、エラー警告0 |
| `python tools/run_locked_checks.py` | exit0、R-01〜08の全8件PASS、tests_ran=True、parser_failed=False、エラー警告0 |
| `python tools/check_frozen_files.py`（前後） | 両方exit0、保護26件/一致26件 |
| `python tools/validate_assets.py --strict` | exit0、素材1154・音15・パレット3・字体2、問題なし |
| 固定前後のfixture/期待hashと既存検査本文のbyte照合、禁止パスのGit差分照合 | 成功。data/assets/test/.scope-lock/.github/AGENTS.md差分なし |
| `git diff --cached --check`（今回の証拠） | exit0。今回R生ログはbyte保存のgzipで登録 |

Rの全観測値は `requirements.json`、個別生ログはrequirement-R-*。R-07はA01〜A14と最終FIRST_REGION_PASSを満たし、他7件はGUTのtests/assertions/failed/pendingを既存判定器で検証した。予算・verify・GUT・保護検査を変更していない。

## CI

本番・検査器固定版 `ada5c87e3aa660a8f04ed92b0c68348e3da9c633` を指定ブランチへpushした。GitHub APIで同じhead_sha・pushイベントの [CI run 37564112973](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37564112973) と [固定受入／最新回帰 run 37564113009](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37564113009) の開始を確認した。報告作成時点は進行中であり、このソース版のCI成功はまだ主張しない。

この報告と生証拠を登録する最終コミットのCIは別のrunになる。自己参照で報告SHAを更新し続けないため、最終提出SHA・全ジョブ終了・各runの3件＋17件の成功結果を、最終返答へまとめる。対象SHAの全20件が成功するまでは完了として返さない。

新装備検査2本は既存CIへ未接続。上記の指定版・固定checkoutの別実行で確認したもので、既存CI20ジョブの成功で代用しない。最終証拠・報告コミットの完全SHAと、その同一SHAをheadとする全CIの終了結果は最終返答で示す。未終了のCIを成功とは記録しない。

## 変更ファイルと範囲

- `scripts/game/equipment_rules.gd`：F1〜F3の本番修正。
- `tools/check_equipment_rules.gd`：既存本文を保持しF2とnative int/候補overflowの追加、今回の証拠出力先。
- `tools/check_equipment_invalid_definitions.py`：固定SHA・一時コピー・固定期待・機械判定・件数・失敗理由・エラー検出。
- `docs/decision-log.md`：今回の技術判断3件だけを末尾追記。
- `docs/tasks/038-fix-equipment-validation.md`：自身の状態行だけ。
- 本報告と `docs/verification/equipment-validation/`：新しい実行証拠。

削除・担当外差分・原画/data変更・保護/契約/workflow変更なし。main/PR27/036/037ブランチへ書込み・マージなし。既存036/037本文・報告・証拠は不変。最終提出までソース3ファイルが上記の固定実行版とbyte一致することを照合する。

## 未達・未検証・後続

F1〜F3と依頼されたローカル検証の未達なし。最終CIは最終返答で結果を確定する。装備全体完成・main受入の報告ではない。

通常ゲーム接続、保存移行、初期生成・一回支給・不足補填、能力習得、実戦効果、上限縮小時の現在値切詰め、UI、新検査のCI接続はこの段階の対象外で未接続。人間試遊・正式な数値調整も未実施。新商品・規則・公開範囲を決める判断事項はない。
