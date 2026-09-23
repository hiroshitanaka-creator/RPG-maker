# 統合機構の実装と実行検証

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

この記録は検証中。最終の全編・受入検査が終わるまでは全件完了と扱わない。

| 検査 | 実行記録 | 現状 |
|---|---|---|
| 凍結R-01〜R-08 | コミット時に元のverifyを実行。保護ファイル21件のハッシュを照合 | 全8件PASS、21件一致 |
| 新機構の固定値・状態遷移 | `verification/integrated-combat-current.json` | 20ケースPASS |
| 育成・旧保存・実戦での習得 | `verification/integrated-progression-current.json` | 10ケースPASS。3人/4人の新規開始からJP注入なしの習得・魔物化・再習得を含む |
| 配分・通路・不正入力拒否 | `verification/integrated-campaign-current.json` | 129配分、6機構、320通路PASS |
| 通常画面 | `verification/integrated-ui-headless.json`、`verification/integrated-ui-native.json` | 6画面・71部品。headlessと実描画を区別 |
| 同予算の構成比較 | `verification/integrated-builds-current.json` | 240JP/4800EXP、3構成×6機構×100シード。勝率・平均/最大ターン・生存者の残MPを記録 |
| 既存の固定勝率・終了率 | `verification/provisional-battle-acceptance.json` | 12,000試行。元の初期値を別JSONとハッシュで固定 |
| 全80話・3人4人・両順序 | `verification/long-full-*.json` | 保存容量を修正した最終版で再実行中。圧縮前は4件とも80話・550戦に到達したが、1MiB上限を超えた |
| 既存CIの独立した受入検査 | `verification/integrated-local-suite.json` | RUNNING。各コマンドの終了値と診断ログを逐次記録 |
| 高頻度履歴 | `verification/long-record-capacity.json` | 72,000件の型・値・順序を保持。暫定16MiB/保存・読込み各5秒の検査 |
| GitHub CI | `verification/integrated-ci-blocked.json` | BLOCKED_BEFORE_EXECUTION。GitHubの支払い状態または利用上限の通知によりジョブ未開始。ローカルPASSをGitHub CIの成功へ置換しない |

固定ACと旧数値の互換検査を分けた理由は `integrated-validation-boundaries.md`。敵の本番行動選択の接続漏れは、直接呼出しだけの検査では不十分だったため、予告と実行を通る検査に追加してFAILを再現してから修正した。修正前の記録は `verification/integrated-enemy-dispatch-baseline.json`。

検査プロセスの中断が発生したため、全編検査には `--audit-session` による二世代の再開記録を追加した。ゲーム保存のSHA-256、ゲームコード、検査コード、初期状態、保存内の実勝利履歴と集計を照合する。条件が一致しない記録は拒否する。従来の `--resume-qa` による診断再開を、新規開始の証明へ昇格させるものではない。最終の4条件はこの記録を導入した後に新規開始している。

既存受入検査は、中断前に終了値を得た18件と残り30件を独立記録に分ける。終了値がない途中実行は成功に数えない。再実行のためのコマンド一覧と照合は `tools/run_integrated_local_suite.py` に保持する。

圧縮前の4条件は進行・戦闘・回収の照合まで到達し、保存容量だけが上限を超えた。履歴は `verification/history/integrated-uncompressed-long-*.json` に保持した。保存量を抑えるため履歴を消す処置は行わず、保存用の包みを可逆圧縮する処理を追加した。実際の4件の全編保存と1万件の合成履歴で、旧JSON互換・型・値・順序・破損時の拒否を別途検証している。この再保存検査を最終版の全編到達に代用しない。

## 残る確認

- GitHub側でActionsを実行可能にし、最終コミットのCIを実行する必要がある。エンジンや受入条件を変えてこの制約を回避しない。
- 人間による初見の理解・面白さ・テンポ・60時間の実測はNOT_RUN。`PLAYTEST_QUEUE.md` の既存項目とPT19〜PT21に分離してある。
- 職別行動をマスター必須条件へ追加する旧衝突は解消扱いにしない。今回の推奨案は凍結要件どおりJPマスターを維持する。
