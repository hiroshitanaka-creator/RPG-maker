# 049 保存codec・能力定義・新版全状態検証を実装する
- 状態：未着手
- 担当：Codex GPT-6.1 Sol／High
- 依頼日：2026-10-08 JST
- 前提：040〜048確認済み。main 3273fa4d788fb8d4e0e2d6ef209a70f029d257e2 の全34CI成功
- ブランチ：codex/task-049-equipment-save-codec
- 担当の場所：下記に限定
- 変更禁止：test/、.scope-lock/、addons/、原画/素材、既存検査器・既存workflow・040計画・他依頼/報告・過去証拠

## 目的と背景
040計画S2を実装する。S1は候補の純粋変換まで完了。raw保存の復元、型を保持する符号化、能力catalog、新版全状態検証を純粋な内部APIとして完成させる。S3のI/O取引、S4通常runtime、S5公開はこの依頼に含まない。採用装備・配布・名称・仮数値は再決定しない。

## 担当の場所
新 scripts/game/equipment_save_codec.gd、必要な新 scripts/game/equipment_document_validation.gd、新 data/equipment_abilities.json。
既存 scripts/combat/battle_catalog.gd、scripts/game/game_session.gd、scripts/game/integrated_progression.gd は能力定義/非装備共通検証/明示context付きstatsの接続に必要な部分だけ。
scripts/game/equipment_save_validation.gd と equipment_state_view.gd は新しい内部API追加に必要な部分のみ。S1公開APIの契約・既存ケースを維持する。
新 tools/check_equipment_save_codec.gd、tools/fixtures/equipment-save-codec/、docs/verification/equipment-save-codec/。
docs/tasks/049-equipment-save-codec.md の状態行、docs/tasks/reports/049-equipment-save-codec.md、docs/decision-log.md の今回追記。
必要なら新 .github/workflows/equipment-codec.yml に今回の専用検査jobを追加可（2026-10-07のユーザー明示承認範囲）。既存workflow/wrapperは変えない。

## 作業内容
1. AGENTS、040計画全文、041/042のS1実装・証拠、043〜046の専用CI、現行保存コードを読む。開始SHA/未コミット/未pushと関数契約・依存・担当箇所を報告冒頭で整理する
2. decode_source(bytes, context) と encode_candidate(document, context相当) を純粋APIとして実装。040第4.1/6/9/10節のM09〜M12を満たす。raw bytesを保持し、UTF-8/JSON/gzip包み/型metadata/metrics/trialID/旧新形式/位置を検証。通常load_gameやsave_game、archiveへ依存して副作用を起こさない
3. 型情報のあるdocumentは型/値/キー/配列順を保持。型なし旧JSONは現行互換規則の正規化と区別。存在しないmetrics/trialID/first_regionを永続documentへ追加しない。位置補正が必要なら差分を示して拒否し、勝手に移動しない。未知キー/型を削除して通さない。符号化の精度損失は拒否する
4. two_handedの採用済みpassive/self定義を実catalogへ登録・検証する。係数・新たな名称/効果は決めず、通常報酬・戦闘へ接続しない。旧能力定義を上書きせず、未定義や壊れたcatalogは拒否
5. 新版全状態validatorを作り、party/reserve・非装備進行・修練/能力・装備所有/袋・上限・監査/支給台帳・metrics/trialIDを明示contextで検証。S1 validate_new(document,source,hash,context) は移行直後一致のAPIであり、一般の進行後保存のvalidatorと分離する。元保存全体を常時要求しない通常新版の検証と、元保存を持つ移行差分検証を区別する
6. 新装備補正を用いた全人物stats/上限を検証する。040で許可された上限再計算と現在値minだけを行い、回復・蘇生を起こさない。現GameSessionの旧装備状態を暗黙参照しない。必要なS2候補準備は別の純粋APIにし、S1の固定契約を変更しない
7. encode後に同じ新版decoderへ戻して全値/型/順序を比較し、metadata再生成を検証。型なしfallbackで失敗を消さない。失敗時candidate/documentを成功値として返さず、入力/state/metrics/historyを不変にする
8. 通常ゲームの開始・save/load/import/UIを新形式へ切り替えない。GameSessionの通常入口がまだ新候補を拒否するS1条件は維持する。純粋な新版内部入口で検証し、公開は後続と明記
9. 新規fixtureでM09〜M12の正負例を独立固定期待から検証。plain/gzip、typed配列/空/float、10000履歴、未知版、壊れた5field、型path重複/欠落/builtin、非有限値、typed辞書、metrics不整合、trialID、未知root/人物キー、reserve、進行後新版を網羅。実装から期待を作らない
10. 既存装備/S1/旧入口比較を全て保持し、既存R8/保護26/全CIを確認。新検査を専用workflowに追加する場合は各job15分、原検査120秒、import600秒以内。固定完成時条件は完全SHAの当時checkoutに分け、最新版回帰との対応表を記録。失敗/警告/欠落の伝播、失敗時証拠保存/保護照合を要求する

## 守ること
通常保存ファイルの実移行、ユーザー保存へのアクセス、取引ディレクトリ生成、S3〜S5の実装・公開、ゲーム規則/数値/作品名の創作はしない。検査削除/省略/時間延長で通さない。旧比較の固定142/10全文を変更しない。既存検査・契約に変更が必要なら具体的な衝突と最小差分を報告し、その変更だけ保留して独立部分を進める。main書込み/マージ・強制push・削除・追加委譲なし。

## 報告・自己点検
全変更と関数契約、S1/S2責任、全fixtureケースID/固定期待/実結果/数、旧互換証拠、コードSHA、全CI、未実装/未実行を保存する。コードを固定SHAにcommitして原証拠を別に保存し、最終版でコード不変を確認。旧ソースと検査の保存・保護26一致・R全8・同一最終SHAの全CI成功を確認。担当外変更を隠さない。報告は指定パス、自身状態は報告済みへ。commit/push、draft PRで提出。最終SHA/CIは自己参照を避け最終応答で補ってよい。
