# 職別行動条件の改訂・設計値の確定

2026年9月25日の依頼1・2への対応。依頼3は番号のみで本文がないため、追加内容を確認中。現在の設計値と20職の条件は [v1確定設計値](v1-final-values.md) に記載した。

## 実装した内容

- JPと人物別・職別の成功行動回数の両条件でマスターする。盗賊10回・僧侶5回・獣系20回を維持し、他の17職にも1条件ずつ定義した。
- 成功行動は戦闘結果から計数する。予約・取消・不発・多段・予測画面・二重報酬で水増ししない。回数・旧マスターの引継ぎ情報を保存対象へ加えた。
- 獣系は8JPで威嚇を習得し、物理与ダメージ25%減の萎縮を付与できる。封緘の完成による防御低下も状態異常として数える。
- 編成・転職比較・魔物化予告に修練の条件と現在回数を表示した。JPだけで必ず魔物化するという説明は改訂した。
- 旧形式1/2は読込みだけで更新しない。確認して引き継ぐ場合に限り、取得済みマスターを維持し、未記録の修練は0から開始する。

## 現在の検証記録

| 検査 | 記録・扱い |
|---|---|
| 改訂前のFAIL | `verification/mastery-amendment-before/test-failure.log`。新しい進捗APIがなく2件FAIL |
| 改訂後の凍結8verify | `verification/mastery-locked-current.json`、全件PASS。旧アサーションは削除せず、マスター入力の行動実行を追加 |
| 単体テスト | 17件PASS。全20職のJPだけ／行動だけの未達、両条件、転職、保存、予測・取消・多段、旧保存移行を検査 |
| 威嚇と状態異常 | `verification/integrated-mastery-current.json`。26検査PASS。実ダメージ、期限、同時予約後の不発、封緘完成を含む |
| 新機構の画面 | `verification/integrated-ui-native.json`。Windows実描画6画面・93部品PASS |
| 全画面・表示遅延 | `verification/preplay-ui-native.json`。222画面・172目標、4種類×100回を測定。`check_preplay_render_record.gd` の版・生値・閾値照合PASS |
| 既存独立48検査 | `verification/mastery-local-suite-final.json`。実行途中の件数と完了済みの終了値を保持。RUNNINGを全件PASSと読まない |
| 全80話 | 新規開始から再検証中。初期の自動方針の敗北は `verification/mastery-long-*-policy-failure.json` に保持。途中結果を完走として扱わない |

全編の旧方針は、行動条件が未達のまま修練職に留まることや、習得前に魔法役へ切り替えることで敗北した。新方針は既存の課題戦で技を習得して担当職へ持ち越し、残留反応への防御は撃破見込みのターンに行う。追加稼ぎ戦闘・JP注入・勝敗の書換えは行わない。固定ACの初期状態と行動方針は変更していない。

後続の確認: Windowsの3人正順は80話・550戦・1,780保存往復でPASSした。記録は `verification/mastery-long-forward-policy6.json`。CIの3人逆順は69話の戦闘で未達となったため、`verification/mastery-long-reverse-first-failure.json` に保持した。ゲームコードの実行と自動入力方針の違いを区別する。

敗北したパーティを基に、開始時の薬数0/1/3/6/12/24で装着を比較した。元ログに開始薬数がないため完全再現とは呼ばない。旧装着は6/12/24個で敗北し、既得の堅守と氷技を使う装着は全6条件で勝利した。封緘を借用する別案も比較したが、採用した修正は既得技の装着である。`tools/check_mastery_charger_probe.gd` は採用案の6条件に未達があれば終了1となる。単体比較を全80話の完走の代用にはしない。

自動操作方針が転職前のスナップショットから装着を選ぶ不備も、`check_mastery_role_transition.gd` で修正前FAILを再現した。転職後の実際の職へ参照を変更し、同じ検査がPASS。開始済みの旧CI `36080247991` はこの不備を含むため中止し、ログを保持した。修正後のコミットで全編を再検証する。

独立48検査の今回の実行は完了し、47件PASS・保護台帳照合1件FAIL。`verification/mastery-local-suite-final.json` に全終了値を記録した。表示遅延はheadlessの時間ではなく、Windows実描画の測定と版照合を使用した。

20連作の両選択・3人4人は、CIで320ケース・1,920戦・6,080保存往復がPASS。原結果を `verification/mastery-ci-branches.json` に保持した。ジョブ全体は、その後の保護ハッシュ照合でFAILとなっており、CI全体の成功とは扱わない。

## 保護台帳の反映

改訂の採用判断は依頼者から受領済み。`.scope-lock/frozen-files.json` の更新はPreToolUseフックに拒否された。拒否文は「このコマンドは凍結契約の一部である `.scope-lock/frozen-files.json` を変更または削除する」として `.scope-lock/**` を示している。別の手段で迂回していない。

反映案は [mastery-frozen-files-proposed.json](verification/mastery-frozen-files-proposed.json)。対象は既存保護ファイル3件の承認済み変更と、新規テスト・UIDの2件追加、計23件。元の台帳・原文と変更前後のハッシュを `verification/mastery-amendment-before/` と `verification/mastery-amendment-protected-changes.json` に保持する。

台帳の反映と一致確認、およびその版のCI成功までは契約改訂手続き全体を完了とは扱わない。現行の緑のmainを維持するため、この状態は専用ブランチへ保存する。

## 未実施・対象外

人間の面白さ・理解・難易度・約60時間の実測はNOT_RUN。評価基準の採用と、良い評価を得たことを区別する。依頼者本人の試遊を必須にしない。外部公開・配布は対象外。
