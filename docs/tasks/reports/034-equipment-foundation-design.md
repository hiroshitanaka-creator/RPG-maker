# 034 装備基盤設計の報告

## 作業前の計画・固定対象・範囲

- 対象リポジトリ：`hiroshitanaka-creator/RPG-maker`。基点main：`daa41e40f64d130ce8a92921b7714fe60c58b9e6`。依頼書登録・開始点：`73df68b13191d32e3abe7629707c033c40692962`。
- 作業ブランチ：`codex/task-034-equipment-foundation-design`。変更可能なのは `docs/design/equipment-foundation-plan.md`、`docs/tasks/034-equipment-foundation-design.md` の状態行、本報告書の3文書のみ。
- 根拠確認方法：登録SHAと基点の差分が依頼書1件だけと照合し、固定版の関数本体・データ・呼出し先・保存検証・既存検査を読む。決定・事実・技術提案・未決を分け、依存表→入出力→移行→受入→実装順へ整理する。最後に差分全パス・状態行以外の本文・保護を検査し、commit/push後のCIを直接確認する。
- 保存環境は初め `work` が基点を指し、未コミット変更なし。指定リモートブランチをfetchして登録SHAへ切替。今回と無関係の未pushコミットなし。mainの更新・取り込み・マージなし。
- `AGENTS.md` 読了。checkoutに `.agents/skills` は存在せず、適用するローカルskillなし。追加委譲なし。PR15の人物原画には触れない。

## 設計結果と確認根拠

成果物：[装備基盤の技術設計](../../design/equipment-foundation-plan.md)。全9節、依存表・12職表・データ契約・移行手順・実装分割・機械受入E01〜E12・判断3件を記載。

確認した主なファイルと根拠：

| ファイル群 | 確認したこと |
| --- | --- |
| `docs/design/items-and-equipment.md`、031報告、033報告、034依頼書 | 決定原本・照合結果・追加採用発言の日時と出典。旧個数や未決の名前を採用していない |
| `docs/rpg-plan-v1.md`、`docs/experience-spec-v2.md`、`docs/integrated-mechanics-implementation.md` | 装着枠と魔物化、現行進行の優先関係、旧貸与・二刀流・形式1/2・保存の既存契約 |
| `scripts/game/integrated_progression.gd`、`data/integrated_rules.json` | armory重複拒否、武器空不可、6品、負の攻撃加算、初期値、JP閾値での一般技習得 |
| `scripts/game/game_session.gd`、`scripts/world/first_region.gd` | 通常/強制転職、未加入reserveと加入、装着解除時の武器切捨て、能力値、武器UI入口、保存/読込/明示更新、販売・報酬の貸与解放 |
| `scripts/ui/game_root.gd`、`scripts/combat/battle_state.gd`、`encounter_effects.gd`、`loadout.gd` | 共有選択UI、武器別hits、主武器差替え、反応回数、能力排他の追加箇所 |
| `data/jobs/*.json`（人間12件）、`scripts/game/job_mastery.gd`、`data/schema/job.schema.json` | 正確な職ID、戦士4技と120JP/物理20回、既得マスター保持。一般技追加だけではJP先行習得になるためマスター報酬を分離 |
| `test/unit/test_job_data.gd`、`test_job_actions.gd`、`test_save_roundtrip.gd`、統合保存/育成/mastery検査 | 全20職、保存往復全値一致、破損時状態保持、型・配列・履歴を含む比較。新規則を理由に旧assertを緩めない |
| `.scope-lock/spec.lock.json`、`.github/workflows/ci.yml` | 保護範囲、R条件、Godot4.7.2、時間上限・警告検出・CIジョブ。読取りのみ |
| `docs/asset-spec.md`、`assets/registry.json` | 文字UIの既存窓・カーソル・字体を利用可能。衣装差分不要。未定義データと原画不足を区別 |

技術提案の要点：

- 形式2の中に明示的な装備規則版を追加し、旧セーブは旧検証・旧挙動を維持。個体IDと袋/装備先の一意な所有から個数を導出し、partyとreserveを横断検証する。
- 純粋な変更計画→全状態検証→一括反映。転職・二刀流解除・侵蝕の強制転職を同じ所有移動へ接続し、袋から失われる装備を作らない。
- 両手持ちは戦士マスター確定後の別報酬。既存4技・常時特性・修練条件を維持し、旧マスターは明示移行で1回だけ習得を追加する提案。通常ロードと自動装着には混ぜない。
- 移行前の原バイト保存、SHA照合、別スロット・tmp・読戻し検証・rename、冪等キーと中断からの再開を定義。数量不明を復元済みと偽らない。
- 20×20職切替、12職可否、同率、他仲間除外、連撃と排他、旧形式・破損・中断・二重適用の正負例を定義。比較は勝率/最小最大/消費/行動数も記録する。

## 判断が必要なこと（いずれも未採用）

1. 旧貸与の個数割当て：記録された全装備枠を個体化＋未装備の解放品だけ袋へ1つ、を推奨。全人物の二刀流分を支給する案、各品1個案と影響を比較。これは新付与方針であり旧個数の復元ではない。
2. 欠ける商品の品名・開始配分と既存6品の分類対応：既存ID/名前を維持し不足分をまとめて決める案を推奨。仮名や裸の初期編成を無断採用しない。
3. 装飾効果：枠・所有・保存を先行可能に分離し、商品・効果の採用を別依頼でまとめる案を推奨。効果の完成とは区別する。

決定済みの二刀流維持、両手持ちの対象・排他・戦士マスター、旧進行/移行前保存保持は再質問しない。係数は後続の仮値比較で調整し、今回正式採用しない。

## 実行検査と限界

- `python tools/validate_assets.py --strict`：終了0、問題なし。
- `git diff <基点> <登録> --name-only`：034依頼書のみ。コード根拠は基点と登録で同一。
- `python tools/check_frozen_files.py`：終了0、保護26/26一致。
- `python tools/check_progress_docs.py`：終了0、history=26 errors=0。
- `python tools/test_locked_check_reporting.py`：終了0、23テストOK。
- `godot --version`：環境既定は **4.6.3**。Fontconfigの書込可能cacheなしの出力もあった。このバイナリでプロジェクトやゲーム検査は実行していない。指定4.7.2で走る既存GitHub CIを実行検査の証拠とし、ローカル実行と混同しない。
- `gh run list`：GitHub APIへのアクセスがForbidden。GitHubコネクターの読取りAPIでCIを確認する経路へ切り替える。
- 新装備・移行・両手持ちのゲーム実行検査はNOT_RUN（今回は実装なし）。E01〜E12は後続の受入計画であり、現状合格した検査ではない。

## 提出と残作業

設計・報告・依頼書状態だけをコミットする。コミット自身のSHAを同じコミット内へ書くことはできないため、確定HEADの完全SHA・CI実行URL・全ジョブ終了結果は最終提出メッセージに添付する。本報告の上記ローカル結果と、そのHEADのCI結果は区別する。

後続実装・判断3件・正式なバランス値・人間評価は未実施。親のレビューと統合は親側の工程であり、本担当はmain未統合で返す。新しい商品・装飾効果・原画を作っていない。実装・保護・検査・workflow・時間上限は変更しない。

設計初回コミット `e25a22efed9cc69f132d40c44bf3b246df964d74` を指定ブランチへpushし、リモートSHA一致・main基点不変を確認した。初回のpush CIは [CI](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37531661126) と [006](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37531661042)。この記録時点では開始待ちであり成功の証拠にはしない。続く文書補足で初期化関数名を実物に合わせ、旧バイナリの新保存拒否・passive能力・将来の検査コマンドを明記した。提出対象は補足後HEADで、その全CIを別途直接確認する。

- 範囲照合用Python：登録との依頼書全文を状態行だけ正規化して比較し一致。stage差分が指定3文書のみであることをassertして成功。`git diff --cached --check` も成功。素材検査は画像1154件・音15件・字体2件で問題なし。
- 作業後の未コミット変更・未pushコミットは最終push後に再照合し、残存があれば最終提出へ明記する。リモート追跡refが環境に生成されなかったため、`git ls-remote` の実ブランチSHAとHEADを直接比較する。
