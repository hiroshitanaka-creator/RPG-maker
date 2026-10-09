# 056 保存専用nativeの独立レビュー
状態：登録済み

## 対象
055提出 c469ae1836edb1084e26d6ae3355626fec8028d4、完成コード 0a44409c99b06569b9e6088ffeb46c2238c821fa。055は未達を含む提出で受入済みではない。
担当：GPT-6 Astra／Medium。指定branch：codex/task-056-review-native-save-io。
2026-10-09 13:36 JST、依頼者が056登録と指定クラウドレビューを明示承認。

## 前提・読むもの
AGENTS.md、docs/tasks/README.md、055依頼と報告、054報告、053依頼・報告・証拠、040保存統合計画、native/addon/専用workflow・runner・fixture。追加skillが必要ならcheckoutの.agents/skillsの関連SKILL.mdを確認する。

## 許可範囲
変更可能はこの依頼書の状態行と docs/tasks/reports/056-review-native-save-io.md の新規作成のみ。隔離checkoutと専用QA一時ファイルで検証する。指定branchへ2文書をcommit・pushする。
実装・検査・workflow・保護26・test/.scope-lock・原画・通常入口・実ユーザー保存を変更しない。新PR、main push、merge、force、削除、委譲、新環境起動は禁止。秘密情報は保存しない。

## 独立確認
1. 登録基点b17f2b475ff8c58924720ea24cce8f205422c50bからの全差分、完成後49コードpath不変、既存S1/S2 API・原053証拠・旧workflow/検査不変を確認する。R01〜08・保護26前後を実確認する。
2. F1：Windows/Linux debug/release配布物、公式Godot4.7.2実ロード、toolchain/ABI/license/依存、標準ユーザー要件、無効binary fail-closed。Windows実環境がなければCI原物確認とローカル再実行を区別。
3. F2/F3：kernel lock、生存/unknown owner、旧053との安全な拒否・復旧、identity/volume/link/no-clobber、root外・予約名・大小文字・long path、fresh依存再検証を照合する。反例は専用QAで再現し重大度・影響・修正範囲を示す。
4. 原172ケース/2178条件/97kill、追加primitive・配布物・16伝播・scope正負を区別。原053固定e003b126de6695fa131e07a3db14c3011fb74f2eを保持。primitive成功を全取引成功の代用にしない。全体180秒、子30秒、import600秒、job15分、全期待値と警告検出を維持。省略・弱体化・skip・continue-on-error・時間延長は禁止。
5. 最終c469の47jobは43成功4失敗。専用nativeはprimitive4＋Linux latest transaction成功、Windows fixed/latestとLinux fixedが約174秒で停止。原053 latestもtransaction失敗、子log詳細未確認。実Actions原記録・artifactを確認し失敗原因を特定する。取得不可は正確に記録し制限を迂回しない。
6. 検証条件を変えない隔離計測で、seed6種・queue待ち・Godot起動・plan/verify・native I/O・snapshotの内訳を調べる。174秒内側締切と外側180秒を区別。import/buildは別予算。batch所要時間の二重計上禁止。Linux4復旧worker/16caseとWindows2/8、過去並列変更の回帰を考慮し、原因未計測なら推測と明記。timeout時の子log欠落も確認する。
7. 証拠のGitHub digestと実raw hashを区別し、archive全member/欠落/改変/manifest再hashの失敗伝播を検証する。固定jobの未使用fixed_sha欄の旧登録値と、実checkout/source_shaを混同していないか照合。
8. F4実ENOSPC・nested別volumeはNOT_RUN。既設専用環境の有無は読み取りのみ。mount/VHD attach/ACL/OS設定変更、共有disk充填は禁止。必要runner・小容量FS/volume・容量上限・操作・影響・撤去手順を提案だけする。注入・RLIMITを実ENOSPCと呼ばない。

## 提出
判定、重大度付き再現済み指摘、成功/失敗/未実施、実argv/秒数/exitと証拠、SHA、検査条件を保った次の最小修正案、別途承認が必要な環境準備を分離する。物語の詳細を報告しない。最終SHAの全CIを失敗も含め確認し、clean/未push有無を報告。レビュー文書追加によるscope拒否を055実装の新規失敗と混同しない。
