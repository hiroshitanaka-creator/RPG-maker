# 055 保存専用native I/OとWindows対応を実装する
- 状態：作業中
- 担当：Codex GPT-6.1 Sol／High
- 依頼日：2026-10-09 JST
- 基点：054提出71908a13bcf704287fbc653ca307c504b4bc7f08（全39CI成功）
- 作業ブランチ：codex/task-055-native-save-io
- 承認：2026-10-09 08:28 JST、依頼者が「保存操作に限ってC++拡張と専用のWindows・Linux検査を追加する」案Aを選択。
- 053は差し戻し、PR33未統合。対象は054のF1〜F4。

## 目的
ゲーム本体はGodot4.7.2/GDScriptのまま、保存操作だけを担う内部C++ GDExtensionを追加し、Windowsの一般ユーザーでも原契約どおりのS3を使用できるようにする。単一writerと依存変更後の再検証不備も解消する。通常UI/実ユーザー保存/S4S5には接続しない。

## 担当範囲
- scripts/game/equipment_save_transaction.gd
- 新 native/equipment_save_io/（ソース・ビルド・依存固定・ライセンス）、新 addons/equipment_save_io/（.gdextensionと必要なDLL/SO、manifest）
- 新 tools/fixtures/equipment-save-transaction-platform/ と tools/check_equipment_save_transaction_platform.py 等の今回専用runner/probe
- 新 .github/workflows/equipment-transaction-platform.yml
- 新 docs/verification/equipment-save-transaction-platform/、本依頼の状態行、docs/tasks/reports/055-native-save-io.md、docs/decision-log.mdの今回追記
ルートAGENTSへ親が記録した限定例外以外の契約は不変。既存addons、既存workflow/wrapper/fixture、S1/S2公開API、通常入口、ゲームdata、原画/assets、test/.scope-lockと保護検査、過去証拠・報告は変更しない。担当外が必要なら理由と最小差分を提示しその部分だけ保留。

## 必須の修正
1. AGENTSと054報告全文、040計画、053原コード/証拠を読む。054付録のF2/F3を元版で再現し、修正版の正負例を固定する。
2. GDScriptはphase/codec/migration/ゲーム規則を保持。nativeはroot/identity、kernel lock、exclusive create、write_exact/flush/close/readback、no-clobber renameだけへ限定。初期化/欠落/不正binaryはfail-closed。新言語へのゲーム移植はしない。
3. WindowsにGNU導入・管理者・Developer Modeを要求しない。handleによるroot内、volume/file ID/link数を確認し、reparse/junction/symlink/hardlink/同一file/既存target/root外を正しく拒否する。Linuxでも対応primitiveを使う。存在確認してから普通のWRITE/renameに流すだけで排他保証を主張しない。
4. 単一writerはOSのkernel lockを生存handleで保持。unknown/照会拒否をdead扱いしない。process終了時の解放と再取得を確認し、metadata/PID/nonceは監査用にする。旧053 writerとの混在を安全に防止し、旧取引原物を削除しない復旧互換を検証。
5. 原backup/確定出力の既存fileを切り詰めない。所有済み未完tmpの再利用とreceipt置換は別契約にする。rename成功後のreceipt失敗はcommittedを維持。原source/履歴のbytes/size/hashは保持。
6. F3はcache削除か全依存のimmutable snapshot/revisionで解消。commit/recoverでfresh判定と不一致を起こさない。job_progressionを含むvalidatorの実依存、jobs/abilities/source_build/session差替えを正負に検証。呼出側が世代を変えるはずという仮定にしない。
7. godot-cpp等は公式sourceの完全commit・licenseを固定し、再現可能なWindows/Linux x86_64 debug/releaseビルドとhash/依存表/コンパイラ情報を残す。配布先に開発環境を要求しない。既存プロジェクトの保護されたexport設定は変えず必要配布物・未接続を明示する。

## 検証の保持と追加
- 053固定e003b126の172/2178・97kill・14伝播・scope2を当時checkoutで保持。旧fixture/期待を書き換えない。
- 新native境界と旧97境界の対応を明文化し、Windows/Linuxの最新で同じ論理不変条件と全正負を実行。新追加の件数/期待は独立固定する。Windows強制終了をSIGKILL/exit=-9と偽らない。
- 原180秒/子30秒/import600秒/各job15分を延ばさない。予算不足は報告し、skip/continue-on-error/期待弱化を行わない。固定完成SHAと最新継続回帰を分け、後続文書で誤拒否しないscope正負例を保持する。
- F2生存owner+照会障害、同時初回取得、異常終了後解放、PID再使用相当、F3同一T/fresh T、inspect/recover書込み0、target直前競合、file差替え、型/値/順序、数量12/22・二重付与0、メモリ/metrics不変を機械検証。
- Windowsのdrive/case/非ASCII/空白/長いpath/UNC/末尾dot-space/予約名/ADS/reparse/root接頭辞を正負に検証。対応FSを明示し全FS保証としない。
- 原証拠の欠落/空/改変/件数とlog同時偽装/manifest再hashが成功にならない。raw archive/member hashとGit blobを分ける。
- 既存S1/S2・装備・旧比較142/10全文、R01〜R08、保護26、全最終CIを確認する。

## 専用環境の承認境界
Windows/Linuxの専用CI追加は今回承認済み。実ENOSPC・別volumeには、既に提供済みの隔離小容量volumeや専用使い捨てrunnerがあるかを最初に確認する。
ユーザーPC/共有diskを埋める、mount/VHD attach/ACL/OS設定を変更する操作は今回の承認に含めない。必要なら実行環境・具体操作・影響・後片付けを親へ提示し、その準備だけ確認待ちとする。新たな環境やタスクを勝手に作らない。
注入・RLIMIT・sparse file・同volume別dirを実ENOSPC/実別volumeと呼ばない。実際のwrite/flush/metadata error、free bytes、volume IDと同volume対照を記録する。未実測のままF4解消としない。その他の実装・専用CI・既存回帰は並行して進める。

## 提出
開始前後の未commit/未pushと実アクセスを報告。初期失敗・修正後成功・未実施を分離し、原物を保持。新コード完成を完全SHA固定して証拠を保存し、最終報告後のコード不変を照合する。
指定branchへcommit/push、自身状態を報告済み。PR33への取り込みは親が行うため新PR/main反映/merge/強制push/削除/追加委譲なし。既存053/054依頼書状態は担当外。全最終SHA CIが終了してから結果を返す。未達があれば明示し、親の独立再レビューへ渡す。
