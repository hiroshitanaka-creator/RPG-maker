# 070 城の案内を実際の進行先に合わせる

- 状態：未着手
- 担当：Codex（GPT-6 Astra／High）、正式GitHub保存と統合はルッカ
- 依頼日：2026-10-15
- 前提：069確認済み。NPC-GUIDANCE-RUNTIMEの原資料を親が受領・照合済み
- ブランチ：codex/task-070-castle-guidance-text
- 担当の場所：world/first_region.json、world/interiors.json、tools/build_castle_town.py、docs/tasks/070-castle-guidance-text.md（状態行のみ）、docs/tasks/reports/070-castle-guidance-text.md
- 変えてはいけない場所：上記以外の本番ファイル、.scope-lock/、test/、保護検査、既存の検査・期待値・締切、workflow、project.godot、素材・台帳、066系列、069本文。docs/tasks/README.mdとdocs/decision-log.mdは親だけが記録

## 1. 参照すべき契約と事前確認
AGENTS.md、.scope-lock、docs/tasks/README.md、docs/dependencies.md、docs/experience-spec-v2.mdを読む。R-01〜R-08と既存の3人/4人・正順/逆順の全編受入を壊さない。基点main8f2bc17b8c36b4304eb17de1a29e91e67a21cf57からの差分を確認する。状態・生成元と実ロード先を確認してから編集する。

### 目的・背景
現行案内は『城の北の門は、王の許しを得た人にだけ開かれます。』。通常入力の実検証で、北門を含む3通路は許可前から通過でき、実際に許可が必要なのは森の塔入口と確認した。物理門は実在する。門不存在・製品全体の不具合とは扱わず、既存の許可を正しい進行先へ結びつける品質修正を行う。AGENTSの自走許可2・6の範囲内で、物語・地名・人物・ルール・配置は追加変更しない。
原資料：NPC-GUIDANCE-RUNTIME-2026-10-15.zip、5,124,073 bytes、SHA256 e9127a1ede4a64a8ae4da816ab0519b623967cb76bf650db4c0ce09bff689acf。対象58観測、既存14項目。初回ハーネス失敗も保持済み。

## 2. 今回使用するスキル
メイン：$rpg-maker-storyteller。検証：$godot-game-verification。基底構文は既存実装を維持。未導入のスキルは勝手に追加せず未導入と記録し、同じ検証原則を守る。AGENTS.mdと.scope-lockを優先する。GD-Agentic-Skills等の同梱.gdを本体へコピーしない。

## 3. 実装対象と具体要件
1. castle_home_residentの1ページ本文を『森の塔へ進むには、王の許しが必要です。』へ変更する。新しい固有名・許可条件は追加しない。
2. world/first_region.json、実ロードされるworld/interiors.json、生成元tools/build_castle_town.pyの対応文字列の3箇所だけを同じ本文へ揃える。JSON全体の再整形はしない。
3. 他の全JSON値、ID、座標、話者、画像、扉、進行フラグ、台詞ページ数、ゲーム数値は不変。生成元の古い座標[10,7]と現配置[11,6]の既存差を直さない。全マップを再生成しない。
4. 依頼書本文は保持し状態行のみ更新。報告には実変更と原ログ/画像の場所を記す。親は正式保存時にdecision-logへ日付・決定・理由・通常コミットで元の本文へ戻せることを記録する。
5. 066とは独立したmain系列で作業する。ローカルの変更・commitは許可するが、GitHub保存は親が公式ai接続で行う。remote push・認証変更・PR/mergeを子から行わない。原資料はcheckout外の専用保存先へ保全する。

## 4. 検証と受入条件
- 3箇所の新本文完全一致、JSONの対象text以外の値完全一致、Pythonの変更が対応文字列だけであることを検証する。
- 固定Godot4.7.2を公式URLと既定SHA256で確認し、素材import後に検証する。
- 実ゲームで通常入力の初回会話・終了・再会話、話者と1ページ、文字切れなしを画像で確認する。王の許可前後の城3通路と森の塔入口の挙動は前回と同じであることを確かめる。通常保存の流用は可、状態注入と通常経路を混同しない。
- 既存GUTのR-01〜R-08、素材strict、check_frozen_files.pyを変更せず実行する。必要な既存回帰検証も現行の上限で行い、保護26件不変を確認する。検査追加のために保護test/や既存検査を編集しない。
- 終了コードだけでなくSCRIPT ERROR、パースエラー、リーク警告を原ログで確認する。環境警告を削除せず区別する。未実行の全編受入は成功と書かない。
- 親による正式GitHub保存・全CIの終了と全成功・差分/保護の確認を経てPR取込判断する。ローカル結果を正式CI成功の代わりにしない。新しい固定SHA/証拠世代の手続きは追加しない。

### 作業前の計画・作業後の自己点検
最初に編集5ファイルと確認順序を列挙。報告前に対象外不変、原67/066不変、既存の期待値/予算不変、実画面と原ログ、未実行項目を点検する。

### 報告
変更5ファイルの原bytes、差分、サイズ/SHA256、全コマンド・成否・警告原文、画面、通常入力の手順、未達項目をdocs/tasks/reports/070-castle-guidance-text.mdへ記す。原資料ZIPを正規Libraryへ返し、確定ID/サイズ/SHA256を報告する。原資料を小さい要約で置き換えない。
