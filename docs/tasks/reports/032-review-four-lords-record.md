# 032 014の原画と決定記録の独立レビュー

## 計画・固定した比較対象

- 判定対象：`37611edb485aab73a074beaa5ef27e0f100aeda4`（014提出）。基点main：`3078f061926f5e74eae7d08a8807d3bff92666b6`。
- レビュー開始点：`787573482d602fc8aa0b46d3682acb993ea0a7e4`。自身の変更は032依頼書の状態行と本報告だけとする。開始時の未コミット変更なし。開始点はリモート032と一致し、未pushコミットなし。
- 対象差分は指定原画4枚・指定文書3件・014状態行・014報告の9ファイル。基点と対象の完全SHAで固定比較し、動く作業ツリーを受入基準にしない。
- 各指定ブランチを個別fetchし、取得時の完全SHAを固定。`git show <取得元SHA>:<path>` と `git show <提出SHA>:<path>` の生バイトをPythonの`hashlib.sha256`へ入力し、依頼書値との三者一致と全バイト等価を確認する。Git blob IDの一致だけで代用しない。

## 判定

**PASS（文書記録と原画保管の独立レビュー）。差し戻し事項なし。** mainへの統合は未実施であり、このPASSはマージ完了やゲームへの実装を意味しない。

## 原画の独立照合

各行のSHA-256は取得元実バイト・提出先実バイトで別々に計算し、両方が依頼書値と一致した。全4枚についてPNGの読み取り検証も成功。名前・パス・バイト数も一致。

| 原画ファイル | 取得ブランチ | 取得元完全SHA | 取得元＝提出先＝指定SHA-256 | バイト数 |
| --- | --- | --- | --- | --- |
| `assets/_incoming/owner-2026-10-05-grok-batch4/optional-boss-undead.png` | `assets/owner-2026-10-05-grok-batch4-undead` | `fcd32182011d03bcb44e81f586325d48d95c8250` | `30e4cee201f6391241afe505b7a522f3c890040ab1bfaa1eb68a9a41954a9a9a` | 1572477 |
| `assets/_incoming/owner-2026-10-05-grok-batch4/optional-boss-bird.png` | `assets/owner-2026-10-05-grok-batch4-bird` | `0e0cf94271b639811ae27a3844e9a03c210737c1` | `e25df4ce5bb7879ed58786671b853a4bbf1b7c8df61254b1ab0db258ba04e8cd` | 1747452 |
| `assets/_incoming/owner-2026-10-05-grok-batch4/optional-boss-spirit.png` | `assets/owner-2026-10-05-grok-batch4-spirit` | `53b98f0f97a81408a59b47972e9678adbcaab808` | `02b05a0888df699489b1ebc8bf61a89c8a565721622ad65974ce83c154c16339` | 1739572 |
| `assets/_incoming/owner-2026-10-05-grok-batch4/optional-boss-dragon.png` | `assets/owner-2026-10-05-grok-batch4-dragon` | `151919f57041fb70d193e394518df731e22dcbe8` | `11139fec646f6a75d233e2f188a25306656a3fea6281dcee953a6b60f40ff562` | 1830645 |

鳥と竜の岩を含む画像全体が原本と全バイト一致しているため、岩の除去・加工はない。今回は絵柄の採否やゲーム用変換の審査ではない。既存原画347件は`git ls-tree -rz`のパス・モード・blob比較で全件不変。指定4枚以外への追加・変更・削除・改名はない。

## 原文・未決・015継承の照合

| 対象（提出SHAの行） | 根拠と照合結果 |
| --- | --- |
| `docs/design/monster-job-unlock.md:35`〜49 | 014依頼書の「主の呼び名の決め方」から人物記録末尾まで、見出し・Markdown強調・句読点・改行を含む連続文字列が完全一致。言い換えなし。 |
| 同文書51〜53、67〜83 | 仮案を明示的に未決と記録。現在の未決3項目を依頼書と照合。旧「主の名前、見た目、強さ」は015時点の履歴であるとの説明が先にあり、現在の決定と混同していない。既存の未決例を採用した変更や、新しい命名・台詞はない。 |
| 同文書1〜30、75行以降 | 014追記ブロックを除いた文字列が基点の全文と完全一致。015の解放の分け方・居場所・選択・未決の台詞例を保持。015依頼書・報告、030、人物文書も変更なし。 |
| `docs/roadmap-v2.md:354`〜367 | 指定の付録B追記見出し、4枚のブランチ・パス・SHA-256、岩を含む採用形を照合。変更はこの追記のみ。015の決定記録を保持。 |
| `docs/experience-spec-v2.md:467`〜475 | 決定済みの本当の名前・原画と、居場所の呼び名・場面の流れと台詞・媒体の選択・強さ・実装時期の未決を区別。既存の実装時期は1項目のままで重複なし。未決事項以外の015の決定も不変。 |
| `docs/tasks/014-record-four-lords.md:3` | 基点との差は状態行だけ。「報告済み」を「未着手」に戻した文字列が基点全文に一致。 |

差分一覧と全ツリーの機械照合により、担当外5897件はパス・モード・blobとも不変。ゲーム、データ、素材台帳、パレット、検査、`.scope-lock/`、`.github/`、`AGENTS.md`、`project.godot`、物語本文、他依頼書・報告を変更していない。検査の弱化・省略・時間上限の延長はない。

## 直接確認した014提出SHAのCI

GitHub APIのworkflow runsを提出SHAで抽出し、014ブランチのpush・PR各2実行を確認。各jobsの`head_sha`は対象SHAと一致。`per_page=100`で総数と取得件数の一致も確認し、全40ジョブが`completed/success`。過去の原画追加コミットの結果だけで代用していない。

| 起動 | ワークフロー | URL | 全ジョブ |
| --- | --- | --- | --- |
| push | CI | https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37422481802 | 3/3 success |
| push | 006 固定受入と最新回帰 | https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37422481736 | 17/17 success |
| PR | CI | https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37422486506 | 3/3 success |
| PR | 006 固定受入と最新回帰 | https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37422486520 | 17/17 success |

push CIのjob `112134701484`の生ログを直接取得。Godot `4.7.2.stable.official.ed1daf0bf`、R-01〜R-08それぞれ`PASS`・終了0・tests_ran=True・parser_failed=False、検査前後の保護26件一致を確認した。CLIのGitHub API呼出しはForbiddenだったため、認証済みGitHubコネクタの読取APIを使用した。空のcombined statusはCI成功の証拠にしていない。

## ローカル再検証

対象SHAそのものを`git worktree add --detach /tmp/task032-check 37611edb485aab73a074beaa5ef27e0f100aeda4`で分離。GodotはCIと同じ公式4.7.2 zipを取得し、SHA-256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`を照合。環境既定の4.6.3は版確認だけに使用し、受入検査には使用していない。XDGの一時状態を`/tmp/task032-xdg/`に分離。

- `timeout 600 /tmp/task032-godot/godot --headless --editor --path /tmp/task032-check --import --quit`：終了0。ログに`SCRIPT ERROR|ERROR:|WARNING:|Parse Error`なし。
- `python tools/validate_assets.py --strict`：終了0。画像1154件・音15件・パレット3件・字体2件、問題なし。原画保管先は既存規約どおり素材検査の対象外のため、上の独立バイト照合で検証した。
- `python tools/check_frozen_files.py`：終了0、26/26一致。
- Pythonで生バイト・原文・台帳・範囲を照合：成功。既存原画の初回集計ではGitの日本語パスのquoteを誤解釈して一時スクリプトが停止したため、`ls-tree -rz`のNUL区切りへ直し、全件を再実行して成功。リポジトリの検査器は変更していない。
- `git diff --check 3078f061926f5e74eae7d08a8807d3bff92666b6 37611edb485aab73a074beaa5ef27e0f100aeda4`：終了0。
- `PATH=/tmp/task032-godot:$PATH XDG_CACHE_HOME=/tmp/task032-xdg/cache XDG_DATA_HOME=/tmp/task032-xdg/data XDG_CONFIG_HOME=/tmp/task032-xdg/config RPG_QA_SAVE_PREFIX=task032 python tools/run_locked_checks.py`：終了0。既存verify・判定器・各300秒上限のまま、以下の全8件を実行した。

| 要件 | 実測結果 | 実行証拠 |
| --- | --- | --- |
| R-01 | PASS・終了0 | 2テスト・765assertion・失敗0・pending 0・invalid false |
| R-02 | PASS・終了0 | 5テスト・946assertion・失敗0・pending 0・invalid false |
| R-03 | PASS・終了0 | 2テスト・73assertion・失敗0・pending 0・invalid false |
| R-04 | PASS・終了0 | 1テスト・293assertion・失敗0・pending 0・invalid false |
| R-05 | PASS・終了0 | 2テスト・79assertion・失敗0・pending 0・invalid false |
| R-06 | PASS・終了0 | 2テスト・87assertion・失敗0・pending 0・invalid false |
| R-07 | PASS・終了0 | A01〜A14 PASS、FIRST_REGION_PASS: checks=14 |
| R-08 | PASS・終了0 | 17テスト・2302assertion・失敗0・pending 0・invalid false |

原記録SHA-256：`21cfac566bf9794458c7a817a61865cc603382aa3c824cd90491bfde0d673e8a`。生ログ・原記録は隔離checkoutに保存。検査後の保護照合も26/26一致。検証による記録更新は隔離checkoutだけで、自身の提出に混ぜない。

## 指摘・確認限界・自身の提出

- 重要度付きの修正指摘：なし。したがって対象行・再現手順・最小修正案を伴う差し戻しはない。上の表は照合根拠であり、レビュー対象への修正は行っていない。
- 014依頼書の「mainに入る」は未達のまま。今回の明示指示どおりmain未統合で親へ返す。014の報告にも同じ限界が記載されている。
- 人間プレイ、60時間の実測、ゲームへの配置・戦闘・会話・解放、画像の新しい採否は今回検証していない。原画は採用済みの指定4枚と同じであることを検証した。
- 自身の変更は`docs/tasks/032-review-four-lords-record.md`の状態行（報告済み）と本報告だけ。014・mainへの書込み、031の先取り、追加委譲、マージは実施していない。
- 本報告と状態行を1コミットで032ブランチへ通常pushする。自身の提出SHAに対する新規CIはpush後に全ジョブの終了を確認し、最終回答で実際のSHA・URL・結果を報告する。本報告時点の未実行結果を先取りして成功と記録しない。
