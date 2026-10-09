# 060 専用計測の原証拠と開始計画

基点 `6695d7b802137e9d6b7e468a1414c04d658a5380`、登録 `e37ddbaf4e84526c8e3f2816438dc9626875c00e`。既存AGENTS.mdと060依頼書を全文確認。末尾正式化補足と冒頭の承認を適用する。計測成功はF1解消・S3受入を意味しない。

- CLI: `python tools/check_equipment_save_codec_cost.py --godot /tmp/qa060/engine/Godot_v4.7.2-stable_linux.x86_64 --base-sha 6695d7b802137e9d6b7e468a1414c04d658a5380 --output docs/verification/task060-save-codec-cost`
- 挿入器: `python tools/fixtures/equipment-save-codec-cost/instrument_copy.py --checkout <専用一時checkout>`。元4ファイルを固定hashで照合し、本体逆変換一致を必須にする。元条件式・return・検査本体は不変。
- 比較器: `python tools/fixtures/equipment-save-codec-cost/compare_results.py --output <専用QA先> --self-test`。欠落・改変・担当外変更を拒否する。scope負例の内部CLIは`--scope-sha <完全SHA>`。
- 条件は既存codec全ケースと全取引172ケース、各off/on 3回。各反復はoff/on、on/off、off/onの順。固定基点の一時checkoutを使い、最新本番の固定基点とのbytes一致を別に確認する。
- 予算はcodec120秒、取引外180/内174/子30秒、import600秒。既存workerはLinux16ケース/4再開、Windows8ケース/2再開、batch最大4を維持。試行を同hostで並列実行しない。
- 既存codec検査・fixture・期待、取引driver・probe・172件/2178条件/97kill・16伝播を変更しない。6正常seedのみを全体の代表にしない。F4環境準備・inspect-prepared条件変更はしない。
- 生成観測は4ファイルの非再帰入口とparse/展開/複製の対象式。関数wrapperは元本体を1度呼び、結果をそのまま返す。再帰same_types/_collectは個別計測せず、describe等の内側に含む。未観測部分をゼロとしない。
- 時刻はprocess内単調microsecond。exclusiveは直接子spanを差し引く。PIDをまたぐ合計は並行累積でありwall比率ではない。根spanのJSON出力はspan外、process wallには含む。on/offの全wall試行値で採取負荷を報告する。
- 各runは指定の10ファイルのみ。results.json内のgzip/base64 archiveに原コマンド出力・旧検査のJSON/入力・型付きgdv・取引file証拠を無加工で格納し、member hashを列挙する。stdout/stderrは別保存。時間切れも部分原物・実exit・監督状態を残し、未取得を成功にしない。
- 既存公式4.7.2取得URLとZIP hashをlaunch.pyから参照し、一時領域へ取得。既存4.6.3は使用しない。OS/プロジェクト設定を変えず、既存run_ci同様の専用process profileを使う。
- 新CI接続なし。既存全CI、旧固定版と最新回帰、今回ローカル計測を分けて最終報告する。decision-log/tasks READMEは更新しない。

結果は [060日本語報告](../../tasks/reports/060-measure-save-codec-cost.md) を参照。12試行を全保存。専用比較器は証拠整合性成功、取引未達を保持してINCOMPLETE/exit 1。inventory.latest_regressionに最新回帰の原archive、baseline_ciに059元提出の全終了記録を収録。候補は未実装。
