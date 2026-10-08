# 055の固定期待と世代対応

原053のe003b126de6695fa131e07a3db14c3011fb74f2eは元workflow/wrapper/fixtureで172/2178、kill97、伝播14、scope2を保持する。既存ファイルは変更しない。055のexpectations/recovery-phasesは原固定と同一bytesの独立コピー。Windowsの唯一の元ケース対応差はnonroot-permissionを専用fileのreadonly属性による実write_failedへ写像すること（Linuxは0500/backup_failedを保持）。ACL・OS設定変更なし。SIGKILL=-9とTerminateProcess=1を別に固定し、ログ上も同一視しない。

旧read.open/buffer前後はnative open_read/read_all/close、各owner/intent/source/history/candidate/receipt open/store/partial/flush/close/readbackは同じGDScript地点のnative open_write/write_exact/flush/close/readback、各rename前後はnative rename_fileへ対応する。directory.createはcomponent検証付きmkdir、lease.acquireはkernel lock取得後の旧混在防止regular leaseのexclusive renameへ対応する。97地点の名前/期待phase/原bytes/数量/再起動/副作用条件は保持する。

追加6境界をextra-expectationsへ独立固定する：kernel.lock.before/after、intent/source/history.native.rename.beforeはincomplete、commit.native.rename.beforeはprepared。その実強制終了→別process resume→committed/quantity12/原sourceとhistory/backup保持/candidate hashを検査する。固定期待を実装結果から生成しない。

F2正負：単独writer、照会障害中の生存ownerにbusy、同時初回取得1、異常終了後再取得、PID再使用相当metadataはkernel lockの代わりにしない。旧live owner拒否、旧dead取引復旧、旧writerによる新取引書込み拒否をLinuxの旧実コードで検査する。F3はcacheを全削除し、control/同一T/fresh T、job_progression/jobs/abilities/source_build/session差替えを実contextと固定期待で確認する。新規元validator/期待を改変しない。

native追加にはexisting target、hardlink、確定fileの切詰め、未所有write、tmp再利用、receipt別契約、same bytes別file identity、target最終競合、inspect/recoverのname/size/mtime_ns/hash不変を含む。Windows drive/case/非ASCII/空白/長いpath/UNC/dot-space/予約名/ADS/root接頭辞は正負を分ける。reparse/symlink/hardlinkは元ケースの最新でも実検査する。FS対象はローカルNTFSおよび実測Linux FS、全FSと呼ばない。

全体180秒・各子30秒・import600秒・各CI15分を維持する。旧Windows未実装を旧固定成功へ混ぜない。新runnerの原証拠16伝播はmissing/empty/warning/exit/timeout/件数/false assertion/phase/bytes/hash/再hash/件数＋log偽装を実子exitで拒否する。raw archive全hash/member hashはGit blob IDと別に保存する。scopeは完成SHAへ固定し、後続文書追加正例と担当外固定負例を実Git tree/実exitで保持する。

実ENOSPC/専用nested別volumeは既設の隔離領域がない場合NOT_RUNとして残し、fixture注入/同volume別dir/共有disk充填で代替成功にしない。通常UI・実ユーザー保存・S4/S5は範囲外。
