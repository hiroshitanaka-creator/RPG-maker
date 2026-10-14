# 067 装備関連スクリプトのUID3件を066系列へ登録

- 状態：報告済み
- 担当：RPG-makerクラウドCodex（実生成・原bytes照合・引渡し）、ルッカ（公式GitHub hiroshitanaka-aiでG保存・読戻し照合）
- 依頼日：2026-10-12 JST（13:47 JSTに依頼者が再開を明示）
- 前提：なし。066全体の受入成功を前提にせず、指定されたD′の隔離checkoutでUIDを生成する。
- ブランチ：codex/task-066-native-build-contract-v1（親がE′の後へ独立コミットGとして保存する。main向けPRは作らない）
- 生成基点：D′ `9a99e6501a7b252f77cd6acf515a9f7564abe5f1`
- 担当の場所：`scripts/game/equipment_rules.gd.uid`、`tools/check_equipment_rules.gd.uid`、`tools/check_equipment_save_codec_cost.gd.uid`、`docs/tasks/067-register-equipment-script-uids.md`
- 変えてはいけない場所：上記以外の全ファイル。元GDScript、native、addonsの既存ファイル、検査、期待値、保護、CI、予算・締切、`docs/tasks/README.md`、`docs/decision-log.md`を変更しない。

## 目的

固定Godotが1回の読み込みで実生成した3UIDを同じ066系列に登録し、以後の検証で未追跡追加になることと、系列ごとに別のUIDを生成することによる将来の値衝突を避ける。

## 背景

旧main `9070038523ded3277fa45bf7615cf023aa08e786` には066の基点系列 `e83bbce4018946da3e5f61f7b9f972474197f9e1` が含まれず、`tools/check_equipment_save_codec_cost.gd` も存在しなかった。旧main向け作業で生成した2UIDは採用せず、原記録を保持する。

依頼者はmain向け067のPR作業を取り消し、D′で3UIDをまとめて実生成し、066系列のE′の後の独立コミットGへ入れることを指定した。2026-10-12の一時停止は中止ではなく、13:47 JSTに再開を明示した。依頼者によれば現mainには068がマージ済みだが、本Gへmainを取り込まない。

参照はこの生成基点の`AGENTS.md`、`docs/tasks/README.md`、`docs/tasks/_template.md`と、依頼者の今回の再開指示とする。通常のcommit・push・報告配置規則に対し、今回はクラウドCodexによるGitHub書込みを禁止し、Library ZIPで親へ渡す。RPG側の変更は上記4件に限定する。

## 作業内容

1. 隔離checkoutのHEADがD′に一致し、既存UIDの有無と生成済み記録を確認する。既に生成済みなら削除・再生成せず原bytesを保持する。
2. 実行Godotのpath・version stdout・実体bytes/SHA-256を採取し、`4.7.2.stable.official.ed1daf0bf`と一致することを確認する。
3. 未生成を確認したcheckoutに対し、`godot --headless --editor --import --quit`を1回だけ実行する。main向け旧2UIDの流用・手作りUIDは禁止する。
4. 生成前後の全ファイルmode/bytes/SHA-256、全差分、原stdout/stderr/exit、元3スクリプトと生成3UIDの原bytes・mode・bytes・SHA-256を保存する。
5. 元コード・検査・期待値・CI・保護が不変であること、提出対象が4件のみであることを照合する。無関係生成物は隔離保持し提出対象へ混ぜない。
6. 本依頼書を報告済みにして、4ファイルの原bytes・完全差分と原証跡をLibrary ZIPへ保存し、ID/version/bytes/SHA-256、実行済みと未実行を親へ返す。
7. 親がE′の後へGとして公式GitHub aiで保存し、原bytesを読み戻して照合する。クラウドCodexはcommit・push・PR・mergeを行わない。

## 守ること

- mainを統合しない。main向けPRを作らない。旧main向け2UID・過去の証拠を削除も書換えもしない。
- UIDを消して再生成しない。今回は1回の生成だけとし、再importや別checkoutでの追加生成を行わない。
- 元コード・検査・期待値・CI・予算・締切を変更しない。未実行を成功と扱わない。
- 独立並行中のinspect前後差分調査は本番ファイル変更なし。共有ファイルの変更が必要になった場合は、変更せず停止して報告する。
- 親のG保存後のSHA・E′のSHAを推測しない。生成基点D′と正式提出Gを区別する。

## 作業の前にしてほしいこと（計画）

既存D′ checkoutと3UID不在を確認し、clean状態の全ファイル一覧を採取する。固定Godotの実体を確認して1回だけimportする。証拠と4ファイルの提出候補はcheckout外へ分け、旧main成果を流用しない。

## 作業の後にしてほしいこと（自己点検）

3UIDが実生成物の原bytesと一致し、対応元3スクリプト・その他の既存追跡ファイル・保護が不変であることを照合する。提出集合が指定4件であること、mainの統合・GitHub書込み・追加のUID生成を行っていないことを記録する。失敗・未実行・正式保存待ちを分ける。

## 報告

今回の4ファイル限定指示に従い、RPG-makerの`docs/tasks/reports/`への追加は行わない。原ログ・生成前後の一覧・全差分・各ファイルの原bytesと照合情報・実行済みと未実行をLibrary ZIPで親へ渡す。親は`lucca-workspace/projects/rpg-maker/reports/067-register-equipment-script-uids/`への文字報告と、原資料保全、公式GitHub保存後の照合を担当する。

## 完了の条件

ローカル引渡しは、指定D′・指定Godot・1回の実生成・3UID原bytes・対象外不変・4ファイル限定を実証したLibrary ZIPの保存が成功したときに成立する。正式登録の完了は、親がE′の後のGへ保存し、GitHub上の原bytesと4ファイル差分を照合した後とする。全CI・R-01〜R-08・066全体の受入は別途必要な検証であり、この生成作業だけで成功としない。
