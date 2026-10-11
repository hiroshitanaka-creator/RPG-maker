# 067 装備関連スクリプトのUID3件を正式登録

- 状態：未着手
- 担当：RPG-makerクラウドCodex GPT-6 Astra / High（実生成・検証）、ルッカ（公式GitHub hiroshitanaka-aiで保存・PR・条件照合）
- 依頼日：2026-10-12 JST
- 前提：なし。066の受入成功を前提にしない。
- ブランチ：codex/task-067-register-equipment-script-uids
- 担当の場所：scripts/game/equipment_rules.gd.uid、tools/check_equipment_rules.gd.uid、tools/check_equipment_save_codec_cost.gd.uid、docs/tasks/067-register-equipment-script-uids.md
- 変えてはいけない場所：上記以外の全ファイル。特に元GDScript・保護ファイル・検査・期待値・workflow・docs/tasks/README.md・docs/decision-log.md。

## 目的
Godotの読み込み時に生じる未追跡UID3件を、固定版Godotが実際に生成した原バイトで登録し、後続検証で未追跡追加になることを防ぐ。検査条件は緩めない。

## 背景
2026-10-12依頼者の明示依頼。066 FのLinux latestで生成されたUID3件が厳密照合に拒否された。最新mainから独立した小さなPRとして扱う。066 v2の4コードファイルとは重複しない。

## 作業内容
1. 最新mainの完全SHA、作業前の未コミット・未push差分、AGENTS.mdと依頼書の規則を確認する。
2. Godotの実行バイナリが4.7.2.stable.official.ed1daf0bfであることを実コマンドで確認する。別版を使わず、使用バイナリのパス・SHA-256・version stdoutを記録する。
3. 隔離したclean checkoutで godot --headless --editor --import --quit を実行し、生成前後の全変更を記録する。指定UID3件の値を手作りせず、実際の生成原バイトを採る。
4. 3件のパス・サイズ・SHA-256・内容と対応元スクリプトを照合。提出する変更はUID3件とこの依頼書だけとする。他の生成物や証拠をRPG-makerへ追加しない。
5. 固定版で再読込みし、登録したUIDが変わらないことを確認する。既存の検査・R-01〜R-08・check_frozen_files.pyを規則どおり実行し、未実行・失敗を明示する。
6. 公式GitHub aiで保存・読み戻し照合しPRを作る。全CI終了後、自走条件すべてを実物で満たす場合だけ通常マージする。不明・不合格があればマージせず報告。

## 守ること
手動UID生成、元コード変更、検査弱体化・省略・予算延長、削除・履歴改変・force push禁止。MSIからの保存・小文字github・creator資格情報を使わない。原資料は指定Drive、報告はlucca-workspaceの文字ファイルへ保存する。

## 作業の前にしてほしいこと（計画）
実行Godot、生成用checkout、4ファイル限定の確認方法、再インポートと受入検査の手順を列挙する。066 v2と変更対象が重ならないことを確認する。

## 作業の後にしてほしいこと（自己点検）
実生成・バージョン一致・3UID原bytes一致・4件以外不変・R全件/凍結/全CIの実結果を各々照合し、未確認を成功にしない。

## 報告
今回の依頼者指定（他のRPG-makerファイルは変更しない、作業別報告をlucca-workspaceに保存）に従い、報告はhiroshitanaka-creator/lucca-workspaceのprojects/rpg-maker/reports/067-register-equipment-script-uids/へ置く。通常のdocs/tasks/reportsへの追加は今回行わない。原ログは指定Driveに保存し、ファイル名・bytes・SHA-256・Drive IDを記録する。PR URL、commit、生成UID、コマンド原結果、全CI成否、取込可否と根拠、未確認を含める。

## 完了の条件
指定版の実生成UID3件をGitHub上で原bytes照合、差分が指定4件内、全CI・R-01〜R-08成功・保護不変・検査弱体化なし・依頼範囲内を確認してPRを通常取込し、取込後も照合する。満たせない場合は未完了と根拠を報告して止まる。
