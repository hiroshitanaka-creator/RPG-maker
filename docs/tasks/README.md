# 伝言板（作業の依頼書と報告書）

このフォルダは、依頼者・指揮役（Claude）・作業を行うAI（Codex・Grok など）の間で、作業の依頼と報告をやり取りする場所です。指示も報告も、このフォルダのファイルで行います。

## 役割

| 役 | 担当 | すること |
| --- | --- | --- |
| 決める人 | 依頼者 | 物語・名前・見た目の採否など、作品の中身を決める。依頼書をリポジトリに入れ、担当のAIに「この依頼書を読んで作業して」と伝える |
| 指揮役 | Claude | 依頼書を書く。報告書とリポジトリの実物を読んで、結果を確かめる |
| 作業する人 | Codex（ChatGPT dot 経由）、Grok など | 依頼書を読んで作業し、報告書を書く |

## 依頼書の決まり

- 1つの作業を、1つのファイルにします。ファイル名は `NNN-短い英語の名前.md`（例：`001-status-and-decisions.md`）。番号は通し番号です。
- 依頼書の書き方は `_template.md` に従います。
- 依頼書の先頭の「状態」の欄で、今の状態を示します。

| 状態 | 意味 | 書き換える人 |
| --- | --- | --- |
| 未着手 | まだ誰も始めていない | 指揮役が作るときに書く |
| 作業中 | 担当のAIが作業している | 担当のAIが始めるときに書き換える |
| 報告済み | 担当のAIが作業を終え、報告書を書いた | 担当のAI |
| 確認済み | 指揮役が結果を確かめ、問題がなかった | 指揮役（依頼者が書き換えてもよい） |
| 差し戻し | 指揮役が結果を確かめ、直す点があった。直す点は、新しい番号の依頼書に書く | 指揮役 |
| 中止 | 依頼者が取りやめた | 依頼者 |

## 担当のAIが守ること

1. 作業を始める前に、依頼書の「前提」に書かれた依頼書が「確認済み」になっているか確かめてください。なっていなければ、始めずに報告してください。
2. 作業を始めるときに、依頼書の「状態」を「作業中」に書き換えてください。
3. 依頼書に書かれた「担当」の場所だけを変えてください。ほかの依頼書の担当の場所は変えないでください。
4. 作業は、依頼書に書かれたブランチで行ってください。
5. 作業が終わったら、`reports/NNN-短い英語の名前.md` に報告書を書き、依頼書の「状態」を「報告済み」に書き換えてください。報告書の書き方は、依頼書の「報告」の節に従ってください。
6. 依頼書と、`AGENTS.md`・`docs/experience-spec-v2.md` が食い違う場合は、`AGENTS.md` を優先し、食い違いを報告書に書いてください。

## 同時に作業しない決まり

同じファイルを、2つのAIが同時に変えないようにします。依頼書の「担当の場所」に、変えてよいファイルやフォルダを書きます。「担当の場所」が重なる依頼書は、同時に「作業中」にしないでください。


## 原画保管の作業記録（2026-10-10）

| 番号 | 依頼書 | 報告書 | 状態・確認範囲 |
| --- | --- | --- | --- |
| 062 | [城と飛行船の原画保管](062-record-region3-castle-art.md) | [062報告](reports/062-record-region3-castle-art.md) | 確認済み。PR #34を2026-10-10にmain 5116756c7b4814fd8cf5f0886983f1949a1ae6d9へ通常取込。最終head f34efde0の全74CI成功、R-01〜R-08・凍結26件一致を直接確認。取込後の5枚のGit blob・サイズ・件数・記録と旧版branch残存を再確認。取込後mainの全37ジョブも成功。ゲームへの組込みは対象外。 |

| 063 | [主の居場所の原画保管](063-record-lord-place-art.md) | [063報告](reports/063-record-lord-place-art.md) | 確認済み。PR #35を2026-10-10にmain a6cb2ebd3d86100b20978bca3503e8ddd4a5d911へ通常取込。最終head48f66b53の全74CI成功、R-01〜R-08・保護26件不変を直接確認。取込後の4枚の同一blob・サイズ・件数・記録、旧版branch残存を照合。取込後mainの全37ジョブも成功。ゲームへの組込みは対象外。 |

| 064 | [第4地方の原画保管](064-record-region4-art.md) | [064報告](reports/064-record-region4-art.md) | 確認済み。PR #36を2026-10-10にmain 983968277de50a11874d412efd02ac885e10a4bbへ通常取込。最終headac7f5241の全74CI成功、R-01〜R-08・保護26件不変を直接確認。11枚の指定hash/bytes一致、取込後の同一blob・11枚限定、旧室内4枚とincoming15段の非混入、全15枝残存を照合。原画追加はbe0cb834の1commit。ゲームへの組込みは対象外。 |

062→063→064の順で逐次取り込み、共通のroadmapの並列編集は行っていない。各PRの最終headと基点mainを照合した。各取込後main CIの最新状態は対応PRの記録で確認する。


## 2026-10-14 会話本文の仕上げ

| 番号 | 依頼書 | 報告書 | 状態・確認範囲 |
| --- | --- | --- | --- |
| 069 | [村の通常NPC5件の会話仕上げ](069-village-dialogue-text.md) | [069報告](reports/069-village-dialogue-text.md) | 報告済み。既存5件のtextだけを更新。ローカルのR-01〜R-08・素材・保護26件・007固定/最新・021全8ケースと全ページ・再会話の結果を原資料で確認。子どもの第2ページは画面外の指示先を要求しない回転表現へ品質修正。正式提出SHAのCI・PR・main反映は別途確認する。 |

### 069の取込後確認（2026-10-14 JST）
069は確認済み。PR #43、提出a828b72082f680d6b89616c1a9285b3d1b9707bdのpush/PR全76ジョブ成功、main a634669d9f9f71ad094bba89b23533c6c5105368の全38ジョブ成功。R全8・保護26件不変・最終本文と全ページ確認済み。上の報告済み行は提出時点の経緯として保持。原資料と照合は069報告の正式受入節を参照。


## 2026-10-20 操作品質修正の逐次取込

- 074：確認済み。依頼 [074](074-return-menu-keyboard-focus.md)、報告 [074報告](reports/074-return-menu-keyboard-focus.md)。PR #50、head8e985fc20dec91fd2eb08a118cafb7c84f6901b1、push/PR全76CI・R全8・前後保護26件不変を再検収。main891cba3433ed0ab72f8559051eee1e35a534e323へ通常merge。取込後main CIは提出時の成功とは分けてSTATUSで追跡。旧coastal基点共通失敗・描画警告は原報告に保持。記録作成者はルッカ、次の075との共有ファイル編集は逐次実施。

- 074取込後：main891cba3433ed0ab72f8559051eee1e35a534e323の全38CI・R全8・前後保護26一致を確認済み。
- 075：確認済み。依頼[075](075-items-keyboard-focus.md)、原報告[075報告](reports/075-items-keyboard-focus.md)、[最新main統合報告](reports/075-main-integration.md)。074→075の順でPR #51からmain cb7ca827f7368a2c636a9bf374a9598b3444069aへ通常merge。head382d9b8110ee22220a3d946fecbcdb358937827dのpush/PR全76CI・R全8・前後保護26、統合16ケースを検収。親記録と074の両修正を保持。初回基点ログ欠損・旧coastal共通失敗・実機未確認は報告に保持し、成功と混同しない。取込後main CIは別追跡。記録作成者ルッカ。

- 075取込後：main cb7ca827f7368a2c636a9bf374a9598b3444069aの全38CI・R8・前後保護26不変を確認済み。
- 076：確認済み。依頼[076](076-party-focus-scroll.md)、[原報告](reports/076-party-focus-scroll.md)、[統合報告](reports/076-main-integration.md)。PR #52、head fc845a681cf65a406553109aed11a2610aea45f4、全push/PR76CI・R8・前後保護26・入力5438判定0失敗。074→075→076の順にmain a7f20f203f6d383c5f3534a1fa26774f1e5f868aへ通常merge。旧coastal共通失敗/物理実機未検証は保持。統合後main CIは別確認。親記録はルッカが逐次更新。

- 076取込後：main a7f20f203f6d383c5f3534a1fa26774f1e5f868a全38CI・R8・前後保護26を確認済み。
- 077：確認済み。依頼[077](077-party-disabled-focus.md)、[原報告](reports/077-party-disabled-focus.md)、[統合報告](reports/077-main-integration.md)。PR #53、head28ab00fd5bef57da9b8fe11dfc2e447512efa8ca全76CI・R8・保護26・入力16221判定を検収。074→075→076→077でmain f34967aadf3f668017854d1c958f3ee075d4097fへ通常merge。取込後mainCIは別確認。失敗履歴/旧coastal/実機未検証は原報告に保持。親記録はルッカ。

- 077取込後：main f34967aadf3f668017854d1c958f3ee075d4097f全38CI/R8/前後保護26確認済み。
- 078：確認済み。依頼[078](078-party-action-focus.md)、[原報告](reports/078-party-action-focus.md)、[統合報告](reports/078-main-integration.md)。PR #54、head d2ca76169aeaec9bcb3ed340444830af3712b448全76CI/R8/保護26/入力39139判定を検収。074→075→076→077→078でmain f83e39e1e38174b4beaace908fc46a3823f8e60eへ通常merge。旧coastal/実機未確認等の限界は保持。取込後mainCIは別確認。記録者ルッカ。


- 078取込後：main f83e39e1e38174b4beaace908fc46a3823f8e60e全38CI/R8/前後保護26を確認済み。
- 079：確認済み。依頼[079](079-checkpoint-focus.md)、[原報告](reports/079-checkpoint-focus.md)、[統合報告](reports/079-main-integration.md)。PR #55、head7d2d2a696c0bf4817b05a4a46cea04ce6e212bd5の全76CI/R8/保護26/32実行42223判定を検収し、main c3fb791d7a1d5998a4174f6286d354c3a8eff106へ逐次merge。統合後全38CI/R8/前後保護26も2026-10-20 22:59 UTCに親が直接検収。074〜079全件の統合後確認完了。旧coastal/物理実機未確認/初回失敗等の限界は統合報告に保持。親記録はルッカ。066・073以前の統合は今回承認に含まれない。


## 2026-10-22 coastal検査開始位置の限定修正
- 依頼[coastal](coastal-fixture-fix-2026-10-22.md)、[担当報告](reports/coastal-fixture-fix-2026-10-22.md)。ユーザー承認済み2行を実装。親は原ZIP CRC/SHA、固定main元コードと2行diff、旧exit124→93項目PASS、R全8/保護26/strict/関連回帰を検収。正式head全CI/PR/統合は未実施で完了扱いにしない。通常プレイ撮影/利用者実機は未検証。他追跡7737ファイル/実行体hashは担当原記録による確認。親台帳記録者ルッカ。


### coastalの取込後確認（2026-10-27 JST記録）
coastalは2026-10-23に統合後検収まで完了。PR #57、提出d8f11e2a84e485a06498f3df4c21e61889217139のpush/PR全10 workflow・76ジョブ成功後、main ec48f7fe60e6ba6f10450a103ea5d1a65a8fd895へ通常merge。統合後の5 workflow・38ジョブ、R-01〜R-08、前後保護26件の一致は10月23日の親検収記録に基づく。今回、PRのmergedと同mainのworkflow成功を再取得したが、検査を再実行したものではない。上の未実施行は提出時の経緯として保持。通常プレイ撮影・利用者実機未検証を維持し、080新成果の受領・066/073等の保留は含めない。
根拠：[PR57](https://github.com/hiroshitanaka-creator/RPG-maker/pull/57)、[統合後原CIログ](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/39899036755/job/120236068784)、[STATUS 2026-10-23 13:34 JST](https://github.com/hiroshitanaka-creator/lucca-workspace/blob/main/projects/rpg-maker/STATUS.md)。記録者ルッカ。本追記は資料整合であり、本体の新機能ではない。


## 2026-10-27 080の親受入・通常取込
- 080：専用ブランチ引渡しを本人承認後、原候補d1d30b4/tree524b72d4を不変保管。提出8f1b5c4d19581318f6aa79bdbce14e7bf1d4ab12をPR #59からmain893c5b1159cb9c7d44f45e8eb2dbbfa1ee32ce14へ2026-10-27 23:16 JSTに通常merge。採用済み5室の開発用歩行基盤で、本番世界接続や全ゲーム完成ではない。
- 親検収：原画5件blob・採用PNG5件SHA一致、証拠外20ファイルの範囲、既存変更3件（registry・限定validator・登録順保持generator）、親台帳/本番scripts/test/CI/保護不変。保存15画面を目視。新候補のpush/PR全76jobs・全76check-runs success、R01〜08全PASS/exit0/tests_ran True/parser_failed False、前後保護26一致を直接照合。run40514635416は集計in_progress表示だったが全14jobs/check-runs成功を個別確認し、再実行やキャンセルなし。
- 旧5033a95の再生成失敗は非保護生成器の既存位置保持で修正。元/1回目/2回目38ファイルのGit blob一致、1159項目一意。検査弱体化・時間延長なし。[修正報告](reports/080-registry-order-fix-20261027.md)、[正式保存報告](reports/080-formal-save-20261027.md)、[原報告](reports/080-adopted-room-walking-foundation.md)。
- 限界：親の原ZIP全419項目独立復元はbinary取得制約で未確認。本人承認済みGitHub直接引渡しのコード受入は原候補tree一致・全差分・固定原画・原CIログで判定し、ZIP独立復元済みとはしない。静止画は実操作の手触りや全位置の視認性を保証しない。取込後main CIは本記録時点で別途確認中。
- 原ログ：[push](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/40514635301/job/122225243014)、[PR](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/40514643242/job/122225270883)。親記録者ルッカ。066/073の既存保留を一括解除しない。


## 2026-10-28 081本編接続の親受入
- 本人A承認 I-20261028-001に基づく既存外観・採用5室の出入り・歩行・保存復帰。PR #61、提出7d85b1100b7d8bea9cdffdad67c4ece72c739bbfをmain e6a29a936b44d7f161335dd649c284720e8418a8へ08:32 JSTに通常取込。新人物・台詞・販売・進行イベント・新規則なし。原画371件不変。
- 親検収：全push/PR10workflow・76jobs success（skipped/cancelled jobs0）。原Godot push job122519832060は同head、PR job122519850686は合成79398822cec9c8794ed434e2588de64dc769985a。両原ログでR01〜08全PASS/exit0/tests_ran True/parser_failed False、import成功、保護26前後一致。既存条件分岐のstep60件skipと検査の省略変更を混同せず、CI/保護/契約/検査弱体化・時間延長なしを差分照合。
- 既存帰還先APIの5件契約を保つ互換修正後、26コマンドはe754b1e上でPASS、最終提出は本番tree同一＋旧保存2判定追加と証拠。追加catalog40判定/失敗0、0097630判定、lifecycle13ケース、通常入力を原結果と照合。圧縮原ログ7本SHA一致。[本編報告](reports/081-region3-port-five-room-connection.md)、[互換修正](reports/081-ci-return-catalog-compatibility.md)。初回未実装・CI失敗は履歴保持。
- 提出画面16枚と最終帰還PNGを実画素確認。入口の梁・祭壇で人物が部分的に隠れる留意点、全歩行セルの視認性・物理実機操作感・restart3画像3枚の親目視未確認を保持。接続の自動操作成功を見やすさの完全保証にしない。取込後CI/import・本記録のmain反映は別工程で確認中。全ゲーム完成ではない。066/073/Grok別保留維持。記録者ルッカ。
- 080の旧『原ZIP未確認』は受入当時の履歴。10月28日00:36 JSTまでに419項目/CRC/418manifestと164546599bytes/SHA256 f7d97291e6458b820303434267d2c26bfe39e229b6e8d8d8e3f75975d0fb8019の独立照合・Library保存、最終main4388bf7全38CI/R8/前後保護26確認まで完了。再実行不要。


## 2026-10-28 082会話・状態処理の親受入
- 本人Bと1.A/2.A（I-20261028-002/003）に基づく正常入室後の自動開始、通常確認による完了、中断後冒頭再開、通常ロード/チェックポイント復帰、旧保存互換を接続。PR #63 head b09e4785ceff7d0685d7c46455b0442e06b52aa6を13:13 JSTにmain 5d33e5aa795701cd58b7c6619dccf9e3772ed619へ通常マージ。本文採用と人物初配置採否は区別。
- 最新headのpush/PR各5workflow・38job、計76job全completed/success。原Godot [push](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/40627767676/job/122616711059) と [PR](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/40627773917/job/122616731816) でR01〜08全PASS・前後保護26一致。集中293条件失敗0、本文9ページ/改変負例13件、関連19コマンド全終了0を[正式報告](reports/082-report.md)・固定実装e675acaの原記録と照合。最後2コミットは報告/証拠のみ。本番8パス、保護・CI・原画・world・保存契約は不変。検査弱体化/省略/上限延長なし。
- 補助旧eb423ad回帰64中2FAILを成功扱いしない。081旧段階の親文書比較2条件は082基点mainでも同じ、固定081完成版1235全PASS。もう1件は内部027撮影180秒timeout（外側timeoutではない）。最終必須検証・元CIとは区別。原結果と限界を保持。
- PR作成拒否は本人根拠追加で解消。親のマージclaimは別に拒否され、本人のPR63対象明示承認 I-20261028-005 を保存・読戻し後に同対象を通常マージ。強制push/履歴改変なし。取込後main CIと本記録のmain反映は別工程。
- 未達：初人物配置の採否/視覚統合、任意4職の旧保存移行と取得接続、人間の操作感評価。会話実装完了をS10全体/全ゲーム完成としない。080/081を再実行せず、066/073/Grokの別保留を維持。記録者ルッカ。


## 2026-10-28 083採用済み静止表示の親受入
- 本人I-20261028-008の表示案Bを実画面へ統合。PR #65 head553f36273dfffb8f943b554ec5986e72ac60b2dfを16:17 JSTにmain454a8175fdd1258325b34ed13f8fbe2b1b4d5e2dへ通常マージ。表示専用NPC・既存占有/旧保存位置補正を利用し、決定はface_eventより前で除外。原画/既存会話/保存契約/パレット/保護/CI設定は不変。
- 最新head push/PR各5workflow・38job、計76job全completed/success。原ログ [push](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/40645468248/job/122673148959) と [PR](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/40645473747/job/122673165494) でR01〜08全成功・保護26件前後一致。正式報告 reports/083-report.md、証拠 docs/verification/task-083/。親は本番差分・素材2032bytes/SHA121010a316a31b88dca753ed48bc9404f176a4fe5f0d6dd5508ebf0615559f5d・実Godot512×288画像10枚を照合し具体的な新規不具合なし。独立したGodot再実行とは区別。
- 旧撮影の正常遮蔽による初回失敗を保持し、入力座標1点を新配置へ調整。元48assertion式/順序、閾値、180秒上限は不変。固定世代・最新・後続の対応表、counter-back正負CI原ログ、元118条件の完全保持と実キー追加141条件を照合。素材36/操作保存77/082回帰293も保存済み実行結果成功。新規S10検査はローカル実行でありCI未接続、毎回CI実行済みとはしない。
- PR作成初回拒否は、拒否後に直接取得した本人の承認済み計画継続原文を追加し同API1回の再判定で解消。別経路回避・強制push・履歴改変なし。取り込み後main CIと本記録のmain反映は別工程で確認中。
- 未完：I-20261028-009で採用した旧保存互換方針Aの実装、任意取得接続、後続段階、人間の操作感評価。083完成を全ゲーム完成としない。既存別保留を維持。記録者ルッカ。
