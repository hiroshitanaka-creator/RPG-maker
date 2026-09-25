# 統合機構の実装と実行検証

2026年9月25日の後続改訂: 職別行動条件の採用と設計値の確定は [改訂記録](mastery-actions-delivery.md) を参照。この文書のJP方式維持・検査件数は改訂前の実行記録であり、新ルールの未検証部分の証明には使わない。

対象は依頼者が実装を指示した統合企画書の推奨案。60時間目標、20職、30敵、80話、49拠点、既存の物語の回収を維持する。数値は `integrated-mechanics-implementation.md` に記した暫定設計値。人間の面白さ・理解・所要時間を機械検査で認定しない。

## 実装した入口と挙動

| 項目 | ゲームでの操作と結果 | 主な実装 |
|---|---|---|
| 観察と知識 | 現地の観察、戦闘の共通「観察」、編成の覚え書き。事実・見立て・確認済みを保存し、未確認の敵規則の確定ダメージを予測画面で伏せる | `game_session.gd`、`encounter_effects.gd`、`game_root.gd` |
| 構築と出力 | 専心を装着した攻撃技へ結び付け、導電・増幅・過負荷・4連撃・二刀流を通常コマンドから使う。装着枠・準備行動・MP・次の行動制限を実行時にも検査 | 同上、`integrated_rules.json` |
| 防御と妨害 | 偏向・護衛・封緘・反射場・維持装置・反撃・還流・残留解除。対象区分、攻撃1回と打数の区別、期限、重複・再反撃・還元の上限を持つ | `battle_state.gd`、`encounter_effects.gd` |
| 敵の行動 | 機構に沿う予告と行動を本番の行動選択へ接続。同じ戦闘内で局面が変わってもHP/MPや付与を初期化しない | 同上 |
| 成長と魔物化 | EXPとJPを分離。侵蝕0.1単位、JP半減の端数、形態の弱点・MP加算、マスター前の予告、祠後の独立した再習得量 | `integrated_progression.gd`、`game_session.gd`、`data/jobs/` |
| 世界への結果 | 80話＋49拠点へ機構を配分。装置破壊・封緘完成は通路、導電突破・残留解除は武器貸与、場の解除は一度だけの補給へ反映。予約しただけでは解決扱いにしない | `integrated_campaign.json`、`integrated_campaign.gd` |
| 保存と引継ぎ | 新規開始は形式2。形式1は読込みだけで勝手に更新せず、画面から明示更新できる。全変数の型・値・キー・配列順序を往復検査 | `game_session.gd`、`saved_value_types.gd`、`save_state_comparison.gd` |

## 検証の扱い

ローカルの新機構・既存受入・全編到達検査を実行した。2026年9月24日のGitHub CI `35972806162` は実装コミット `9a70db9` の全12ジョブで成功し、開始できなかった制約は解消した。2026年9月25日の依頼範囲の再照合で見つけた合計表示と測定記録の不足は、[タスクの完了照合](integrated-task-closure.md)に追記した。この追補に対するCIは、追補コミットの実行結果と区別する。

| 検査 | 実行記録 | 現状 |
|---|---|---|
| 凍結R-01〜R-08 | コミット時に元のverifyを実行。保護ファイル21件のハッシュを照合 | 全8件PASS、21件一致 |
| 新機構の固定値・状態遷移 | `verification/integrated-combat-current.json` | 20ケースPASS |
| 育成・旧保存・実戦での習得 | `verification/integrated-progression-current.json` | 10ケースPASS。3人/4人の新規開始からJP注入なしの習得・魔物化・再習得を含む |
| 配分・通路・不正入力拒否 | `verification/integrated-campaign-current.json` | 129配分、6機構、320通路PASS |
| 通常画面 | `verification/integrated-ui-headless.json`、`verification/integrated-ui-native.json` | 追補後は6画面・92部品。全20職取得時の合計表示と個別内訳を含む。headlessと実描画を区別 |
| 常時特性の合計・侵蝕の固定550戦 | `verification/integrated-completion-current.json` | 24ケースPASS。20職の合計、再取得・保存、3方針計1,650戦。実際の全編遭遇や人間の選択頻度の分布とは区別 |
| 圧縮保存の互換・破損拒否 | `verification/integrated-storage-current.json` | 43検査PASS。1万件の合成履歴と4件の実保存で、状態・型・値・順序を照合 |
| 同予算の構成比較 | `verification/integrated-builds-current.json` | 240JP/4800EXP、3構成×6機構×100シード。勝率・平均/最大ターン・生存者の残MPを記録 |
| 既存の固定勝率・終了率 | `verification/provisional-battle-acceptance.json` | 12,000試行PASS。各条件の勝率41.5〜59.2%。10ターン以内11,625/12,000。元の初期値を固定 |
| 全80話・3人4人・両順序 | `verification/long-full-*.json` | 圧縮保存を含む最終版の4条件すべてPASS。各80話・80現地操作・550戦。保存の1MiB・2秒条件も維持 |
| 既存CIの独立した受入検査 | `verification/integrated-local-suite.json` | 48件PASS（中断前18件＋再開後30件）。保存のみの変更後に関係12件を再実行してPASS。各実行版・終了値・ログ・結果要約を保持 |
| 高頻度履歴 | `verification/long-record-capacity.json` | 72,000件の型・値・順序を保持。315,191バイト、保存930ms、読込み2,223ms。暫定16MiB/各5秒以内でPASS |
| GitHub CI | `verification/integrated-ci-success.json` | `9a70db9` の全12ジョブ成功・スキップ0。`integrated-ci-blocked.json` は以前の未開始の履歴として保持 |

固定ACと旧数値の互換検査を分けた理由は `integrated-validation-boundaries.md`。敵の本番行動選択の接続漏れは、直接呼出しだけの検査では不十分だったため、予告と実行を通る検査に追加してFAILを再現してから修正した。修正前の記録は `verification/integrated-enemy-dispatch-baseline.json`。

検査プロセスの中断が発生したため、全編検査には `--audit-session` による二世代の再開記録を追加した。ゲーム保存のSHA-256、ゲームコード、検査コード、初期状態、保存内の実勝利履歴と集計を照合する。条件が一致しない記録は拒否する。従来の `--resume-qa` による診断再開を、新規開始の証明へ昇格させるものではない。最終の4条件はこの記録を導入した後に新規開始している。

既存受入検査は、中断前に終了値を得た18件と残り30件を独立記録に分ける。終了値がない途中実行は成功に数えない。再実行のためのコマンド一覧と照合は `tools/run_integrated_local_suite.py` に保持する。

圧縮前の4条件は進行・戦闘・回収の照合まで到達し、保存容量だけが上限を超えた。履歴は `verification/history/integrated-uncompressed-long-*.json` に保持した。保存量を抑えるため履歴を消す処置は行わず、保存用の包みを可逆圧縮する処理を追加した。実際の4件の全編保存と1万件の合成履歴で、旧JSON互換・型・値・順序・破損時の拒否を別途検証している。この再保存検査を最終版の全編到達に代用しない。

## 残る確認

| 残る項目 | ブロック理由・成立条件 |
|---|---|
| 初見の理解・面白さ・テンポ・60時間の実測 | NOT_RUN。本人の初見体験・理解・実時間を機械の入力回数や実行秒数から認定できないため、`PLAYTEST_QUEUE.md` の既存項目とPT19〜PT21で別に記録する |

採用した新機構の対応はD01〜D32を[タスクの完了照合](integrated-task-closure.md)で追跡する。以前の「独立して着手できる実装・ローカル検証は終えている」という判断には、D04の合計表示とD21の測定記録の不足があった。今回この2点を補った。CIの開始制約をエンジンや受入条件の変更で回避したものではない。

職別行動をマスター必須条件へ追加する旧衝突は、今回の採用範囲とは別の仕様判断として残す。凍結要件どおりJPマスターを維持する推奨案を実装しており、旧衝突を解消したとは扱わない。

## 全編の実行結果

| 人数 | 進行順 | 話数 | 戦闘数 | 保存往復 | 別プロセス再開 | 結果 |
|---|---|---|---|---|---|---|
| 3 | 正順 | 80 | 550 | 1780 | 0 | PASS |
| 3 | 逆順 | 80 | 550 | 1780 | 1 | PASS |
| 4 | 正順 | 80 | 550 | 1780 | 0 | PASS |
| 4 | 逆順 | 80 | 550 | 1780 | 0 | PASS |

ゲームコードの実行版ID: `8f0e796ed660489980bb2ee49e5a847aba0e3fa27342f5507ca133577f526c08`。このコードの検査中にゲーム・検査コードが変わっていないことも各完走で照合した。機械の実行秒数を人間の60時間の実測へ加算しない。

## 変更ファイル

比較元は `d4b5bef`。全134ファイルの一覧は [変更ファイル一覧](verification/integrated-change-manifest.json) に記録した。主な変更は `scripts/combat/`、`scripts/game/`、`scripts/ui/game_root.gd`、`scripts/world/integrated_campaign.gd`、`data/jobs/`、`data/integrated_*.json`、検証用の `tools/` と記録類。ゲームに使う画像は今回変更していない。
