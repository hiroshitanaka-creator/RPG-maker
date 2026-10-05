# 026 遺跡下準備の独立レビュー

## 作業前の計画

- レビュー登録：8d6149c9c097506b2c6354fc484805ad04947b3b。
- 基点：0f781630fa75b620f06e5d71430979a1c5162ef4。対象：48667e38ae331b1b3cd6d917ce050e47715372bc。
- 完成固定：d258908fbb0397e64d08780694786ef1855c4979。CI登録：8ae87d658fe04f4053ea2f258d973e0862530085。
- 基点と対象の全差分、011依頼書・報告・コード・台帳を照合。対象専用の別worktreeで検証し、レビュー枝の変更を指定2文書に限定する。
- Godot 4.7.2の固定／最新検査、保護検査、素材検査、CI照会を区別して記録する。床と通行の一致は原画・全体図を目視して独立評価する。
- 実画素を見る画像：原画4階・敵4体・ボス・戦闘背景、派生4背景・上層、011 floor1〜4-overview、latest/images の歩行・奥・手前・階段・battle-1〜3、enemy-assets、visual-target-comparison。
- 開始時に未コミット変更なし。remote tracking refが未作成なので未push一覧は登録ブランチの実remote SHAと照合する。

## 判定

**差し戻し（P2・1件）**。現行の下準備の通行・階段・保存と素材形式は合格。後続の正当な遭遇追加を拒否しないという011作業8の要件は満たしていない。実装修正・mainへのマージは行っていない。

## 指摘（重大度順）

### P2：最新の階段回帰が道中の戦闘通知を拒否する

- 場所：`tools/check_task011_runtime.gd:83-89`。特に85行目は `stage` に関係なく、階段までの全歩で `kind == "moved"` を要求する。70行目の同種条件は正しく固定側だけに限定されているが、85行目に残っている。
- 影響：後続で許可された通常遭遇を実装し、本番APIが既存仕様どおり `kind: battle` を返すと、地形・階段・保存が正常でも最新回帰が失敗する。撮影器も戦闘を終了して探索へ戻る経路を持たない。現在は未接続なので現行CIの成功と矛盾しない。
- 独立再現：対象SHAの別worktreeだけで `Region2Ruins.move` の最終return直前へ下記を挿入し、未変更の検査器を **`--stage` なし** で実行した。階段の接触・着地・向きは変更せず、非階段の移動通知だけを既存形式の戦闘通知へ置き換えた検証用fixtureであり、本番への遭遇実装・採用ではない。

```gdscript
if state["entry_lock"] != "region2_ruins_stairs":
    return {"kind":"battle","id":"ruins_review_probe","enemies":["slime"],"seed":1}
return {"kind":"moved"}
```

```bash
# 対象SHAの別checkout・インポート済み、専用XDG領域で実行
RPG_QA_SAVE_PREFIX=task011-review-future \
TASK011_EXECUTION_SHA=48667e38ae331b1b3cd6d917ce050e47715372bc \
timeout 120 /tmp/026-review/engine/godot --headless \
  --path /tmp/026-review/future --script res://tools/check_task011_runtime.gd
```

- 結果：終了1、`stage=false`、11822 checks。失敗1840件はすべて「通常移動APIで階段へ歩く」。5067マス、3552隣接移動、階段60回、保存16回、補正16回の他のassertionは成功した。未変更の対象では同コマンドの検査がPASS。記録は検証用領域 `/tmp/026-review/future-runtime.log` とfixtureの `docs/verification/task-011/latest/runtime.json`。この差分は提出ブランチへ入れていない。
- 最小修正案：無遭遇の全経路条件は完成固定側に残す。最新側では道中の有効イベントと階段そのものの遷移を分離し、階段直前・直後で位置以外の状態を比較する。最新撮影も後続イベントを適切に処理できる確認状態を用意する。後続遭遇を有効にした正例と、階段の誤接続・静止再遷移を拒否する負例を追加し、既存項目の削除や黙ったskipで解決しない。修正は制作側の別作業とする。

## 実差分・実装の根拠

- `git diff --name-status 0f781630… 48667e38…` を全件照合。既存の本番変更は `first_region.gd` の4箇所と `first_region_presentation.gd` の地図追加1行。その他の実装・素材・道具は011の追加。既存検査、原画、`.scope-lock/`、`test/`、`project.godot`、AGENTS、既存場所・世界のデータの差分なし。
- 完成固定d258908と提出48667e3の `scripts/ assets/ world/` に差分なし。CI登録・報告・新規外側検査器の変更と本番完成点を混同していない。
- 素材台帳をJSONで独立比較し、既存項目の内容と相対順序が一致。追加は14素材。敵の候補台帳には7体・仮称・仮値・遺跡の場所を記載し、再利用2体は既存画像を維持。
- 本番移動は隣接・通行判定後だけ遺跡の専用処理へ分岐する。6接続は接触と着地が異なり、静止の同一セル要求は隣接判定で拒否される。保存補正は各階のspawnへ既存経路で接続。世界入口、出口、遭遇、ボス、物語、宝箱は本編へ接続されていない。
- 固定側は実際に `git worktree add --detach <dir> d258908…` を作り、当時の素材・runtime・撮影器を実行する。最新側は対象48667e3を別実行する。CI既存本文の比較先は登録8ae87d6のGit blobで、最新CIに後続の追加を許容する。
- 完成SHAと登録ステップの完全SHA一致、追加1ステップ以外のCI全文不変を確認。境界正例1件（将来のCI追加）と負例3件（登録時上限改変、完成SHAの文字列改変、ステップ重複）を実行しPASS。負例はGit読取り結果への注入であり、あらゆる参照・検査器の同時改変に耐える証明とはしていない。
- 過去の初回失敗はattemptとして残っている。今回の判定に使う完成点・提出点の成功と取り違えていない。

## 独立実行した検査

作業領域は `/tmp/026-review/target`（対象48667e3の別worktree）。レビュー枝へ検査生成物を持ち込んでいない。Godotは公式ZIPのSHA-256がCI指定 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` と一致し、版は `4.7.2.stable.official.ed1daf0bf`。既設4.6.3は検証に使っていない。

| 実行 | 結果 |
| --- | --- |
| `python tools/check_frozen_files.py` | 保護26/26一致 |
| `python tools/validate_assets.py --strict` | 素材1154・音15・字体2・パレット3、問題なし |
| Godot `--headless --editor --import --quit` | 終了0。SCRIPT ERROR / ERROR: / WARNING: / Parse Errorなし |
| `python tools/run_locked_checks.py`（PATHを4.7.2へ設定） | R-01〜R-08すべてPASS、各exit0、tests_ran=true、parser_failed=false |
| `python tools/check_task011.py --completed d258908fbb0397e64d08780694786ef1855c4979 --godot /tmp/026-review/engine/godot` | 固定版のimport PASS（37.002秒）、素材PASS（原画7・素材16、再生成・範囲照合）、runtime PASS。その後ローカル描画用xvfb-run不在で停止。**外側全体をPASSとはしていない** |
| 対象48667e3の `python tools/check_task011_assets.py` | PASS、原画7・素材16、stage=False |
| 対象48667e3の `check_task011_runtime.gd`、専用XDG・保存接頭辞 | PASS、5067マス・3552移動・60階段・16保存・16補正 |
| `python tools/check_task011_ci_boundary.py --godot /tmp/026-review/engine/godot` | 正1・負3すべてPASS |
| 上記遭遇通知fixtureのruntime | 意図した反証：exit1、1840件の同一条件失敗 |

仮想画面・Vulkanドライバ導入も試したが、aptのシステム領域がread-onlyで導入できなかった。ローカル実描画再撮影は未実施。時間上限の延長・検査条件の変更・headless画像での代用はしていない。

## GitHubで直接確認したCI

CLI照会は403だったが、接続済みGitHubの読取りから全ジョブ・各ステップの終了状態を取得した。対象のGodot jobログでもcheckout完全SHAと最終PASSを確認した。

| run | ジョブ結果 |
| --- | --- |
| [37281488531](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37281488531) | 3/3 completed/success。素材、試遊前、Godot・凍結受入 |
| [37281488394](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37281488394) | 17/17 completed/success。固定／最新の分岐に対応したskipは既存CI設計どおりで、011による検査省略ではない |

Godot job `111670363158` のログに、checkout `48667e38ae331b1b3cd6d917ce050e47715372bc`、R-01〜R-08 PASS、`TASK011_PASS: completed=d258908fbb0397e64d08780694786ef1855c4979 latest=48667e38ae331b1b3cd6d917ce050e47715372bc`、`TASK011_CI_BOUNDARY_PASS: positive=1 negative=3 registered=8ae87d658fe04f4053ea2f258d973e0862530085` を確認。ローカルでできなかった固定／最新の実描画はこのCIの成功として区別する。既存各job/commandの上限・条件は基点との差分で不変。

## 画像の評価（採否は親・依頼者へ）

原画4階・敵4体・ボス・戦闘背景、全体図4枚、上層4枚、歩行4枚、柱の奥／手前8枚、戦闘3枚、敵一覧、目標比較図を実画素で確認した。

- 1階の右室の穴、3階の上下の水面は不通、中央の橋は通行として分離されている。2階の周回通路と最下層の柱間・細い連絡路も原画の床へ対応している。単にlayout同士が一致したという根拠だけで目視一致を判定していない。全888床のあらゆる足元画素を人が一つずつ測ったとはしていない。
- 原画全体の縮小・3階と最下層の位置合わせで、部屋が切り落とされている様子はない。1階3/4、他階7/8で人物が通路を歩ける比率になっている。画像全体を512×288へ押し込まず追従カメラを使用。3階・最下層の端では余白が見えるが、人物や必要な道が画面外へ固定される問題は確認していない。
- 奥では柱が人物の一部を隠し、手前では人物が見える。上層は透明atlasで、柱の上部・巨像等の切出し。斜めの切出しは背景同一RGBの再配置であり、原画の欠損と同一視しない。8枚の標本以外の全上層境界の人間操作確認は未実施。
- 新規敵は槍・頭・足が画像端で切れていない。PNG不透明領域は通常敵96×96の内部、砂の霊も上端に2pxの余白。ボス192×160ではbbox(35,6,157,158)で余白があり、青い発光・目の模様は残る。戦闘見本で敵6体・ボスは味方から分離され、背景による身体の遮蔽や画面切れは見つからない。
- 暖色主体で参考の冷色・苔とは色調が異なる。砂の霊と砂岩の人形は床と近い色で、番犬・翼像より輪郭の対比が弱い。これは見た目採否へ渡す観察で、独断で原画や配色を変更しない。
- 3階右下↔最下層左上等は、絵の上り方向と進む階の上下が一致しない。この原画上の制約は011報告に明記され、元絵を変えないという依頼範囲で接続されている。採否を代行しない。

## 親へ渡す既存確認画像とLibrary

すべて確認用状態の既存画像で、元の実行SHAは8ae87d658fe04f4053ea2f258d973e0862530085。提出48667e3との本番・素材差分はないが、48667e3で撮り直した画像と表記しない。画像は再生成・改変していない。

| 用途 | リポジトリ内の元画像 |
| --- | --- |
| 1階歩行 | `docs/verification/task-011/latest/images/floor1-walking.png` |
| 2階歩行 | `docs/verification/task-011/latest/images/floor2-walking.png` |
| 3階歩行 | `docs/verification/task-011/latest/images/floor3-walking.png` |
| 最下層歩行 | `docs/verification/task-011/latest/images/floor4-walking.png` |
| 柱の奥／手前 | `docs/verification/task-011/latest/images/floor1-behind.png`、`floor1-front.png` |
| 敵6体／ボス | `docs/verification/task-011/latest/images/battle-1.png`、`battle-2.png`、`battle-3.png` |

現行の [Libraryスキル](skill://plugin_connector_1p_1b8ff8edfc1481918b252c8277e23125/library/SKILL.md) と prepared-uploads 手順を読み、現行ヘルパー3ファイルを新しい私用ディレクトリへ取得し、実在する上記9画像を順序付きで保存しようとした。Libraryへの接続エラーで保存に至らなかった。**確認済みlibrary_file_idは0件（なし）**。未確認ID・別画像のID・旧手順での代用はしていない。親は上記パスの同じ元画像を利用できる。

## 未達・未確認と引渡し

- 修正が必要：P2の最新回帰の段階分離。制作側への差し戻しであり、このレビューでは直していない。
- ローカルの実描画再撮影は環境依存で未実施。対象CIの固定／最新実描画成功と既存画像の目視を根拠として区別した。
- Library画像共有は接続エラーで未達。IDなし。見た目の採否は親・依頼者が行う。
- main未統合。後続依頼・物語・名前・新規の遊び方の決定は行っていない。
- レビュー対象の最終SHA：`48667e38ae331b1b3cd6d917ce050e47715372bc`。レビュー提出コミットの完全SHAはcommit/push後の親への最終通知に記載する（自己参照SHAを文書へ捏造しない）。
- 変更ファイルは、この報告書と `docs/tasks/026-review-ruins-groundwork.md` の状態行だけ。レビュー文書コミット自身のCI結果を対象011の全20成功で代用しない。
