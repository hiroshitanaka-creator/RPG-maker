# 082 祠の会話・自動開始・中断復帰

基点 main：`6c996d5c37fd384e679bb23dd59113c99494790c`。開始時の `git ls-remote origin refs/heads/main` と一致。080/081は再実装していない。
初回実装：`2ea3c32ada2713bbfcd0582f5bd1c9eaf401d36a`。古いメニュー操作の修正：`eb423ad0bc269ac737da80174ff812d63861d26e`。古い決定ボタン通知の修正：`3216b3aaa3962307361de2e7ae8b0d0df84ab99a`。重複再開の保持：`e675aca03d7a726379f88ad1529a2597f38de405`。最終検証の本番コードは最後のSHAに固定する。
作業ブランチ：`codex/task-082-shrine-conversation-20261028`。mainへの書込み・マージなし。

## 変更

- `scripts/game/game_session.gd`：成功した祠への遷移の後にだけ自動開始。導入の前提、一時会話の排他、最終確認、初期4職の利用条件を接続。ロード時に一時状態を破棄する。
- `scripts/ui/game_root.gd`：専用の場面ID/実行番号を保持し、通常確認をセッションへ渡す。通常ロード・チェックポイント読込・起動中の戦闘前復帰・タイトルからの再開時に安全なWORLD復帰を確認する。キーリピートを拒否する。
- `scripts/world/region2_shrine_story.gd`、同 `.uid`：本文表示と一時ページ/実行番号。異なる場面・古い実行・古い/先のページを拒否する。
- `data/region2_shrine_scenes.json`：[承認資料](https://github.com/hiroshitanaka-creator/lucca-workspace/blob/0cd7dc2070e651b353554422c361c02b0aedd160/projects/rpg-maker/drafts/region2-story-connection-preparation-2026-10-14.md)第11節の9ページを原文のまま格納。第12節と本人1.A/2.Aで採用された範囲を使用。
- `tools/check_region2_shrine_story.gd`、同 `.uid`：人工境界のAPI正負例、実在旧保存、通常UI操作、中断/反復/復帰の検査。
- `tools/check_region2_shrine_story_data.py`：本文・引用・話者・順序の原文照合と13件の改変負例。
- 本報告と `docs/verification/task-082/`：原ログ、実行コマンド、終了値、固定SHA、証拠目録。

## 保存と職業の境界

完了の通常確認で `progress_flags.region2_shrine_seen` と `progress_flags.region2_shrine_jobs_unlocked` を一度だけtrueにする。どちらも既存のString/bool拡張契約内であり、ページ・実行番号は保存しない。保存形式・検証関数・保護対象を変更しない。追加前の保存はキー欠落を未完了として扱う。旧訪問履歴を既読に変換しない。完了前の全ページの保存から冒頭へ再開し、完了後は再演しない。

新しい初期4職ゲートはslime/beast/plant/shellだけを許可する。全8職共通の `monster_jobs_unlocked` は変更しない。`actor.unlocked_jobs` へ基本職を入れない。転職共通条件、上級条件、既使用の保持順序、first_regionのない旧本編を維持する。

**未決の依存部分**：旧保存で `monster_jobs_unlocked=true` の場合は、現行コードがundead/bird/dragonを既に許可し、spiritも修練と侵蝕で取得しうる。保存には主の勝利/受取の根拠がなく、spiritの `unlocked_jobs` も修練取得と受取を区別しない。未使用まで受取済みにする移行も、使用済みを取り上げる移行も未承認。このPRは旧共通ゲートの意味を維持し、この依存部分の移行と任意主の取得接続を保留する。新しいS10完了による任意4職の追加解放はない。任意4職全体の完成を主張しない。

## 検証

固定実装SHAの別checkoutで検査を実行し、`docs/verification/task-082/final-validation/execution.json` にコマンド、作業場所、環境、上限、終了値、判定、原ログSHA-256を記録する。原verifyの判定は既存 `run_locked_checks.judge_output` を使用する。最初の版の実行記録 `execution.json`、eb423adの補助全体回帰 `final/execution.json`、3216b3aの `latest/execution.json` と最終e675acaの結果を区別する。

作業ツリーでの先行確認：本文9ページ/改変負例13件が成功。集中実行は279条件成功（`focused-fifth.log`）。最初の環境既定のインポートはユーザーディレクトリへの書込みエラーを出したため成功扱いしない。以降はクラウドworkspace内のXDG領域を使用。集中検査の初回パースエラーと人工保存条件/既存API名の誤りも原ログを保持し、既存契約に合わせて検査入力を修正した。既存検査器・期待値・上限の変更はない。

追加負例で、古いメニュー操作が会話中に届くとUI/実行番号を失う不具合を再現した（`stale-ui-red.log`）。確認・タイトル中断・ロード以外の古いUI通知を会話中に拒否し、同じ負例を含む283条件で成功を確認（`stale-ui-green.log`、`focused-final.log`）。この修正後の固定SHAでR-01〜R-08も全て再実行して成功した。

さらに画面の再生成直後の古い決定通知を4経路で再現した（`stale-confirm-red.log`）。決定ボタンの生成時に場面ID・実行番号・ページを固定して渡し、前ページの二重通知、ロード前の画面、新旧の別人物会話との通知混入を拒否する（`stale-confirm-green.log`）。3216b3aの固定SHAで集中290条件、R-01〜R-08、導入・通常画面・復帰・保存・081継続APIの関連回帰、保護照合の19コマンド全件が終了0、エラー/警告なしで成功した。082の新規集中検査はCI設定を変えず、固定checkoutで明示実行している。

「続ける」の直接の重複呼出しでも進行中の会話を保持する境界を再現し、再開処理を冪等にした（`duplicate-resume-red.log` / `duplicate-resume-green.log`）。最終e675acaでは集中293条件、上記19コマンドを全件再確認し、全て終了0・エラー/警告なし。R-01〜R-08は原判定のまま全件PASS、保護対象26件は検査前後とも26件一致。

初回の実描画回帰はVulkanドライバー不足の警告・エラーで失敗した。照合のPASS行だけで成功扱いせず原ログを保持する。XvfbとMesa Vulkanをworkspace内へ展開し、絶対パスを持つICD設定でllvmpipe/Vulkanの警告なし起動を確認した（`vulkan-probe-fixed.log`）。パッケージ出所・hash・設定は `environment.json`、修正後の各検査の環境は `final/execution.json` に残す。ドライバー変更のために本番設定や検査器を変更していない。

追加実行した081の当時限定検査 `check_task081_port_data.py` は、081着手時BASEに対する親文書2件の不変条件でFAILを出す。082基点main `6c996d5c37fd384e679bb23dd59113c99494790c` でも1235件中同じ2件だけFAIL、081完成 `7d85b1100b7d8bea9cdffdad67c4ece72c739bbf` では原検査の1235件全件PASSを確認した（`historical-stage-081.json` と各原ログ）。元の検査器・assertion・期待値・FAIL判定は変えていない。この2条件は081固定完成版で維持し、現在の継続条件は親文書を082基点から変えないことへ対応させる（`scope-audit-final.json`）。補助回帰の残る1233条件も元の検査器で全件成功した。

eb423adでの補助全体回帰は64コマンド中62件成功、2件FAILを保持する。上記081の旧段階検査と、011本体の固定/最新の資源・通行・保存・実描画が成功した後の027「毎歩通知あり撮影」の180秒タイムアウトである（`final/regression-records.tar.gz` 内の `task-027/fixtures/battle-capture.log`）。上限や検査を変更せず、失敗をPASSへ変換していない。最終版の現在条件は関連19コマンドとGitHubの原CIで確認する。

最終e675acaのGitHub CI：全5ワークフロー・38ジョブがcompleted/success。`final-validation/github-workflows.json` と `github-checks.json` に完全SHA・各ID・URL・開始/終了・結論を保存した。原CIの各コマンド・各上限・判定・固定版/最新の世代分離を変更していない。新規集中検査は上記ローカル実行の証拠を使用し、CIに含まれると偽っていない。

ドラフトPR作成は自動承認レビューで拒否された。対象はこのブランチからmainへのdraft作成だけで、理由は「GitHubへの外部操作について明示的な本人承認を確認できない」。API結果は拒否であり、読取り照合でも該当PRは0件。再試行・別経路への切替えはしていない。`docs/verification/task-082/pr-blocker.json` に操作・対象・理由・再開条件を記録する。検証とブランチへの証拠保存は独立して継続する。

解消記録：親が追加取得した本人原文の証拠を受領後、該当PRが0件であることを再確認し、同じAPI・同じ対象へのドラフト作成を1回だけ再試行した。2026-10-28 03:35:42 UTCに [draft PR #63](https://github.com/hiroshitanaka-creator/RPG-maker/pull/63) 作成成功。最初の拒否記録は残し、`pr-create-result.json` と `pr-blocker.json.retry_outcome` に解消結果を追加した。経路変更・再試行の反復・mainへのマージはしていない。カスタムルールの写しは保存していない。

## 未達・未検証

- 人物の初配置画像の採否は別作業。world配置・原画・台帳を変更しておらず、視覚的に統合されたS10場面の完成を意味しない。
- 任意4職の旧保存移行・任意主の取得接続は上記根拠が未決。S11、鍵、戦闘、報酬の新規則は本依頼の実装範囲外。
- 人間による手触り評価は未実施。機械検証の成功と区別する。

`docs/tasks/README.md` と `docs/decision-log.md` は親担当のため変更していない。親記録用の技術判断：既存のbool拡張契約内で2フラグを原子的に確定し、初期4職の専用条件を追加した。理由は旧共通ゲートで任意4職まで誤解放しないため。戻す場合は本実装コミットを新しい訂正コミットで差し戻せる。履歴の書換えは不要。
