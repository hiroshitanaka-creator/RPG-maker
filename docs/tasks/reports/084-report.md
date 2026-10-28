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
