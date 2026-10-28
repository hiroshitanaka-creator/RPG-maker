# 084 採用済み遺跡の入口と帰路接続

基点 main / origin/main：f9169ac4048e98229d34692bc1e9efb6a0a3efaf。
作業ブランチ：codex/task-084-region2-ruins-connection-20261029。mainマージ・approve・親記録編集は行わない。
指定モデル：GPT-6.1 Sol / High。実モデル・推論設定を照会するAPIはなく、実値は未確認。
指定3スキルはカタログとcheckoutの .agents/skills に不在。唯一のstorytellerは本文・創作変更を行わないため適用しない。既存固定検査・R verifyをそのまま使用する。
開始前未追跡：scripts/game/equipment_rules.gd.uid、tools/check_equipment_rules.gd.uid。開始前未pushコミットなし。この2件は含めない。

## 実行前の計画とログ名

依頼書の指定座標を採用し、既存完了フラグだけで入場を制限する。出口は完了フラグを要求せず旧内部保存からも使う。旧補正spawn・MAPS・LINKS・素材・保存形式は保持する。Atlasは既存siteの入口で示す。
全ログは docs/verification/task-084/logs/。開始前に次の具体名を予約：frozen-before.log、import-initial.log、runtime-red.log、runtime-green.log、data-red.log、data-green.log、capture.log、import-final.log、frozen-final-before.log、assets-strict.log、task011.log、task011-boundary.log、shrine-data.log、shrine-runtime.log、static-data.log、static-runtime.log、second-coast.log、R-01.log〜R-08.log、frozen-final-after.log。必要な追加試行ログは同じフォルダに置き、成功ログへ上書きしない。
XDGとQA保存prefixを隔離し、既存検査が出す旧証拠は別checkoutで受ける。正式検査は固定SHAで実行する。

状態：作業中。実装・検査・PR結果は実行後に追記する。

## 実装と判断

本番/検査器固定SHA：`bc353deb55f04ba3f8e60002d7f4e2789feddf2d`。通常push後にoriginの作業ブランチを確認した。固定SHAの別checkout `/workspace/task084-verification` で検証し、既存082/083/011の証拠は作業ブランチで上書きしない。

- scripts/world/first_region.gd：既存の徒歩世界移動成功後にRegion2Ruins.enterを1行追加。会話排他は既存GameSessionを通る。
- scripts/world/region2_ruins.gd：既存COMPLETE_FLAGだけで世界入場。内部出口は完了条件を要求しない。旧spawnと既存stairs処理を保持。
- scripts/world/first_region_view.gd：採用済みfirst_cave_entrance.pngを既存64×64の入口描画方式で再利用。新しい外観・画像・地形を作らない。
- scripts/ui/first_region_atlas.gd：描画が使うcurrent_cellを分離し、遺跡・第2村・第3港を既存siteの世界入口へ対応。第1地方/第2港の表示を継続検査。
- world/region2_ruins.json、tools/task011_ruins_defs.py、tools/build_task011_ruins.py：接続メタデータだけを追加・整合。旧MAPS/LINKS・部屋・床・上層・画像生成算法は不変。
- tools/check_region2_ruins_connection.gd/.uid、tools/check_region2_ruins_connection.py、tools/capture_region2_ruins_connection.gd/.uid：新規正負例、独立BFS、全bytes再現、本番UIの実キーと保存/復帰を検査。
- docs/tasks/084-region2-ruins-connection.md：固定原本を全bytes一致で保存。Git blob `2d5ae7e841c0b436cb2b40cc1f57d7003ff59232`。
- 本報告とdocs/verification/task-084/：実行記録、原ログ、画像、検査対応、hash目録、PR拒否記録。全変更pathはchanged-paths.txtへ保存する。

親担当docs/tasks/README.md・docs/decision-log.mdは変更しない。親記録用判断：入口条件をCOMPLETE_FLAGに限定し、保存受理/出口は既存互換を守る。帰着と接触を1マス離し、通常入力を1回ずつ処理する既存移動経路を用いる。戻す場合は本実装commitを新しい訂正commitで差し戻せる。履歴改変・mainへの直接書込みは不要。

## 先行失敗と撮影

runtime-red.logの最初の試行は新規検査の型推論エラーであり、入口未接続の証拠とはしない。検査のString型を明示したruntime-red-corrected.logでは220条件中7条件が未接続としてFAIL。data-red.logは接続定義/defsの2条件FAIL。実装後の新規集中は257条件全件成功し、生成再現を含むdataは62条件成功。

capture-atlas.logは43条件を満たしたが、検査が画面を続けて閉じたためdeferred focusのERRORが1件出た。成功扱いしない。本番コードを変更せず、検査側で画面切替の完了を待ってから次を押すよう訂正し、capture-focus-corrected.logは43条件・6画面・終了0・警告/ERRORなし。

1階採用背景を担当環境で実見した。着地[18,19]と接触[18,20]は南の石床に立ち、旧候補y21の壁は開けていない。世界入口は実見した既存first_cave_entrance.pngの石造入口を既存表示倍率で再利用。既存目標ruins-temple.jpgと並べて構成を照合したが、目標画像の画素は使用しない。原画・採用PNG・台帳を1バイトも変更していない。

実Godot 512×288：before-complete.png、after-complete-entry.png、interior-return.png、loaded-return.png、interior-atlas.png、returned-atlas.png。人工境界保存からViewport.push_inputによる方向/決定キーで操作し、キー押下・解放・echo・前状態・時刻をinput-trace.jsonへ記録した。S10の全9ページは本番決定キーで完了した。長距離移動は人工境界へ分離しており、本人の初見プレイや全行程プレイとは報告しない。

本番checkpointの_persist_checkpoint/_load_checkpointと、手動保存・タイトル/ロードを個別確認。APIだけの保存経路と実UIのcheckpointを区別する。退出時の入力反復・保持で即再入場せず、下向き次歩は世界の[176,93]へ進んだ。独立BFSで世界入口/村港入口を避けて村近傍・港近傍・浅瀬へ歩行可能と照合した。世界の遭遇率0.025は保持しており、無遭遇の帰路とは報告しない。

## draft PR作成の拒否

GitHub連携のcreate_pull_requestで同repositoryの作業ブランチからmainへのdraftを1回要求し、自動承認レビューが拒否した。理由は「draft PRは外部リポジトリへのコミットメントであり、実装継続は承認されているがPR作成の明示的本人承認を確認できない」。操作結果は拒否で、直後の同head/all state読取り照合は0件。PR未作成であり結果不明ではない。再試行・別経路・迂回作成を行っていない。pr-blocker.jsonに操作/対象/理由/読取り結果を保存した。

新しい関連する本人承認を受け取り、未作成を再照合できた場合だけ、拒否された同じAPI/同じ対象を1回再判定できる。実装・通常push・検証・正式証拠保存は独立して進める。mainマージとapproveは担当外で実行しない。

## 検証の条件数と世代

固定SHA `bc353deb55f04ba3f8e60002d7f4e2789feddf2d` の本番/検査器を使用。新規はAPI257条件、data62条件（独立BFS4帰路・2回生成全path/全bytes・既存原資源不変）、実キー撮影43条件/6枚。082は本文9ページと13負例・runtime293条件、083は素材36条件・runtime77条件、第2沿岸91条件。旧導入1,988条件、通常画面10条件、保存位置補正31室/199条件、既存港2,677条件を確認した。戦闘復帰/保存型の原検査も終了0・警告/ERRORなし。

R-01〜08は原verifyを元の300秒上限で実行し、原run_locked_checks.judge_outputで全件PASS。R-07は通常操作14条件、R-08は25テスト/3,046 assertion・pending0・invalid=false。コマンド/実終了値/開始終了/上限/ログhashはcommands.json、元判定はlocked-checks.jsonに保存した。

static-data.logは検査の固定参照d46151a633a2b5701bf0c583bf01344f39095929が未取得で終了1。検査を変更せず完全SHAをfetchし、static-data-isolated.logで別checkoutの同一検査36条件全件成功。static-data-fetched.logは作業checkoutの同一検査の補助実行で、旧083の出力は既存記録と同bytesだった。正式な隔離検証はstatic-data-isolatedを採用し、初回失敗を消していない。

旧011の全assertion対応はassertion-migration.md、旧検査器の全bytes不変はchecker-conservation.jsonへ保存する。新規084検査はCI未接続。既存CI成功で新規検査を代用せず、ローカル新規証拠と既存全CIの終了を分けて記録する。

画像：[未完了の入口](../../verification/task-084/before-complete.png)・[完了後の内部着地](../../verification/task-084/after-complete-entry.png)・[通常退出](../../verification/task-084/interior-return.png)・[保存復帰後の帰着](../../verification/task-084/loaded-return.png)・[内部Atlas](../../verification/task-084/interior-atlas.png)・[帰着Atlas](../../verification/task-084/returned-atlas.png)。実行時点の元PNGを保存し、静的合成ではない。

## 027の注入対象を保持する補正

最初のローカル全体回帰は28コマンド中26件成功し、素材固定参照未取得と027の通知あり撮影180秒タイムアウトを保持する。素材参照は上記の通り解消。通知あり撮影はLP_NUM_THREADS=2（Mesa描画並列数のみ変更）でも180秒タイムアウトし、元の上限/検査器/判定は変更しない。

追加点検で、旧027の最終returnリテラルを探す故障注入が新しい退出通知にも一致することを発見した。mutation-target-red.logは元1か所から2か所になった条件をFAILとして保存。Region2Ruinsの退出通知を局所変数exited経由で返し、旧最終通知リテラル1か所と旧階段の注入対象を維持する。検査器は変更せず、新規dataへ元target数の継続検査1件を追加した。新規dataは再生成込み63条件となる。最初の62条件は削除していない。この補正は動作の変更ではなく既存故障注入の対象維持である。

### PR拒否の解消

拒否後、親が本人の継続許可原文（Sentinel_88686aa1bca08191b42f3c9365adb23e、2026-10-03T22:23:32.035731+00:00の項目5/6、およびSentinel_f4892d63b37881918711fe97b2e1b32e）を直接取得し、認証された本人発言として追加提供した。今回の同repository/head/base/draftに関連する新しい根拠であり、未決の物語・保護変更・検査弱化へ広げていない。

同head/all stateのPRが0件と再確認し、拒否された同じcreate_pull_request APIを同対象へ1回だけ再判定した。根拠はAPI引数へ混入していない。2026-10-28T21:26:58Zに[draft PR #67](https://github.com/hiroshitanaka-creator/RPG-maker/pull/67)を作成成功。pr-create-result.jsonとpr-blocker.json.retry_outcomeへ結果を保存し、初回拒否の記録は保持した。mainマージ・approve・別経路への切替えはしていない。

### 旧stage負例が読むメタデータの保持

初回bc353deのCIは37ジョブ成功・Godotジョブ取消終了であり、全件成功ではない。原ログci-initial-godot.logでは通知あり撮影の後、旧027のstage拒否のassertionで停止した。現物照合で、旧stage検査が読むworld_connection.cellsを接続メタデータ置換時に落としていたと確認した。固定版の旧候補3セルは床ではなく壁の候補として現在も必要である。

legacy-metadata-red.logに旧候補メタデータ欠落の失敗を保存し、defs/生成器出力/JSONに旧cells3件を同じ値で保持した。新しいworld_cell/exit_cellと混同せず、旧stage負例は失敗判定まで実行できるようにする。旧assertion/検査器/判定を変更しない。新規dataの元62条件と注入target継続1件を保持し、旧cells継続1件を加えて再生成込み64条件となる。
