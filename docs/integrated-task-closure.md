# 統合機構タスクの完了照合

> 履歴資料: 以下の進捗・未達・暫定値は記録時点の状態です。現在の実装・受入・残作業は [現在地](current-status.md) を参照してください。

2026年9月25日の改訂: 依頼者は職別行動回数の採用と暫定設計値の最終確定を指示した。現在の決定は [v1確定設計値](v1-final-values.md) を参照。以下の旧判断・暫定表記は各記録時点の履歴として区別する。

2026年9月25日。対象の依頼は「新機構の実装・実行検証」。CIの確認だけで終了せず、`integrated-design-delta-20260921.md` のD01〜D32と実装・検査を照合した。元の比較表は実装前の履歴として変更しない。旧企画の未決事項を今回の採用範囲へ無断で加えない。

## 中断理由の解消と今回の修正

実装済みコミット `9a70db9edacd71a44d985cbb932f9148e3faa205` は [CI 35972806162](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/35972806162) の全12ジョブ・全ステップが成功した。原結果は `verification/integrated-ci-success.json`。以前の支払い状態・利用上限通知による未開始は `verification/integrated-ci-blocked.json` に保持する。

再照合では、D04の職別表示に合計がないこと、D21の閾値境界検査に550戦の頻度別測定がないことを確認した。前回の機械作業完了の判断はこの2点について不十分だった。

- D04: 本番の編成へ取得済み常時特性の合計を追加。取得順に20職を積み上げ、戦闘用能力との差分、全職合計、再転職と実勝利で増加0、別インスタンスへの保存往復を検査した。
- D21: 新規4人・シード71・毎戦スライム1体・毎戦前の通常休息・祠除去なしを固定。人間職、獣系で通常攻撃、獣系で習得後に爪を各戦1回使う3方針を各550戦実行した。技は60JPで習得した後に通常APIで装着する。JP・侵蝕の注入はない。

検査は `godot --headless --path . --script res://tools/check_integrated_completion.gd`。実装前にD04の不足で終了1となった記録を `verification/integrated-completion-baseline.json` に保持し、実装後は24ケース・失敗0で終了0。合計監査のマスター状態は計算用の明示入力であり、全職習得の到達証明ではない。画面は `check_integrated_ui.gd` の6画面・92部品をheadlessとWindows実描画で検査した。

| 固定方針 | 侵蝕30への初到達 | 60への初到達 | 90への初到達 | 550戦後 |
|---|---:|---:|---:|---:|
| 人間職・通常攻撃 | 到達なし | 到達なし | 到達なし | 0.0 |
| 獣系・通常攻撃 | 150戦目 | 300戦目 | 450戦目 | 100.0 |
| 獣系・爪習得後は各戦1回使用 | 120戦目 | 220戦目 | 320戦目 | 100.0 |

これは固定方針での感度測定。全編の異なる敵・転職・祠の使い方や、人間の選択頻度を代表する統計分布ではない。人間の約60時間の実測はNOT_RUN。

## 採用案との対応

表の検査名は `tools/` の `check_*.gd` を指す。各検査の適用範囲は `integrated-validation-boundaries.md` に従い、旧保存の結果を新規開始の証明に流用しない。

| ID | 今回扱う仕様と実装 | 実行検査・根拠 |
|---|---|---|
| D01 | 20職・30敵・6章・80話・49拠点を保持 | 凍結R-01、integrated_campaign、long_fullの4経路 |
| D02 | 観察→規則→介入→世界への結果 | integrated_campaign、integrated_ui |
| D03 | 習得・装着・使用権・常時特性を分離 | R-02/R-03、integrated_combat、integrated_progression |
| D04 | 職別内訳に合計表示を追加。既存総予算を保持 | 今回のintegrated_completion、integrated_ui |
| D05 | 得意タグ割引と形態MP加算を同じ計算で表示・実行 | integrated_progression、integrated_combat |
| D06 | 共通観察を実行し、知識を保存 | integrated_combat、integrated_ui |
| D07 | 対象再選択と不発時の無消費を明文化 | integrated_combatの対象・MP境界 |
| D08 | 専心の装着・結び付け・1機会・失効 | integrated_combat、integrated_ui |
| D09 | 導電を物理の全打へ適用し1行動で消費 | integrated_combat |
| D10 | 増幅・過負荷・重複拒否・次機会の制限 | integrated_combat |
| D11 | 推奨どおり先行防御を維持 | 保護されたR-05、integrated_combat |
| D12 | 偏向・単体物理の護衛・全打・全体魔法除外 | integrated_combat |
| D13 | 共有封緘・充填中断・崩し・期限 | integrated_combat |
| D14 | 予告・反射場・維持装置・敵の実行入口 | integrated_combat、integrated_campaign |
| D15 | 武器別4打・二刀流。爪は身体能力として別処理 | integrated_combat、integrated_progression |
| D16 | 基礎式を維持して補正を接続 | R-05、integrated_combat |
| D17 | 行動単位の反撃・MP還元・追加効果上限 | integrated_combat |
| D18 | 予告・解除可能な残留反応と勝敗確定順 | integrated_combat、integrated_campaign |
| D19 | マスター前の予告・取消不変・操作権を維持 | R-04、integrated_ui、worst_case |
| D20 | 全8形態の加算補正を保持し、弱点・有料技加算を追加 | R-04、integrated_combat、integrated_campaign |
| D21 | 侵蝕0.2/0.1・旧保存・境界と550戦の測定 | integrated_progression、今回のintegrated_completion |
| D22 | 人物×職業のJP半減端数 | integrated_progression |
| D23 | 祠後の技保有・マスター履歴・再習得を分離 | integrated_progression、integrated_storage |
| D24 | EXPとJPを分離。成長で無料蘇生しない | integrated_progression、integrated_builds |
| D25 | 全職へ技配分。実際の敵分類で報酬と学習順を接続 | integrated_campaign、integrated_progression、long_full |
| D26 | 4職の取得済み噂・図鑑と実解放条件 | integrated_campaign |
| D27 | 今回はJPマスターを維持。旧職別行動条件は未解決 | R-02/R-04。旧エスカレーションを解消扱いにしない |
| D28 | 知識の段階・予測・代償・512×288の通常操作 | integrated_combat、integrated_ui |
| D29 | 無料帰還を保持。同一戦闘局面で資源を保持 | integrated_combat、worst_case、long_full |
| D30 | 解法の通路・貸与・補給を保存・再訪へ反映 | integrated_campaign、long_full。既存54回収を保持 |
| D31 | 強制暴走AI等の不採用と固定職数・章数を維持 | 今回の実装範囲・変更差分。禁止要素を新規採用しない |
| D32 | 旧固定受入と新機構の検査を区分し、両方実行 | 凍結8verify、CI12ジョブ、新機構8検査 |

今回の変更は合計表示・追加検査・CIへの追加・記録。保護ファイル、数値、ダメージ式、報酬、勝率の条件は変更していない。追補前のCI成功を追補コミットのCI成功と同一視しない。追補後はコミットに対応するCI12ジョブを再確認する。

## 残る項目の依存関係

| 項目 | 現在の扱い・ブロック理由 |
|---|---|
| 初見の理解・面白さ・テンポ・約60時間 | `PLAYTEST_QUEUE.md`。人間の入力と感想が必要。自動実行から補完しない |
| 旧職別行動によるマスター | 既存エスカレーション1件。JPだけの到達を要求するR-02/R-04との仕様衝突。今回の合計表示とは独立し、未実装を完了に数えない |
| 外部提供画像の生成条件・他用途の許諾 | 本人情報を必要とする既存の来歴確認。公開・外部配布は今回の対象外 |

凍結8verifyは今回もPASS、verify未定義0。openフォルダの4記録中3件は本文冒頭で解決済み、未解決は上記1件。予算設定は継続40回・停滞3回。stateには使用回数の記録がないため消費回数は不明。これらを今回勝手に変更しない。
