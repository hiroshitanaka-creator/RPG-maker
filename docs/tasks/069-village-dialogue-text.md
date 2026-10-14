# 069 村の通常NPC5件の会話仕上げ

- 状態：未着手
- 担当：Codex GPT-6 Astra／High（実装・検証）。正式GitHub保存・PR・取込判断はルッカ。
- 依頼日：2026-10-14 JST
- 前提：007・021・022・023の確認済み状態を照合する。
- ブランチ：codex/task-069-village-dialogue-text
- 基点：d7626859d7243795ee9cc072e8eb7e37d6287781（最新mainを依頼登録直前に照合）
- 担当の場所：world/region2_village.json、docs/tasks/069-village-dialogue-text.md（状態のみ）、docs/tasks/reports/069-village-dialogue-text.md
- 変えてはいけない場所：上記以外。検査・CI・保護・画像・ゲームコード・066系列は変更しない。

## 目的・承認
既存5人の短文を以下の2ページの会話へ整える。新しい人物・商品・機能・進行条件を作らない。依頼者は2026-10-14 17:19 JST、5人分の採用と組込み・検証を推奨したA/B質問に『総監督はルッカだから、任せるよ‼️』（Sentinel_2d0fefa6fa54819195b4e7af9fc1419e）と回答。ルッカが提示済みAの範囲を選択した。正式な題名・人物設定・主要会話の新規採用を含まない。

## 背景
AGENTS.md、docs/tasks/README.md、007・021・022・023の依頼と報告、storytellerスキルの現物を読む。旧本文完全一致は007の--stageのみ、既存ラッパーは固定完成版にだけ--stageを使い、最新側は通常回帰する。検査を変更する必要はない見込みだが、実行結果を優先し、必要になれば止めて報告する。

## 作業内容
world/region2_village.jsonの対応idのtextだけを、次の値にする。id・kind・sprite・label・cell・reachその他全値とイベント順序を維持する。JSON全体の再整形は避ける。

```json
{
  "oasis_water_keeper": [
    "泉のそばでは、足元に気をつけて。",
    "ひと息ついてから、歩きましょう。"
  ],
  "oasis_child": [
    "風が吹くと、風車がよく回るんだ。",
    "ほら、あそこ！"
  ],
  "oasis_date_farmer": [
    "いらっしゃいませ。",
    "品物はまだ準備中なんです。"
  ],
  "oasis_camel_keeper": [
    "ここは武器屋です。",
    "すみません。品物はまだ準備中です。"
  ],
  "oasis_elder": [
    "旅の身支度は、整いましたか。",
    "慌てず、確かめていってください。"
  ]
}
```

宿oasis_innkeeperは原文・処理とも不変。商品準備中の状態を維持。村10人計画、ネルの配置・解放場面、料金・祠・魔物職・通行・素材は対象外。

## 作業前の計画
1. 前提状態と基点、既存未コミット/未push、変更予定3ファイルを確認する。066と共有ファイルを変えない。
2. 機能は会話データ差替えだけ。インターフェースは既存text配列・通常会話のまま。親が本文採用・保存・CI確認、Codexが編集・検証・原bytes引渡しを担当。
3. 通常画面の全ページと子どもの指示先をどう確認するかを計画する。

## 検証
- 指定Godot4.7.2を公式の固定URL/SHA256に照合して使う。既存時間上限を維持。
- godot --headless --editor --import --quit
- python tools/validate_assets.py --strict
- python tools/check_frozen_files.py
- python tools/run_locked_checks.py
- python tools/check_task007.py --completed 776ad944723d21c1e250a1ee5fd56d35da42cfed --godot <承認済み実体パス>
既存ラッパーは固定/最新と021反証回帰を含む。先にローカル作業コミットを作って検査対象HEADを一致させる必要があれば行い、正式GitHub SHAと区別する。remote pushはしない。
- 5人それぞれの2ページ・話者・順番・終了・再会話を通常ゲーム画面で確認。既存撮影は初ページだけなので、それで2ページを検証済みにしない。追加の一時撮影は追跡外に置き、既存検査器を変えない。
- 子どもの『あそこ』が指す風車が自然に分かるか実画面で確認する。合わない場合は位置・カメラ・画像・本文を勝手に直さず親へ戻す。
- 差分が指定5件textのみ、宿と非text値が不変であることを機械比較する。

## 守ること
既存検査・期待値・締切・固定SHA・保護ファイルは変えない。skipや上限延長で成功化しない。新しい検査世代や汎用検査器は追加しない。force push・履歴改変・削除は禁止。GitHub書込みは親が公式GitHub aiで行う。MSI・本人資格情報・小文字github経路は使わない。Codex側でremote push・PR・merge・認証操作をしない。

## 報告と引渡し
reports/069-village-dialogue-text.mdへ日本語で記録。依頼書の状態を報告済みにする。変更3ファイルの全文・bytes・SHA256、ローカルコミット、検査結果と原ログ、通常画面の証拠を引き渡す。親が受け取れる正規LibraryのIDを優先し、失敗したら原文を報告する。原資料の再生成・短縮で転送を誤魔化さない。原資料は親が指定Driveの該当タスクフォルダへ保全し、lucca-workspaceには文字だけ記録する。

## 完了条件・自己点検
指定5件だけの本文更新、全ページ確認、007固定/最新/021回帰・R全8件・素材・保護不変が成功し、親が正式GitHub保存と対象SHAの全CIを確認する。未検証は明記し、Codexのローカル成功をPR完成としない。docs/tasks/README.mdとdocs/decision-log.mdは親が逐次更新する。mainへの反映はPR経由のみ。新しい依頼番号を増やさない。
