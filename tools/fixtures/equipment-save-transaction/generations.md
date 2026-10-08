# 053 世代ごとの全条件

- 固定053は完成コードの完全SHAへcheckoutし、その時点の本番・probe・Python検査・172ケース/2178条件・97 kill地点を全実行する。scopeは登録e2c2847→その完成SHAの全treeを監査する。
- latestは当該head SHAの本番に同じ全継続動作を実行する。scope比較先だけは完成053へ固定し、後続のレビュー文書を担当外として誤拒否しない。
- 旧装備5394＋93/400、S1 61/2828、S2原049 112/723/13と修正051 154/975/18＋scope2は既存workflow・fixture・固定SHAを一切変更せず保持する。
- 今回の全動作（原本保持、型/値/順序の読戻し、世代/hash/候補/衝突拒否、append-only排他、別process復旧、二重付与0、履歴raw保持）は最新でも継続する。当時scope・通常非接続は完成053で全保持。将来のS4/S5の動作を今回のPASSに混ぜない。

kill用Godotは各地点まで進め、Pythonがmarkerの地点/PIDを確認してSIGKILLし、waitする。その完了済み要求だけを最大4件まとめて新Godotへ送る。新processは各要求に実GameSessionを起動後に完全構築して読取り専用依存として再利用し、各要求のcontext/transactionを新規作成する。各要求の前後にstate/metrics不変を照合を作り、recover→同取引prepare/commitを行う。異なる取引で純粋計画cacheを共有しない。各要求の元PID、新PID、全argv、共有batchの全root、実exit/logを記録し、元processとは別であることを検査する。子30秒、全体180秒（174秒で新規実行を止め終了証拠の時間を確保）を延長しない。

純粋計画・decoded bytesのcacheは同一transaction instance内だけ。contextの実abilities/jobs/source_buildとrawが変われば無効化。書込み後の最初の読戻しは実bytesをS2でdecodeし全値/型/順序/IDを照合する。後の再照合も実ファイルbytesを読み、同じ検証済みbytesと完全比較する。再起動のinstanceはcacheなしで元rawからS1/S2を再計算する。directory/deviceのcacheはprocess中にmount設定が変わらない隔離QAを前提とし、リンク成分は毎回再検査する。

self-testは正常証拠の別コピーを使い、control=0、13件の失敗/警告/件数/exit/timeout/原bytes/欠落/false assertの負例=1を別Python processで実測する。scopeは実Git tree/commitの後続無名文書正例=0、固定側担当外負例=1。成功/失敗の結果を混ぜない。

通常API正負例も隔離したバッチprocessで実施する。各バッチは新たな実GameSessionを完全構築し、読取り専用依存を再利用する。各要求のcontext/transaction/cacheを分け、各要求の前後でstate/metrics不変を観測する。kill用は地点/PIDが固定された独立process。2つのバッチ実行器と最大8件の検査workerで全条件を同じ180秒予算内で実行する。追加の作業委譲ではない。
