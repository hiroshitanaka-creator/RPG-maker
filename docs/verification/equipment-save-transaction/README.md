# 053 保存取引の実測証拠

コード完成固定：`e003b126de6695fa131e07a3db14c3011fb74f2e`。依頼登録：`e2c28474b55bd3a9e3dee00be768661ba87e09c4`。main前提：`87f4e66ed64f2ae9a92538acb9716c6a01f5cb27`。

固定SHAの独立checkoutでwrapper全体を実行。172ケース・2178条件、実SIGKILL 97地点、障害注入24件、個別条件51件。全体180秒・各子30秒・import600秒を維持。全ケースID・期待理由・実理由・条件数・実exit・phaseは [cases.md](cases.md)、完全なcase.json/commands/log/bytes/hash/marker/PIDは原archive内。receiptの自己申告とは別に97地点の期待phaseと実bytesを検査した。

[final-fixed-execution.json](final-fixed-execution.json) は全argv・実exit・経過時間・log hash・engine/source hash・14伝播検査・2範囲検査。[final-fixed-summary.json](final-fixed-summary.json) は固定件数と全ID。[archives.json](archives.json) と各members.jsonはarchiveのSHA256と全原file/symlinkのbytes hash。archive作成後に全memberを再読出しして照合した。symlinkは参照先文字列のbytesとして記録し、リンク先へ展開しない。コピーにGitの改行処理を受ける前の原証拠をtar.gzへ保持する。

`fixed053-raw.tar.gz` は固定wrapperの全結果、QA原入力/履歴/取引実物、実exit伝播の改変コピー、scope負例、原ログ。隔離profileのXDG_CACHE_HOMEとGodot再生成cacheは省略する。保存・取引の実bytesやログは省略しない。`development-raw.tar.gz` は成功前の試作・中断・予算超過・失敗validatorも保存し、完成受入とは区別する。初期試行にはGodotの非子PID問い合わせ・空bytes hash・再帰mkdir由来のエラーログ、逐次実行の予算超過、バッチ内依存生成の試行がある。完成版は実GameSession読取り専用依存、各要求の新規context/transaction/cacheと前後state/metrics不変検査を使う。

エンジン：公式Linux `4.7.2.stable.official.ed1daf0bf`、ZIP SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、実体SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。環境の既設4.6.3は受入に使わない。

実権限拒否はuid1000で新設専用directoryを作成時0500とし実測。ユーザー権限・OS設定・ディスク設定は変更していない。ENOSPCは注入を実測し、実容量不足は専用小容量環境がないため未検証。専用nested別volume、Windows/macOS、停電・媒体故障・directory fsync、悪意ある非協調processが検査/open間にdirectoryを置換するTOCTOUも未検証。Linux以外は拒否する。プロセス終了後の復旧を停電保証と呼ばない。

S3は通常画面・通常GameSession入口・運用記録・実ユーザー保存へ未接続。メモリ適用は常にfalse。履歴は専用rawを保持し、新IDやイベントを生成しない。今後のS4/S5と人間による操作体験の採否は今回のPASSに含めない。

最終固定は通知競合修正後の上記SHA。`final-fixed053-raw.tar.gz` が最終固定の172/2178・97地点・伝播14・scope2の全原証拠。`fixed053-raw.tar.gz` とfixed-*は初回固定75b6e350の成功を保持し、最終受入とは区別する。`marker-race-raw.tar.gz` はd144ea49の追加latest失敗（171/2163、156.939秒、exit1）、空paused.json、全QA入力/結果と旧CIログ。旧CIのfixed/latestが成功してもこのlocal失敗を無視せず、probeだけでtmp→flush/close→renameによる通知公開を修正した。保存本体・既存検査の差分は0。期待件数と予算は不変。
