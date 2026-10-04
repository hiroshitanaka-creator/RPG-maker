# 004 停止中の村の色調整を保全して検証する

- 状態：作業中
- 担当：Codex（GPT-6.1 Sol／High）
- 依頼日：2026-10-04
- 前提：001・002・003が「確認済み」であること。依頼者の2026-10-04 03:46 UTCのローカル再開指示を指揮役が確認していること。同じ場所を変更する別の依頼が作業中でないこと
- ブランチ：`codex/task-004-village-colors`。新しいローカルタスクで扱う。停止中の`codex/sprint6-village-color`の作業ツリーを保全・棚卸ししてから分ける
- 担当の場所：下の「作業内容2」の限定一覧、この依頼書の状態行、`docs/tasks/reports/004-resume-village-colors.md`、`docs/decision-log.md`の本件記録だけ
- 変えてはいけない場所：上記以外。特に原画全件、停止中候補の未照合ファイル、`AGENTS.md`、`docs/experience-spec-v2.md`、`docs/roadmap-v2.md`、`docs/story-outline.md`、`docs/current-status.md`、001・002・003の依頼書／報告書、`scripts/`、`scenes/`、`data/`、`world/`、`test/`、`.scope-lock/`、保護検査、`.github/`、`project.godot`、`addons/`、対象以外の素材・パレット

## 目的

停止していた村の外観と4室の色調整候補を失わずに引き継ぎ、原画にある色と既存仕様の範囲で仕上げ、最新の実描画・回帰・CIまで検証する。村の施設、本番接続、人物、商品、職業解放、遺跡は実装しない。

## 背景

- この依頼書は、main `d2ad6c044920a44340b725987b86c36f4adf7952` の実在する`docs/tasks/_template.md`の見出しに従う
- 002の計画報告はmain `d17f7dfd377b471764c3148c8e8f5ce4ae5cd067`に登録済み。指揮役の確認記録は`d2ad6c044920a44340b725987b86c36f4adf7952`。開始時には最新mainと対象SHAのCIを改めて確認する
- 再開先は依頼者が指定した接続済みのPC（MSI、既存作業場所 `C:\Users\tanak\RPGゲーム`、再開指示 `Sentinel_98b1c03f9a8481918c95e60eac7e2f78`）。実際のリポジトリの場所をそのPCで確認する。クラウドのパスをPCのパスと見なさない
- 停止時点は`codex/sprint6-village-color`、HEAD `6384ee81f99a1c3262823fa5fda04075f214f459`、未コミット35ファイル。内訳として背景／上層PNG10、パレット1、出典記録2、比較PNG15、検査JSON1、Python6が報告されている。これは未照合の申告であり、全35件を一括許可する一覧ではない
- 4色`#7E4C2C`、`#CC773D`、`#A7592D`、`#713D1D`は停止中の候補。原画由来、採取位置、色の必要性、先頭80色の不変を再確認する。まだ見た目の採用済みではない
- 前回は再生成と負例11件まで。最新の実描画、R-01〜R-08、CIは未実施として引き継ぐ。過去の成功を新しい成果の成功として使わない
- 003・002への追加依頼ではなく004の新しいタスクとする。別の制作範囲の決定を、この色調整の作業へ混ぜない

読むもの：`AGENTS.md`、`docs/tasks/README.md`、本依頼書、`docs/asset-spec.md`、`docs/region2-village-backdrops.md`、`assets/source_records/region2-village-backdrops.json`、`assets/registry.json`、関係する生成・検査コード。`.scope-lock/spec.lock.json`は保護対象を調べるための読み取りだけとする。作業場所の`.agents/skills`に関連するものがあれば、その`SKILL.md`を読む。

## 作業内容

1. 変更する前に、PC・リポジトリ・HEAD・現在のブランチ・追跡先・未pushコミット、staged／unstaged／untrackedをそれぞれ調べる。停止時35件の全パス、変更種別、既存ファイルのSHA-256、差分、未追跡ファイルの実体を別の退避先へ保存し、退避物が読めることを照合する。現在が申告と違えば差を報告し、他の作業を混ぜない。`reset --hard`、`clean`、`stash drop`、元ブランチの削除、force push、履歴の書換えは行わない。退避先のファイルも勝手に消さない

2. 停止成果を次の一覧と照合する。固定パスの一覧は以下だけとする

   - `assets/palette/natural.gpl`：開始時先頭80色とその既存バイトを保持し、対象原画の実在色を末尾に最大4色追加する部分だけ
   - `assets/town_backdrops/region2_village_exterior.png`
   - `assets/town_backdrops/region2_village_exterior_overlay.png`
   - `assets/interiors/region2_village_inn.png`
   - `assets/interiors/region2_village_inn_overlay.png`
   - `assets/interiors/region2_village_item.png`
   - `assets/interiors/region2_village_item_overlay.png`
   - `assets/interiors/region2_village_weapon.png`
   - `assets/interiors/region2_village_weapon_overlay.png`
   - `assets/interiors/region2_village_shrine.png`
   - `assets/interiors/region2_village_shrine_overlay.png`
   - `assets/source_records/region2-village-backdrops.json`：この5地形の色選択・出典・再生成に必要な記録だけ。座標・通行・変換寸法は変えない
   - `tools/build_region2_village_backdrops.py`：この5地形に使う許可色の選択だけ
   - `tools/check_region2_village_backdrops.py`：既存の検査を保ったまま、原画由来の末尾追加色を厳密に照合するための追記だけ
   - `tools/validate_assets.py`：先頭80色の完全保持と、証拠付き最大4色だけを認める限定検証。無条件の上限引上げは不可
   - `tools/check_first_region_gado_data.py`：パレット全体SHAの置換は禁止。旧80色部分の既存SHAを維持し末尾の許可色を別に厳密検証する対応だけ。導入本文・描画・既存アサーションの検出能力を保持する
   - `tools/check_region2_village_palette.py`：必要な場合だけ新設してよい、本件専用の色出典・既存色不変・負例検証。既存すると主張せず、開始時に同名ファイルの有無を確認する
   - `docs/verification/region2-village-backdrops/`：`exterior`、`inn`、`item`、`weapon`、`shrine`の5箇所の既存比較・実描画画像と、対応する実測JSON・READMEだけ。原画、目標画像、他スプリントの証拠へは書かない
   - `docs/region2-village-backdrops.md`：今回の色調整の実結果、追加色と出典、残る未評価を追記する部分だけ

   未照合の「2つ目の出典記録」「残るPythonのパス」「検査JSON」の名前を推測して新設・上書きしない。開始時一覧から実在のパスと役割を指揮役へ報告する。上の一覧外の候補は保全・読取りにとどめ、指揮役が004の担当パスへ明記する前に変更・stage・commitしない。共通処理や別の素材への波及があるものは別途判断する。新設専用検証へ既存候補を移し替えるために元ファイルを削除することもしない

3. 全候補の保全と許可範囲の照合が済んでから、新ブランチへ引き継ぐ。最新mainの取込みでローカルの未コミット差分を上書きしない。通常のcommit、別worktree、バックアップを用いた再適用など、内容を失わず元に戻せる方法を選び、選択・理由・戻し方を`docs/decision-log.md`へ記録する。既存候補を保存するだけのcommitと、検証済み提出物のcommitを混同しない。他の作業の未pushコミットを一緒にpushしない

4. 元の5原画は次のファイルと照合し、全バイトとSHA-256を維持する

   - 外観：`assets/_incoming/owner-2026-10-01-region2-port/51294233-3D3D-4A6A-A54F-D8429C67CACF.PNG`
   - 宿：`assets/_incoming/owner-2026-10-03-region3-port/01-oasis-inn.png`
   - 道具屋：同フォルダ`02-oasis-item-shop.png`
   - 武器屋：同フォルダ`03-oasis-weapon-shop.png`
   - 祠：同フォルダ`04-oasis-shrine.png`

   候補4色について、原画パス、SHA、採取座標、RGB、元の減色で失われた重要な色を記録する。原画にない補間色や作った色は追加しない。4色が必要な根拠がなくても、数合わせで追加しない。4色を超える場合は依頼者判断を求め、その部分に依存しない検証を続ける

5. 色選択だけを調整する。既存の最近傍縮小、配置寸法、原画1画素との対応、64色以下の個別画像、背景と同じRGBの上層、二値透過、足元順、通行・入口・家具の座標を維持する。既存の先頭80色の値・順序・記述と、この村以外の画像を変えない。`world/region2_village_backdrops.json`と通行・上層マスクが変わるなら原因を調べ、色調整の副作用を消す。マップの作り直しでつじつまを合わせない

6. 既存80色と最大4色の原画由来追加という条件を、任意の84色を通す検査へ置き換えない。無関係なパレット、通常素材の色数・寸法・透過、台帳の出所、元の固定基準SHAを維持する。専用検証は正規入力の成功に加え、少なくとも報告済み負例11件の実体を読み、同じ失敗検出を再実行する。旧色の変更・並べ替え・削除、5色目、原画にない色、出典の欠落・虚偽、村外への影響を検出できることを示す。負例数の一致だけで同じ網羅性と扱わない。対象が保護検査に該当したら変更せず、正確なパスと必要理由を報告する

7. 最新main取込み後は、固定版Godot 4.7.2-stableで先にimportを実行する。`docs/region2-village-backdrops.md`の現行コマンドを読み、次を対象の提出差分で実行する。実在しない過去の専用負例コマンドを推測して実行済みと書かない

   - `python -B tools/build_region2_village_backdrops.py`
   - `python -B tools/check_region2_village_backdrops.py`
   - `python -B tools/check_region2_village_scope.py`（旧固定基準の検査を維持。これだけを004の差分検査の代用にしない）
   - `godot --headless --editor --import --quit`
   - `godot --headless --path . --script res://tools/check_region2_village_backdrops.gd`
   - 同じGodot検査の`--capture`によるWindows/OpenGLの最新実描画25枚。現在の実行引数は技術文書に従う
   - `python -B tools/check_region2_village_native.py`
   - 原画由来色・既存80色不変の専用検証と負例11件以上の実再検証
   - `python tools/validate_assets.py --strict`
   - `python tools/check_frozen_files.py`
   - `python tools/run_locked_checks.py`

   2つの独立した一時出力先への再生成を全バイト照合する。実表示のGPU丸め許容差1は元のまま、原画変換の全画素照合は許容差0を維持する。既存の回数・アサーション・入力・時間上限を変えない。生成で変わった追跡証拠は、本件担当パス以外へ混ぜない

8. 原画、main版、今回版、目標、実描画を識別できる比較を5箇所まとめて用意する。原画・目標は参照のみ。初の見た目採否は区切り末の1回へまとめ、「検査成功」と「見た目採用済み」を分ける。通常の進捗文には未体験の物語・場面を載せず、比較画像は依頼者の採否用として一括提示する

9. 許可した差分だけを通常commit・pushし、対象SHAのCI全ジョブを確認する。main統合はCI全ジョブ成功、R-01〜R-08成功、`check_frozen_files.py`成功、検査の弱体化・省略・時間延長なし、依頼範囲内という5条件をすべて満たしたときだけ行う。統合後mainのCIも確認する。状態は「報告済み」までとし、指揮役が実物を確認するまで「確認済み」にしない。見た目採否待ちは明示して残す

## 守ること

- 35件という件数や再開許可を、未確認のファイル・未採用の色・検査緩和の承認に広げない
- mainの先頭80色不変を実ファイルで確認する。末尾追加のために既存行・ヘッダー・改行を再整形しない
- 村以外の再生成、原画変更、原画の差替え、画像生成、新規人物、台詞、商品、施設機能、解放場面、遺跡に進まない
- 既存の導入・港・保存・素材・CI・保護検査を弱めない。旧固定コミットの成功と現行成果の成功を分ける
- ローカルの他作業・未追跡ファイルを消さない。必要なmain取込みが範囲外差分を生む場合は、その差分を報告する
- 素材や確認画像の外部公開・ホスティング・ブラウザ版作成はしない

## 作業の前にしてほしいこと（計画）

報告書の冒頭に、実行PCとリポジトリ、開始SHA、001〜003の状態、35件の実照合と保全結果、担当パスとの照合、未許可パス、main取込み方法、色の出典確認、実行する検査を短く書く。パス未確定の候補をこちらの推測で既存ファイルとして記載しない。

## 作業の後にしてほしいこと（自己点検）

1. 停止時の全成果を退避し、変更前の全パスとSHA・差分・未追跡実体を照合できる
2. 原画5点と既存パレット先頭80色が全バイト不変。追加色は最大4色で、実在画素の証拠がある
3. 対象10素材だけが色調整され、通行・寸法・入口・上層形状・本番接続に差分がない
4. 独立2回再生成が全バイト一致し、原画照合・負例・実描画25枚・素材strictが成功している
5. R-01〜R-08・保護ファイル・提出SHAのCI全ジョブが成功し、検査の弱化・省略・時間延長がない
6. `git diff --name-only`と`git diff --stat`の全件が004の許可パスと一致し、他作業をstage／commit／pushしていない
7. 見た目採否・歩きやすさ・施設や村の完成を、機械検証の成功から推定していない

## 報告

`docs/tasks/reports/004-resume-village-colors.md`へ次を記録する。

- 変更ファイル一覧、開始／提出／統合SHA、開始前後の未コミット・未push状態
- 停止成果の保全先と全35件の照合結果。範囲外候補は実パスと理由
- 追加した色、RGB、採取原画・座標・SHA、追加理由、既存80色と対象外素材の不変証拠
- 実行したコマンド・終了値、負例の中身と結果、最新25枚の実描画・5つの比較の所在
- R-01〜R-08、保護照合、CIの対象SHA・URL・全ジョブ結果。未実行・失敗・未評価は別記
- 自己点検1〜7、未達、指揮役の判断が必要な点（最大3件）

通常の完了メッセージは、色調整の結果、PCでの実行、検査結果、画像採否待ちだけを短く伝える。

## 完了の条件

- 元の停止成果が失われず、許可範囲の色調整と出典・再生成・最新実描画の証拠がリポジトリに登録されている
- 必須検査と対象SHAのCI全ジョブが成功し、main統合は上記5条件の成立時だけ行われる
- 報告書があり004は「報告済み」。指揮役の実物確認と、依頼者の初の見た目採否はそれぞれ独立して残す
- 村機能・新住人・商品・解放・遺跡の実装へ進んでいない


