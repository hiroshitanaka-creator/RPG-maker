# 001 状態確認と決定反映の報告

## 作業前に決めた計画

基準mainは `dad3fca1d2d6216c3418999d27a4cf581ca00860`。以下を決めてから文書の編集に着手した。001だけを担当し、002の計画・実装には進まない。

### C・Dで直す文書と箇所

| 文書 | 見出し・箇所 | 行うこと |
| --- | --- | --- |
| `docs/roadmap-v2.md` | 冒頭、新設「2026年10月3日の決定」 | Cの5決定を記録し、今回の状態確認への参照を追加する |
| 同上 | 「4. スプリント計画」の「スプリント6：第2・第3地方」、新設「付録B追記：owner-2026-10-03-region3-port」 | 外観・室内の新方式と6枚の用途を明示する |
| 同上 | 「2026年10月2日：第2地方の港町案Aと追加原画の指定」 | 部品方式を当時の計画と明記し、10月3日の変更を併記する |
| `docs/experience-spec-v2.md` | 「決定事項と前提」「世界構造」「拠点の中身」 | 伝言板、港町の実装済み方式、今後の外観・室内の制作方針を反映する |
| 同上 | 「戦闘・職業・アビリティ・魔物化」直後に新設「状態異常・道具・メダル・防具（設計のみ）」 | 設計文書への参照と決定・未決・未実装を分けて記す |
| 同上 | 「物語の大筋」内に新設「結末の方向」 | 物語原本の方向を反映し、原本は変更しない |
| 同上 | 「画面と演出の仕様」の「町・村・城」「世界マップ」、新設「建物の中」 | 一枚絵・通行地図・上の層、手前の高い壁、世界マップ原画の用途を明記する |
| 同上 | 「未決事項」の「遊び・仕組み」「見た目・音」 | 旧本編CIの手動化とメニューの見た目の統一を実施済みに直す。防具・メダルの細部は未決のまま残す |
| `docs/asset-spec.md` | 「2. 色と透過」 | 水の4色の既存追加記録に合わせ、natural.gplの現行上限を80色とする |
| `README.md` | 冒頭の進捗案内 | 最新の入口をロードマップへ向け、従来の現在地への参照も履歴として残す |
| `docs/current-status.md` | 冒頭 | 最新の入口と001の状態確認へ案内し、既存の実施記録を保持する |

### 「外観は部品で組み立てる」と読める記述の扱い

| 文書・見出し | 既存の記述 | 方針 |
| --- | --- | --- |
| ロードマップ「スプリント6：第2・第3地方」 | 10月1日の「外観は部品で組み立て」 | 当時の計画として残し、10月3日に一枚絵方式へ変更・第2港は実装済みと併記する |
| ロードマップ「2026年10月2日：第2地方の港町案Aと追加原画の指定」 | 「外観を原画の部品で組み立て」 | 当時の方式として残し、現在の方式への参照を付ける |
| 体験仕様「拠点の中身」 | 「内部のタイルは、既存の素材台帳の画像を使う」 | 今後の町村外観・建物内部にタイル組立を強制しない文へ直し、適用範囲を明示する |
| 体験仕様「画面と演出の仕様／町・村・城」 | 「家ごとに…小物を置き」「建物の外観（屋根・壁・扉・窓）を置き」 | 見た目の要素として記し、部品を並べる制作指示を一枚絵方式へ直す |
| 同上 | 「建物の中は床・壁・家具…で作る」 | 一枚絵の室内に含める要素として整理し、今後の高い手前壁の標準を別項に記す |
| ロードマップの過去の城下町・魔物化等の実施記録、体験仕様「世界マップ」「ダンジョン」 | 過去に使った部品、タイルや地形の描き分け | 町村外観の新規制作とは対象が異なるため保持。第1地方の配置・R-07は変えない |

## A. 基準mainの状態確認

実行日：2026-10-04（JST）。以下の機械ログ時刻はUTCで記す。10月3日は依頼者の決定日であり、この作業の実行日と区別する。

### A1. mainの取り込み

- `git fetch origin` で、開始時の `f6434d5d188449c24dcba935bf1ae92d80080d27` から最新main `dad3fca1d2d6216c3418999d27a4cf581ca00860` を取得した。
- `git switch -c codex/task-001-status-and-decisions origin/main` で指定ブランチを作成した。別のworktreeは作成していない。
- 元のローカルブランチ `work` は保持した。今回と無関係なコミットをpushしていない。

### A2. Godotのインポート

作業ディレクトリは `/workspace/RPG-maker`。クラウド環境で検証済みの `.tools/cloud-onboarding/activate.sh` を読み込み、Godot `4.7.2.stable.official.ed1daf0bf` と書き込み可能なキャッシュ・保存先を使用した。

`timeout 600 godot --headless --editor --import --quit` は終了0。ログ中の `SCRIPT ERROR`・`ERROR:`・`WARNING:`・`Parse Error`・`Fontconfig error` は0件。ログは `.tools/task-001/import-main.log`。

### A3. 保護照合とR-01〜R-08

`python tools/check_frozen_files.py` は **保護対象26件、一致26件、終了0**。

R-01〜R-08は、`.scope-lock/spec.lock.json` の各verifyを変更せず、保存済みクラウド補助 `.tools/cloud-onboarding/checks.py` から実行した。判定は既存 `tools/run_locked_checks.py` の `judge_output` をそのまま使用し、300秒制限・警告検出・空実行とpendingの拒否を維持した。標準ランナーが上書きする追跡済みの履歴資料を保護するため、ログの保存先だけを `.tools/` に分離した。検査本体や判定器は編集していない。

対象SHAは **`dad3fca1d2d6216c3418999d27a4cf581ca00860`**、記録時刻は `2026-10-04T00:57:07.634160+00:00`。結果は `.tools/cloud-onboarding/logs/20261004T005532Z/results.json` と各 `R-xx.log` に保存した。

| 条件 | verifyの対象 | 結果 | 実行件数 |
| --- | --- | --- | --- |
| R-01 | `test/unit/test_job_data.gd` | PASS・終了0 | 2テスト・765アサーション |
| R-02 | `test/unit/test_job_actions.gd` | PASS・終了0 | 5テスト・946アサーション |
| R-03 | `test/unit/test_ability_slots.gd` | PASS・終了0 | 2テスト・73アサーション |
| R-04 | `test/unit/test_monster_form.gd` | PASS・終了0 | 1テスト・293アサーション |
| R-05 | `test/unit/test_battle_loop.gd` | PASS・終了0 | 2テスト・79アサーション |
| R-06 | `test/unit/test_save_roundtrip.gd` | PASS・終了0 | 2テスト・87アサーション |
| R-07 | `tools/smoke_first_region.gd` | PASS・終了0 | A01〜A14の14項目すべて成功 |
| R-08 | `test/unit/` 全体 | PASS・終了0 | 17テスト・2,302アサーション |

GUTの失敗アサーション・pendingは各実行0、invalidはfalse。R-08にはR-01〜R-06のテストを含むため、重複分を別テストとして合算しない。Aの停止条件に該当する失敗はなかった。

### A4. 基準mainのGitHub Actions

**未確認。ローカル成功をGitHub Actions成功の代わりにしていない。** 対象はA1の `dad3fca1d2d6216c3418999d27a4cf581ca00860`。`gh api repos/hiroshitanaka-creator/RPG-maker/actions/workflows/ci.yml/runs --method GET -f branch=main -f per_page=8` は `Forbidden`、終了1。認証なしの読み取りでもCONNECT時点で403となり、GitHubのAPI応答へ到達していない。

環境のネットワーク許可先に `api.github.com` が含まれていないことを確認した。Gitのfetchは既存のHTTPSプロキシで成功し、`GH_TOKEN` は存在する。値の表示・抽出・追加トークンの要求は行っていない。

| 通常CIのジョブ | 状態 | 所要時間 | 対象runのURL |
| --- | --- | --- | --- |
| `preplay`：試遊前の通常戦闘・案内・画面・復帰検査 | API接続制限により未取得 | 未取得 | 未取得 |
| `assets`：素材検査 | 同上 | 未取得 | 未取得 |
| `godot-import`：Godot・凍結受入テスト | 同上 | 未取得 | 未取得 |

[CIの一覧](https://github.com/hiroshitanaka-creator/RPG-maker/actions/workflows/ci.yml) は参照先であり、個別runの成功証拠ではない。既存文書の `0674954` の成功runを、今回の基準mainの結果へ流用しない。

不足している `api.github.com` だけを追加した環境設定ドラフトは保存済み（`status: saved`、`requires_publish: true`）。既存の許可先プリセット・インストール手順・起動手順は保持した。環境設定でこの変更が公開・反映されたら、同じSHAの全ジョブ状態・所要時間・個別run URLを取得して追記する。

### A5. ローカルの状態

開始時点の記録は `2026-10-04T00:54:51.235130+00:00`。

| 項目 | 作業前の状態 |
| --- | --- |
| 作業ブランチ | `work`、HEAD `f6434d5d188449c24dcba935bf1ae92d80080d27` |
| 未コミット変更・未追跡ファイル | なし（`git status --short --untracked-files=all` が空） |
| 未pushコミット | なし（fetch後の `git log --oneline --branches --not --remotes` が空） |
| stash | なし（`git stash list` が空） |
| ローカルだけにあるブランチ | `work`。`git ls-remote --heads origin` の19ブランチと照合し、同名リモートブランチなし。コミット自体はmainの履歴に含まれる |

001の開始後に作成したローカルブランチは `codex/task-001-status-and-decisions`。既存の `.tools/` と `.godot/` はGit管理対象外の環境・検査用ファイルとして保持した。作業後のpush・作業ツリー状態は末尾に記す。

### A6. AC-01〜AC-03の正式登録

正式契約 `.scope-lock/spec.lock.json` の `requirements` は **R-01〜R-08の8条件だけ**。AC-01〜AC-03は未登録だった。

- `python tools/check_acceptance_registration.py`：`requirements=8 errors=6`、終了1。既存8条件＋追加3条件の並び、過去のgoal・non_negotiables・protected_paths・改訂履歴、追加3条件の改訂理由の照合で不一致。旧登録案の基準から、世界マップ型への承認済み改訂も行われているため、これをR-01〜R-08の失敗や保護ファイルの破損と混同しない。
- `python tools/check_acceptance_registration.py --proposal`：`requirements=11 errors=0`、終了0。これは保存済み改訂案の構造照合であり、正式登録や今回の全11verify実行を意味しない。
- `docs/current-status.md` の「承認待ち」は当時の記録として残す。リポジトリから正式登録済みという証拠は得られなかった。現在の承認の有無を推測せず、001では保護契約を変更しない。

## B. ZIP原本の登録とハッシュ照合

ZIP内の6ファイルを、原本と同じパス・同じバイト列でコミット **`886d98c711a2c6d74ac44d03c1b202141969443a`** に登録した。展開後のファイルとGitコミットのblobの両方をZIPに照合し、6/6一致。

| 原本のパス | バイト数 | SHA-256 |
| --- | ---: | --- |
| `docs/tasks/README.md` | 3140 | `6da4afae76de9ba1377a8247b84e2b84ea41993ab45d1f7cabc04bcded6de044` |
| `docs/tasks/_template.md` | 1310 | `a0b16481740c7c7ee613ffd46a72a0cf622b6a298b73f9a329df2cd931cf9519` |
| `docs/tasks/001-status-and-decisions.md` | 15007 | `21d666d20de7e450a99af4604614d7056b1e89bd74f161a18832c2cd49295f61` |
| `docs/tasks/002-sprint6-next-plan.md` | 7464 | `1a12370036539d19f34ea5fd60eb40dc8ed3b5763c73e7588478dcafc62c5315` |
| `docs/design/items-and-equipment.md` | 4711 | `948615a73fecff7dae7aea2c0e29aa6497bb2c6c81735cee438582651235561f` |
| `docs/handover/2026-10-03-claude-snapshot.md` | 59140 | `7bcaf6889e838f89adf6ae3017405b8a9395b410f9b26df328e7af96b6160db2` |

001原本の「6ファイル不変」と「状態を報告済みにする」は両立しないため確認し、依頼者から **「001の状態行だけ更新する」** と回答を受けた。原本は上記コミットに保持し、作業版は先頭の状態行だけを作業中、提出時に報告済みへ更新する。他の5ファイルと001の本文は変更しない。引き継ぎ原本にある不明・未実装の記述は資料作成時点の記録として保持し、Aで実測した最新mainの状態と区別する。

## C〜E. 文書への反映

| ファイル | 変更内容 |
| --- | --- |
| `docs/tasks/README.md` | 伝言板の運用原本を新規登録 |
| `docs/tasks/_template.md` | 依頼書のひな型原本を新規登録 |
| `docs/tasks/001-status-and-decisions.md` | 原本登録後、承認された状態行だけを更新 |
| `docs/tasks/002-sprint6-next-plan.md` | 原本を新規登録。作業には着手していない |
| `docs/design/items-and-equipment.md` | 設計原本を新規登録。内容・数値・未決事項は不変 |
| `docs/handover/2026-10-03-claude-snapshot.md` | 引き継ぎ原本を新規登録 |
| `docs/roadmap-v2.md` | Cの5決定、6枚の用途表、旧外観方式の変更履歴、001の基準状態への参照 |
| `docs/experience-spec-v2.md` | Cの決定、メニュー統一と旧本編CI分離の実施済み表記、物語原本の結末の方向 |
| `docs/asset-spec.md` | natural.gplの現行80色上限と既存の水4色の採取記録を反映 |
| `README.md` | 最新進捗の入口をロードマップにし、伝言板へ案内 |
| `docs/current-status.md` | 冒頭でロードマップ・001の報告へ案内。過去の記録は保持 |
| `AGENTS.md` | Eで指定された「自走の許可」を末尾にそのまま追加 |
| `docs/decision-log.md` | 既存ファイルの見出し・表・記録を保持し、1件1行の書き方を追記 |
| `docs/tasks/reports/001-status-and-decisions.md` | この計画・状態確認・変更内容・自己点検・未達の報告 |

Eの「空のdecision-logを作る」は、最新mainに既存記録があるという原依頼時点からの差があった。依頼書の「過去の実施記録は消さずに残す」に従い、空の内容で上書きしなかった。新しいゲーム仕様や元に戻せない判断を追加していない。

natural.gplは実ファイルを数えて80色、記録の旧76色が順番・値とも一致、末尾4色が `#014A92`・`#0065B8`・`#017ACB`・`#5DB9E4` と一致することを確認した。001で色を追加したわけではない。

物語原本 `docs/story-outline.md` のSHA-256は `13e9366c89c5a2cd759406f54f88daca4c188ce06504c532a005e7a9a052650c` のまま。結末の詳細は仕様書内に反映し、通常の進捗報告へ展開しない。

## 自己点検

| 項目 | 結果 |
| --- | --- |
| Aの6項目と対象SHA | 6項目を記録。ローカル検査は基準mainのSHAと一致。CIの実結果だけはAPI制限により未取得 |
| ZIP原本 | 登録コミットで6/6完全一致。作業版は承認済みの001状態行だけ例外、他5点と本文は不変 |
| Cの5決定 | ロードマップと体験仕様に反映。原画6枚の用途・今後の外観と室内方式・設計のみの扱い・伝言板を確認 |
| Dの5修正 | 反映済み。過去の実施記録を保持し、変更日と現在の参照先を明示 |
| Eの指定節とdecision-log | 指定節は依頼書内のコードブロックと末尾の文字列を完全一致で照合。decision-logは既存記録を保持 |
| 編集範囲 | 基準mainとの差分は担当文書とE指定のdecision-logだけ。ゲーム・データ・素材・検査・契約・CI・project.godot・addonsは差分0 |
| 未決事項 | 題名・地方や町村の正式名・防具・メダルの細部・道具数値等は未決のまま。最新mainで既に決まっていた内容を未決へ戻していない |
| GitHub CI全ジョブ成功 | **未確認。これがmain統合を止めている外部要因** |

文書編集後、次も成功した。

| コマンド | 結果 |
| --- | --- |
| `python tools/check_progress_docs.py` | 履歴26本・errors=0 |
| `python tools/test_locked_check_reporting.py` | 23テスト成功 |
| `python tools/check_sprint6_preparation.py` | 原本12枚・座標候補78件・errors=0 |
| `python tools/check_frozen_files.py` | 26/26一致 |
| `python tools/validate_assets.py --strict` | 画像1124件・音15件・字体2件・パレット3件、問題なし |
| `git diff --check` | 問題なし |

追加・既存テストを弱めたり、飛ばして合格としたり、時間上限を延ばしたりしていない。今回のCI状態はローカル検査とは別に未確認とした。

## 統合状況と残る作業

指定ブランチ `codex/task-001-status-and-decisions` へ、原本登録 `886d98c711a2c6d74ac44d03c1b202141969443a` と文書反映 `639cd3419e01487ca63b85e693ca0c1a5d22c3c9` を通常pushした。この段落を追記する前の確認では、HEADとリモート追跡先がともに `639cd3419e01487ca63b85e693ca0c1a5d22c3c9`、未コミット変更・未pushコミット・stashは0。ローカルだけの既存ブランチ `work` は保持している。

環境のfetch対象がmainだけだったため、push後の追跡確認に必要な今回のブランチのfetch設定だけを追加し、リモート追跡先を取得した。リポジトリのソースや履歴は変更していない。PR作成用URLはpushで案内されたが、APIが使えないためPRを作成済みとはしていない。

**mainには未マージ。** 自走の許可の5条件のうち、R-01〜R-08成功・保護ファイル不変・検査の弱化なし・依頼範囲内の4条件を確認したが、GitHub CI全ジョブ成功は未確認のため、mainへpushしていない。マージSHAとマージ後のmainのCIは存在せず、記載できない。

ネットワーク変更の公開・反映後に残る作業は、基準mainと作業ブランチの対象SHAに対する全CIジョブ・所要時間・run URLの取得、必要なら失敗原因の確認、5条件が成立した場合のマージ、そのmainのCI確認と本報告への結果追記である。保護対象の修正が必要なら依頼者へ確認する。002には進まない。

依頼書の状態「報告済み」はこの未達を含む報告の提出を示し、001全体の完了やmain反映済みを意味しない。
