# 025 人物記録と正式原画の独立照合報告

## 作業前の計画

- 対象SHA：`de89dc8d5e45517d27d2fee6b87a22fe19c02fe2`
- 比較基点main：`52c36908a146f3ca2aea964bb4400018a0945f29`
- レビュー登録SHA：`a43502805fc99e735c5809c46fae7e6653b02168`
- 変更可能：`docs/tasks/025-review-ner-record.md` の状態行と本報告書のみ。
- 手順：010依頼書と固定SHAの実差分確認、決定原文の文字列比較、体験仕様・付録B照合、指定出所ブランチの実バイトとSHA-256比較、その他全パスのGit不変確認、対象SHAのGitHub CI全ジョブを直接確認する。
- 開始時：作業ツリーは清潔、登録SHAからの未pushコミットなし。チェックアウトに `.agents/skills` は存在しない。

## 判定

**PASS**。010の指定範囲内で記録・正式原画の保管が行われている。修正指摘なし。mainへの統合は本レビューの対象外であり、実施しない。

## 独立照合の結果

- `git show <固定SHA>:<パス>` で取得した010依頼書と人物文書をPythonで比較した。決定本文は見出し間の外側の空行のみ除外し、内部の空白・句読点・Markdownを含めて完全一致（1290文字、UTF-8 SHA-256 `2de29fe9da556390d5bf2f99e195a853d6ef78de314364d2934d447175ee4504`）。話し方5項目も個別に抽出し、人物文書と体験仕様に各1回、原文のまま存在することを確認した。
- 人物文書冒頭の指定文、正式原画2枚のパス・ハッシュ、体験仕様の人物の要点・対になる人物との関係・詳細文書へのリンクを確認した。未決2項目は未チェックで各1回。既存の複合未決行の更新は、今回決まった場所・人物の同期に限り、残る依存事項を保持している。
- 付録Bの指定見出し、正式2枚の出所・パス・ハッシュ、途中版5ブランチと不採用理由を照合した。015の決定や具体的な台詞・実装の先取りなし。
- 素材規約、職業・魔物化企画書、素材台帳も確認。今回は `_incoming` の原本保管のみであり、素材加工・ゲーム向け素材登録ではない。台帳1140項目は基点と不変。

### 原画の実バイト比較

指定した出所2ブランチをfetchし、そのコミットのblobと010対象SHAのblobをPythonのbytes等値とSHA-256の両方で比較した。2枚とも一致。出所は010報告の転記だけでなく実際のremote refから確定した。

| 原画パス | 出所ブランチ | 出所SHA | SHA-256 | バイト数・結果 |
| --- | --- | --- | --- | --- |
| `assets/_incoming/owner-2026-10-05-grok-batch3/ner-oasis-shrine-keeper-concept.png` | `grok/owner-2026-10-05-ner-concept` | `30ea9fd70bdb7c322034e2df08ff69dd7b70e053` | `aa72aa35101e0f978c0da832ea5c31c0aca28467fd40bdd281cbab93e81c9921` | 2095857、一致 |
| `assets/_incoming/owner-2026-10-05-grok-batch3/oasis-shrine-keeper-chibi.png` | `grok/owner-2026-10-05-oasis-shrine-keeper-chibi-eye` | `1118ecc485592ce7dddbaf509d460a851d225aa8` | `7fb285a7c31839ff33350c328f39dfd97e94ea57a0fe6567ef862f8fb19a9aa5` | 1627646、一致 |

同名chibiも指定された最終版と一致。追加原画はこの2枚だけであり、途中版の追加・置換はない。

### 010の実変更一覧と範囲

`git diff --name-status 52c36908a146f3ca2aea964bb4400018a0945f29 de89dc8d5e45517d27d2fee6b87a22fe19c02fe2` の結果を許可リストと集合比較し、7ファイルで完全一致した。

| 状態 | ファイル |
| --- | --- |
| A | `assets/_incoming/owner-2026-10-05-grok-batch3/ner-oasis-shrine-keeper-concept.png` |
| A | `assets/_incoming/owner-2026-10-05-grok-batch3/oasis-shrine-keeper-chibi.png` |
| A | `docs/design/characters/ner.md` |
| M | `docs/experience-spec-v2.md` |
| M | `docs/roadmap-v2.md` |
| M | `docs/tasks/010-record-ner.md` |
| A | `docs/tasks/reports/010-record-ner.md` |

- 全文diffで体験仕様と付録Bの許可された節だけの変更を確認。010依頼書は状態行を置換した文字列と完全一致。
- `git ls-tree -rz` の全パス・モード・blobを比較し、許可7ファイル以外に追加・削除・改変なし。既存原画345件はパス・モード・blobすべて一致。
- ゲームのコード、データ、検査、CI、保護ファイル、物語文書、他タスク・報告書も不変。検査の緩和・省略・時間上限変更なし。
- 010対象SHAから025登録SHAへの差分は025依頼書の追加だけ。
- `python tools/check_frozen_files.py`：終了0、保護対象26件／一致26件。
- 固定比較とレビュー作業ツリーの `git diff --check`：終了0。

## 対象SHAのGitHub CI直接確認（2026-10-05 UTC）

GitHub CLIの `gh run list --commit de89dc8d5e45517d27d2fee6b87a22fe19c02fe2` はForbiddenで取得できなかった。接続済みGitHubのGETで `actions/runs?head_sha=<対象SHA>&per_page=100` と各runのjobsを取得し、次の010提出runの `head_sha` が対象SHAと完全一致し、両runと全20ジョブが `completed/success` であることを直接確認した。

- [CI／37263911147](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37263911147)：3ジョブすべて成功。
- [006 固定受入と最新回帰／37263911090](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37263911090)：17ジョブすべて成功。

| run ID | job ID | ジョブ | 結果 |
| --- | --- | --- | --- |
| 37263911147 | 111616592489 | 試遊前の通常戦闘・案内・画面・復帰検査 | completed/success |
| 37263911147 | 111616592670 | Godot・凍結受入テスト | completed/success |
| 37263911147 | 111616592708 | 素材検査 | completed/success |
| 37263911090 | 111616592133 | acceptance-and-regression (latest) | completed/success |
| 37263911090 | 111616592211 | normal-input-and-rendering (fixed, restart-0) | completed/success |
| 37263911090 | 111616592289 | lifecycle-audit | completed/success |
| 37263911090 | 111616592313 | normal-input-and-rendering (latest, journey) | completed/success |
| 37263911090 | 111616592314 | normal-input-and-rendering (fixed, details) | completed/success |
| 37263911090 | 111616592354 | normal-input-and-rendering (latest, restart-2) | completed/success |
| 37263911090 | 111616592356 | normal-input-and-rendering (fixed, restart-3) | completed/success |
| 37263911090 | 111616592374 | normal-input-and-rendering (fixed, restart-2) | completed/success |
| 37263911090 | 111616592380 | normal-input-and-rendering (latest, restart-3) | completed/success |
| 37263911090 | 111616592391 | normal-input-and-rendering (latest, restart-0) | completed/success |
| 37263911090 | 111616592392 | normal-input-and-rendering (fixed, restart-4) | completed/success |
| 37263911090 | 111616592411 | normal-input-and-rendering (latest, restart-4) | completed/success |
| 37263911090 | 111616592431 | normal-input-and-rendering (latest, details) | completed/success |
| 37263911090 | 111616592440 | normal-input-and-rendering (fixed, journey) | completed/success |
| 37263911090 | 111616592481 | normal-input-and-rendering (fixed, restart-1) | completed/success |
| 37263911090 | 111616592558 | acceptance-and-regression (fixed) | completed/success |
| 37263911090 | 111616592781 | normal-input-and-rendering (latest, restart-1) | completed/success |

凍結受入ジョブの「凍結契約に登録された全verifyを実行」と前後の保護照合もsuccess。fixed/latestの対になるstepのskippedは、基点から不変のworkflowのmatrix条件による分岐で、各世代の対応jobはすべて成功している。

同じ対象SHAに対して025ブランチ作成時にもrun `37265461883`／`37265461927` が起動しており、照合時点では進行中だった。これらを成功扱いせず、上記の終了済み010提出runを判定根拠とする。

## 自己点検・未確認・引継ぎ

- レビューで新規作成するのは本報告書、変更するのは025依頼書の状態行だけ。実装の修正・創作判断・保護ファイル変更は行っていない。
- 025依頼に従い、Godotインポート・R-01〜R-08等の全実行はローカルで重複実施せず、対象SHAの終了済みCIを確認した。ローカルで実行したのは独立した原文・実バイト・Git範囲比較、保護26件の照合、diffの空白検査である。
- 原画の新たな見た目の採否、人間試遊、後続のゲーム実装は対象外として未実施。記録・保管レビュー内に未確認の受入項目や修正指摘なし。
- mainへの統合条件は親へ引き継ぐ。本レビューは `codex/task-025-review-ner-record` だけにcommit・pushする。報告書自身のpush後CIは010対象SHAのCIと区別し、終了報告で確認状況を返す。
