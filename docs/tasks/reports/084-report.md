# 084 採用済み遺跡の入口と帰路接続

承認済みの世界入口・内部着地・帰着を接続した。S10の完了フラグだけで入場し、未完了の旧内部保存からも退場できる。画像・床・階段・保存形式を変更していない。[draft PR #67](https://github.com/hiroshitanaka-creator/RPG-maker/pull/67)。mainマージ、approve、親担当の2文書の編集は行っていない。

基点：`f9169ac4048e98229d34692bc1e9efb6a0a3efaf`。本番実装固定SHA：`5a484cf0d8816c43487eaf6913a900874db702a4`。作業ブランチ：`codex/task-084-region2-ruins-connection-20261029`。最終証拠HEADと実装SHAは区別し、本番・旧検査器の同bytesを照合する。最終HEADのpush/PRの全CI終了は、PRのチェック一覧と最終応答で完全SHA・結果を示す。

指定モデルはGPT-6.1 Sol / High。実モデル・推論設定を取得するAPIはなく、実値・使用量は未確認。実行したエンジンはCI固定のGodot `4.7.2.stable.official.ed1daf0bf`（SHA-256はenvironment.json）。既設4.6.3の結果を検証証拠に使っていない。指定3スキルはカタログとcheckoutに不在で、既存の検証手順をそのまま使った。

## 変更したファイル

- `scripts/world/first_region.gd`：既存の徒歩世界移動成功後に入場判定を追加。既存GameSessionの会話排他を通す。
- `scripts/world/region2_ruins.gd`：世界[176,91]から1階[18,19]・北向きへ入り、出口[18,20]から世界[176,92]・下向きへ戻る。出口はS10完了を要求しない。旧保存補正spawn[18,5]を保持。
- `scripts/world/first_region_view.gd`：実見した採用済みfirst_cave_entrance.pngを、既存の64×64の入口描画経路で再利用。
- `scripts/ui/first_region_atlas.gd`：内部siteの入口を現在地として表示する純粋関数を描画に使用。遺跡・第2村・第3港を既存siteへ対応し、第1地方と第2港を回帰確認。
- `world/region2_ruins.json`、`tools/task011_ruins_defs.py`、`tools/build_task011_ruins.py`：接続メタデータだけを整合。旧壁候補cells3件も保持。MAPS/LINKS・全4階の部屋/床/階段/上層・画像生成算法は不変。
- `tools/check_region2_ruins_connection.gd/.uid`、`tools/check_region2_ruins_connection.py`、`tools/capture_region2_ruins_connection.gd/.uid`：API正負例、独立BFS、全bytes再現、実キー・保存・checkpoint・Atlasを追加検証。
- `docs/tasks/084-region2-ruins-connection.md`：依頼書原本と全bytes一致。Git blob `2d5ae7e841c0b436cb2b40cc1f57d7003ff59232`。
- 本報告と`docs/verification/task-084/`：原ログ、実行記録、検査対応、実画面、hash目録、PR作成結果。全pathはchanged-paths.txt、許可範囲との照合はscope-check.jsonに保存。

`.scope-lock/`、`test/`、保護検査、CI設定、project.godot、assets/registry.json、原画/パレット/全既存画像、GameSession、FirstRegionTravel、地形/沿岸data、082本文、083配置、docs/tasks/README.md、docs/decision-log.mdは変更していない。開始前から未追跡のequipment_rules.gd.uidとcheck_equipment_rules.gd.uidはcommit/pushへ含めない。開始前未pushコミットは0件。

## 検証

本番固定SHAの別checkout `/workspace/task084-final` でインポート後、元の検査を実行した。実コマンド・開始終了・終了値・上限・環境・原ログhashはcommands.json。新規検査はCI未接続であり、ローカル実行と既存CIを区別する。

| 検査 | 実行条件数・結果 | 証拠 |
| --- | --- | --- |
| 新規API | 257条件成功。未完了通過、完了入場、古い入力拒否、旧内部退場、通常保存/ロード、旧spawn補正、Atlas | accepted-runtime.log / runtime-checks.json |
| 入退場の全進行保持 | 257条件成功。位置6フィールドだけを正規化し、cleared/opened/transportを含む残りの全保存値を比較 | full-progress-preservation.log / 同名jsonの検査器hash |
| データ・再生成 | 64条件成功。独立BFS4帰路、旧定義/画像算法不変、2回の全出力path/全bytes一致、本番PNG/出所/接続JSON一致 | accepted-data.log / data-checks.json |
| 実Godot・通常キー | 43条件・512×288の6画像成功。入力反復/echo、S10の実決定9ページ、入退場、手動保存・タイトル/ロード、本番checkpointを確認 | accepted-capture.log / input-trace.json / capture-checks.json |
| 082 | 本文9ページ・13負例、実行時293条件成功 | accepted-shrine-data.log / accepted-shrine-runtime.log |
| 083 | 素材36条件、実行時77条件成功 | accepted-static-data.log / accepted-static-runtime.log |
| 第2沿岸 | 91条件成功。世界遭遇率0.025を保持 | accepted-second-coast.log |
| R-01〜R-08 | 全件PASS。元verify/300秒上限/元judge_outputを使用。R-07は通常操作14条件、R-08は25テスト・3,046 assertion、pending0・invalid=false | accepted-R-01.log〜accepted-R-08.log / accepted-locked-checks.json |
| 保護 | 作業前後とも26/26一致 | frozen-before.log / accepted-frozen-before.log / accepted-frozen-after.log |
| 素材strict | 1,161画像・15音・2字体、問題なし | accepted-assets-strict.log |
| 011固定/最新の通常検査 | 両方で素材・全マス通行・3,552隣接移動・60階段・16保存・16補正・25枚/315キー歩行が成功 | task011-local-components.json / accepted-regression-records.tar.gz |
| 011 CI登録境界 | 1正例・3負例成功、固定完全SHAを保持 | accepted-task011-boundary.log |

追加の原回帰も初回本番SHAで実行し、導入1,988条件、通常画面10条件、31室の位置補正199条件、既存港2,677条件、戦闘復帰、保存型が成功した。各原ログを保存し、最新側は同じ原CIでも検証する。

**ローカル未達を保持する。** `python tools/check_task011.py --completed d258908fbb0397e64d08780694786ef1855c4979 --godot ...` は、027の毎歩通知注入撮影で180秒タイムアウトした。通常の固定/最新検査が成功した後の負荷撮影である。既定描画、LP_NUM_THREADS=2、さらに60fps上限の実行設定でもタイムアウトを保持し、まとめコマンドを成功扱いにしていない。後続のstage拒否・7負例は、このローカルまとめ実行では未到達。原検査・判定・時間上限は変更せず、同じ全条件を実行する最終HEADのGitHub CIの終了も別に確認する。

初回28コマンドは26成功、固定参照未取得と上記タイムアウトの2失敗。参照SHAをfetchした素材検査は同じ検査器で36条件成功。補正後の最終22コマンドは21成功・上記1失敗。各試行を別名で保持し、旧証拠は別checkoutで受けて3つのregression-records archiveへ保存した。検査の省略・閾値変更・上限延長で合格させていない。

## 先行失敗と旧検査の維持

runtime-red.logの型推論エラーを未接続の証拠にしない。型を明示したruntime-red-corrected.logで220条件中、入場/退場の7条件が未接続としてFAIL。data-red.logも未接続の2条件FAILを保持する。

旧027は末尾のreturnリテラルへ故障注入する。追加した退出通知へも一致する重複をmutation-target-red.logで検出し、退出通知を局所変数経由で返して元の注入対象1か所を保持した。さらに旧stageが読むworld_connection.cellsの欠落をlegacy-metadata-red.logで検出し、旧壁候補3件を同じ値で保持した。元62条件を削除せず、注入対象と旧メタデータの継続2条件を加えて64条件とした。旧検査器の全bytes不変はchecker-conservation.json、固定/最新/後続の全assertion群の対応はassertion-migration.mdへ記録した。

初回bc353deのCIは37成功・Godotジョブ取消終了であり、成功扱いにしない。原ログci-initial-godot.logは、通知あり撮影後のstage拒否assertionでの停止と取消を保持する。修正前cd04d23の重い再検証は、新しい固定SHAへ置き換えるため中断し、終了-15として記録した。新しいSHAで同じ全コマンドを再実行し、中断を合格やskipへ変換していない。

capture-atlas.logのdeferred focus ERRORも保存した。検査側で画面切替を待ってから次へ進め、本番コードの変更で隠していない。以後の実撮影は43条件・6枚・終了0・Godot警告/ERRORなし。

## 実画面と限界

[未完了入口](../../verification/task-084/before-complete.png)、[完了後着地](../../verification/task-084/after-complete-entry.png)、[通常退場](../../verification/task-084/interior-return.png)、[保存復帰後の帰着](../../verification/task-084/loaded-return.png)、[内部Atlas](../../verification/task-084/interior-atlas.png)、[帰着Atlas](../../verification/task-084/returned-atlas.png)。静的合成ではなく本番UIの実画面。

採用済み1階背景を担当環境で実見し、[18,19]/[18,20]が南の石床に立つことを確認した。旧y21の壁は開けない。世界入口は採用済み石造入口の再利用で、新しい外観を創作していない。既存目標ruins-temple.jpgと照合したが、目標画像の画素を使用していない。

人工境界保存からの本番キー操作であり、本人の初見プレイ・全長距離行程の通しプレイではない。人間による手触り評価は未実施。世界の帰路は歩行可能だが、遭遇率0.025を保持し「無遭遇」とは報告しない。内部遭遇/ボスはfalseのまま。鍵・戦闘・報酬・未決本文・任意4職の取得規則は追加しておらず、ゲーム全体の完成とはしない。

## PR・判断・戻し方

初回draft作成は自動承認レビューに拒否された。理由は「実装の継続は承認されているが、PR作成の明示的本人承認を確認できない」。同head/all stateの読取りは0件。初回の拒否・対象・未実行確認はpr-blocker.jsonに保持する。

拒否後、親が本人の継続許可原文Sentinel_88686aa1bca08191b42f3c9365adb23e（項目5/6）とSentinel_f4892d63b37881918711fe97b2e1b32eを直接取得して追加提供した。今回の同repository/head/base/draftと照合し、未作成を再確認して同じcreate_pull_request APIを1回だけ再判定。2026-10-28T21:26:58Z、draft PR #67の作成に成功した。pr-create-result.jsonとretry_outcomeへ保存した。証拠をAPI引数へ混入せず、別経路・反復再試行・mainマージ・approveは行っていない。

親記録用の判断：入場だけをCOMPLETE_FLAGに限定し、保存受理/出口は旧互換を守る。接触と着地を1マス離し、既存の1歩処理と入力排他を使う。旧候補cellsは旧拒否検査のデータ契約として保持する。戻す場合は084の実装コミットを新しい訂正コミットで差し戻せる。履歴改変は不要。初期計画と逐次記録はreport-history.mdへ保存した。

## 証拠HEADの再確認

`a4c545a954e4773a4f0e7255cab0f3e5d2bbe616` で、照合を強めた新規API257条件、R-08（25テスト/3,046 assertion）、保護26件一致を再確認した。evidence-head-runtime.log、evidence-head-R08.log、evidence-head-R08.json、evidence-head-frozen.logへ保存した。本番・旧検査器は実装固定SHAと同bytesである。

この補助起動の最初は手動コマンドのXDG指定漏れで標準保存先の作成が拒否され、254条件中73件失敗となった。environment-probe-failure.jsonへ対象・理由・観測結果を保存した。ツール返却上限でその起動ログは一部省略されており、欠落部分を補作していない。拒否された保存先へ再試行せず、既存の隔離XDGで同じ検査器を実行し、上記257条件が成功した。
