# 029 遺跡の検査修正と表示調整の最終レビュー

## 対象と検証計画

- レビュー登録：`348ea2dc30914f8c923a4ed608be05442fcf6e3a`。対象：`72abb3f1612351bb74215ce9045b59229a51e5a5`。
- 027基点 `791ec46e07bd4816bc14da3fc5e223318ac42c5f`、最終 `3ca51fcd756d885d6e0fd309f47efee3b841050c`、028基点 `a5f3f65dcb63e8fa86a8c68e702ebf931115cd85` と実差分を比較する。
- 026のP2、027/028の依頼・報告を読み、固定当時の条件、最新の継続条件、確認用探索復帰と実戦の区別を照合する。
- 対象SHAの隔離worktreeでGodot4.7.2による正負例・通行・階段・保存を再検証し、描画環境が用意できれば既存上限のまま撮影を再実行する。既存実画素とコードも独立に照合する。
- 指定4件のCIを直接照会し、全ジョブ終了と対象SHAのログを確認する。保護26・原画・他42体・011以前の検査・workflowと上限の不変を確認する。
- 作業開始時の未コミット変更0、登録SHAとremoteの差0。提出は本書と依頼書の状態行のみ。実装修正・main反映・採否代行を行わない。

## 判定

**PASS（026のP2解消と028の表示指定への適合）**。実差分・対象CI全40ジョブ・独立した正負例・前後実描画から、今回の範囲で修正を求める機能上の指摘は0件。

ただし、ローカルの毎歩通知撮影は180秒でTIMEOUTとなり、外側検査全体は未完走。これを合格としていない。対象CIでは同じ固定／最新／通知あり撮影が全成功している。既知の時間余裕の小ささが環境差で顕在化した検証上の制約として親へ返す。見た目の採否とmain統合の判断は代行しない。

## 実行結果

### 実差分と条件の保持

- 027基点→最終で本番 `scripts/`・`world/`・`assets/`・`test/`・`.scope-lock/`・workflow・project設定の差0。028基点→対象でも原画を含むassetsのGit treeが同一。本番の変更は `scripts/ui/rpg_battle_view.gd` の対象ID限定倍率のみ。
- 011以前の基点 `0f781630fa75b620f06e5d71430979a1c5162ef4` に存在する `tools/` 447ファイルを対象のGit blobと全件比較し、変更0。保護26/26一致。
- 固定側は `d258908fbb0397e64d08780694786ef1855c4979` の別checkoutで当時の検査器を使用する。無遭遇・入口未接続・変更範囲・2回再生成・全経路状態比較・全25枚等を保持。登録 `8ae87d658fe04f4053ea2f258d973e0862530085` のCI本文比較も不変。
- 最新側は道中のbattle形式（非空ID・既知敵の配列・整数seed）を検証し、本番開始APIの受理後に、通知後の全保存値を新しいGameSessionへ取り込んで探索へ戻す。勝利・報酬の検証ではない。階段ではmoved必須、着地・向き・layer/nodeを確認し、room/cell/facing/entry_lock以外の全状態を直前直後で比較する。overworld全体を除外していない。静止要求の拒否と全状態一致、全4方向の保存16回と補正16回も保持。
- 撮影は本番キー入力後のコマ値を維持して探索の表示時刻だけを合わせる。歩行コマ条件・全画素条件・通常移動時間・表示時間を緩めていない。028の011撮影差分はUV計算の独立期待値（対象1.125／他0.75）1行のみで、実装倍率の自己参照ではない。
- workflow不変。runtime120秒・capture180秒・import600秒、既存job上限を維持。既報の毎歩通知撮影173.666／176.454秒は180秒に対して余裕が小さい事実として残す。

### 表示の実物評価

対象SHAの `python -B tools/check_task028.py --godot /tmp/review029/bin/godot` は終了0。前後各93項目、前12.247秒／後12.157秒でPASS。原画・全assets1,611ファイル、他42体の領域／配置／足元、他6体の2画面不変を確認した。

- 表示rect（内部座標）は `[124.25,82,91.5,114]` → `[101.375,25,137.25,171]`。縦横各1.5倍、素材倍率0.75→1.125、足元中心(170,196)不変。
- 頭・腕・足が画面に収まり、上端25px、下部UI開始223pxまで27px。味方4人と30px前進位置との重なりなし。最近傍の敵・透明部93,708画素が全一致。
- 今回再撮影した前後のbattle-3と他敵画面は提出済みPNGと全バイト一致。after/battle-3のSHA-256は `2b7e0b66e6b37dc710a2556fc9c675e82d3cda822cf2600d07112ba9e519724b`。
- 保存済み前後PNGをPillowでも独立比較し、変更53,856画素、1024×576上のbbox `(203,50,477,392)`。対象領域外は全画素不変。他2ページはPNG全バイト一致。
- 既存比較画像と今回再撮影したafter/battle-3.pngを目視。全身・足元・味方との空間分離、発光色とドット輪郭を確認した。背景に近い暖色主体という性質は維持される。見た目の採否は依頼者の回答待ちのままで、レビューPASSとは区別する。
- 既存 `docs/verification/task-028/before-after.png` を再アップロードしていない。

### 直接照会した対象CI

CLIのAPI照会は403。接続済みGitHub読取りで各run本体・全job・各stepを取得し、全てhead_shaが対象72abb3fでcompleted/successと確認した。

| run | 全ジョブ結果 |
| --- | --- |
| [37297608946](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37297608946) | 3/3 success |
| [37297609008](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37297609008) | 17/17 success |
| [37297609664](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37297609664) | 3/3 success |
| [37297609649](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37297609649) | 17/17 success |

Godot job `111722438335` と `111722440056` の実ログでcheckout完全SHA、R-01〜R-08全PASS、`TASK027_PASS: positive=1 negative=7 capture=25 stage_rejection=1`、`TASK011_PASS` の固定／最新SHA、登録8ae87d6のCI境界正1・負3 PASSを照合した。固定／最新jobに存在する相互排他的なstepのskipは既存workflowどおりで、今回追加した省略ではない。

### ローカル独立実行

作業領域 `/tmp/review029/target` は対象72abb3fの別worktree。既設4.6.3は検証に使用せず、公式4.7.2 ZIPのSHA-256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` を照合し、`4.7.2.stable.official.ed1daf0bf` を使用した。XDG保存先、Xvfbと公式Debian Mesaパッケージを一時領域へ展開し、X11／Vulkan／llvmpipeで実描画。OS設定・本番保存・検査の上限は変更していない。

| コマンド | 結果 |
| --- | --- |
| `python tools/check_frozen_files.py` | 保護26/26一致 |
| `python tools/validate_assets.py --strict` | 素材1154・音15・字体2・パレット3、問題なし |
| `godot --headless --editor --import --quit` | 終了0、SCRIPT ERROR／ERROR／WARNING／Parse Errorなし |
| `python tools/run_locked_checks.py` | R-01〜R-08全PASS、exit0・tests_ran=true・parser_failed=false |
| `python tools/check_task011_ci_boundary.py --godot /tmp/review029/bin/godot` | 終了0、正1・負3 PASS |
| `python -B tools/check_task028.py --godot /tmp/review029/bin/godot` | 上記の前後実描画・全素材・変更範囲・独立倍率照合PASS |

固定側は14,417項目、最新側は13,662項目がPASS。各5,067マス・3,552隣接移動・階段60回・保存16回・補正16回。固定import45.271秒／素材37.763秒／runtime10.883秒／capture123.129秒、最新素材4.424秒／runtime11.498秒／capture120.526秒。固定・最新とも全25枚の画像と元の画素条件が合格した。

`python tools/check_task011.py --completed d258908fbb0397e64d08780694786ef1855c4979 --godot /tmp/review029/bin/godot` は固定／最新の素材・runtime・撮影までは上記のとおりPASSしたが、その後の027毎歩通知撮影が180秒でTIMEOUTとなり、`check_task027.py:144` の「通知あり撮影」でAssertionErrorとなった。**ローカル外側全体はFAIL／未完走であり、全PASSと表記しない。** 対象CI2件の同じ検査の成功とは区別する。上限延長、描画項目削減、成功扱いへの置換はしていない。

通知＋保存値変化の正例runtimeは終了0・13,668項目・2回復帰でPASS。撮影の時間切れにより外側runnerが未着手のまま終了した負例は、別worktreeへ独立driver `/tmp/review029/negative_review.py` から注入し、対象SHAの未変更runtimeで個別に再現する。これは撮影を省いた外側PASSではなく、個別のruntime検証である。結果は以下のとおり。負例は全て終了1、Parse Error・SCRIPT ERROR・ERROR・WARNING・timeoutによる失敗ではなく、指定したassertionのFAILを確認した。

| 個別再現 | 結果 |
| --- | --- |
| 階段の誤着地 | 着地・向き等20件FAILで拒否 |
| 静止再遷移 | 静止要求等166件FAILで拒否 |
| 階段で所持品破損 | 直前直後の状態保持60件FAILで拒否 |
| 階段で進行破損 | 同60件FAILで拒否 |
| 階段で地図破損 | 同60件FAILで拒否 |
| 無効通知 | 通知妥当性4,411件FAILで拒否 |
| 階段上でbattle通知 | 階段接触moved条件60件FAILで拒否 |
| 同じ正例をstage指定 | 無遭遇条件を含む2,575件FAILで拒否 |

毎歩通知runtimeの独立追加確認は終了0、19,182項目、1,840回の本番戦闘API受理・確認用復帰、失敗0。115.957秒／120秒で成功した。7負例は各7.506〜8.247秒、stage拒否は8.617秒。通知あり実描画の未完走と、runtimeでの正負例成功を混同しない。

## 未確認・範囲

- 通知後の復帰は確認用探索への復帰。本番の戦闘攻略・勝利・報酬・未接続の進行を検証したという意味ではない。
- 見た目の採否は依頼者の回答待ち。011/026全体の採否やmain統合を代行しない。
- 今回の一時実行ログ・生成画像は隔離worktreeに保持し、指定2文書以外を提出ブランチへ持ち込まない。結果の数値・コマンド・根拠は本書に記録し、既存の提出済み画像へ対応付けた。
- 毎歩通知のローカル実描画は180秒で時間切れ。今回の環境での完走を未確認とし、CI成功や保存済み画像でローカル成功を代用しない。既報の173〜176秒という余裕の小ささを実際にも確認した。
- このレビュー文書コミット自身のCIは対象72abb3fの成功で代用しない。提出時の状態を親への最終通知で区別する。
- 変更ファイルは `docs/tasks/029-review-ruins-final.md` の状態行と本書のみ。原画・素材・実装・検査・設定・保護ファイルへの変更0、mainへの書込み・マージ0。
- レビュー対象SHA：`72abb3f1612351bb74215ce9045b59229a51e5a5`。報告提出の最終SHAはcommit/push後に親へ返す。

## ユーザー向け要約（ネタバレなし）

移動・保存の検査修正と指定された表示サイズを確認しました。原画や他の表示への影響はありません。見た目の採否とmainへの反映は行っていません。
