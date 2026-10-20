# 078 main統合・再検証報告

日付：2026-10-20 UTC。未commitの通常merge候補と原証拠の引渡し。正式保存・push・PR・main反映・全GitHub CIは親担当。

## 固定対象と統合内容

- 第1親：`50717552bd29088a7ea9fe5c162252b16efc0b03`（tree `3dd7537717c6470beb6944464f63b6d6552ef987`）。
- 第2親（指定main）：`f34967aadf3f668017854d1c958f3ee075d4097f`。
- 共通基点：`8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`。
- 原078完成HEAD：`7be406d53a34ff71f26f9f37a06e247b3cabd16f`。
- 検査したコードtree：`7ad6bdd8eb97ac0e021b2d874df39b8623beb8d8`。最終報告追加後の引渡しtreeはZIP内candidate.jsonに記録する。treeはcommitではない。

`git merge --no-commit --no-ff`で取り込み、競合したのは親担当台帳2件だけ。競合原文を保存し、第1親の原bytesをそのまま採用した。`docs/decision-log.md`のblobは`54a73490b43a6cbfe771f879145d3bc181845e3b`、`docs/tasks/README.md`は`3705a756651e5cc13f8839dc9d896c0a624aead0`。第2親の台帳全bytesが第1親の先頭に保持されることも照合した。原078依頼・原報告は第1親と同一。

UIは自動統合された。game_root.gdから076のfollow_focusと077の無効装着focusの2行を除くと第1親に完全一致する。078の転職初期/候補変更/清めるのfocus同期3行を除き、移動した閉じ括弧を戻すと第2親に完全一致する。first_region_screen.gdは第2親と完全一致し074/075を保持する。職・清めるの既存disabled式、初期と候補変更時の式の差、選択肢・状態変化の規則を変更していない。

第1親からの差分は以下14件。13件は上流取り込み、今回新たに執筆したrepoファイルは本報告だけ。

- `docs/tasks/074-return-menu-keyboard-focus.md`
- `docs/tasks/075-items-keyboard-focus.md`
- `docs/tasks/076-party-focus-scroll.md`
- `docs/tasks/077-party-disabled-focus.md`
- `docs/tasks/reports/074-return-menu-keyboard-focus.md`
- `docs/tasks/reports/075-items-keyboard-focus.md`
- `docs/tasks/reports/075-main-integration.md`
- `docs/tasks/reports/076-main-integration.md`
- `docs/tasks/reports/076-party-focus-scroll.md`
- `docs/tasks/reports/077-main-integration.md`
- `docs/tasks/reports/077-party-disabled-focus.md`
- `scripts/ui/first_region_screen.gd`
- `scripts/ui/game_root.gd`
- `docs/tasks/reports/078-main-integration.md`

保護/test/既存検査器/CI/assets/registry/project.godot/066/物語・規則は変更していない。元078作業領域のHEAD・status・全7723ファイルと、既存ZIP 10件をハッシュで保存・照合する。

## 実行環境・Git参照

作業領域`/tmp/task-078-main-integration`、証拠`/tmp/task078-main-integration-evidence`。同じ実行環境の/tmpを使用した。別PC・新環境への切替なし。候補検査用コピー7734件、共通基点7721件の全source blob/mode/SHAを実行前に照合。独立indexを持つコピーで検査し、生成されたdocs/verificationだけを実行後の例外として列挙する。

固定Godot `4.7.2.stable.official.ed1daf0bf`。archive SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、binary SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。実バイトを照合し、統合後最初のGodot実行をeditor importとした。その他の起動時刻がその終了後であることも監査する。

source監査はgit_source.pyで全継承GIT_*を除去し、--git-dir/--work-treeを明示する。検査用GIT環境を意図的に与えるpreflightを先に実施し、sourceのHEAD/MERGE_HEAD/index/treeが対象通りであることを確認した。パッチ検証には独立indexだけを明示する。日本語ファイル名はNUL区切りで列挙。今回の監査を077の結果で代用していない。

11:37 UTCの切断通知後、11:38:31 UTCに同環境を実測確認した。source・原証拠へアクセスでき、親2件とtreeは一致。editor importは11:38:11 UTCに86.018秒・exit0で既に終了していた。再実行や重複環境作成はしていない。内部接続障害の原因は不明で、復旧原因を推測しない。記録はenvironment-check-1137.json。11:55 UTCの再通知後も11:57:56 UTCに同環境を実測し、親/tree一致と原証拠へのアクセス、4人逆順・未解放検査exit0を確認した。検証を妨げる障害は観測せず、通知の内部原因は不明のまま記録した（environment-check-1155.json）。

## ハーネスの世代対応

原078 reproduction.gdと最終boundary.gdを全文保存し、今回版との差分を同梱した。差分の逆適用が原本bytesに一致することを検査した。単独078の「076未統合でfollow_focus=false」「077未統合でequip.focus_mode=ALL」という2条件だけを、今回承認済み統合の「follow_focus=true」「equip.disabledならNONE/有効ならALL」に対応付けた。原assertは原本側に残し、対応表assertion-transition.jsonに記録。その他の入力列・独立期待状態・078継続assertは保持した。

同じTab入力後に076の焦点全体可視、077の無効装着非選択を追加観測。通常再現にも撮影用wheel前の可視性/無効装着非選択を追加した。reproductionの原30判定に8観測を追加し38判定0失敗。原078との43イベントのcase/key/Shift/wheel列は完全一致する。統合後の焦点対象やEnter結果が原078と同じとは仮定しない。

078の43診断ケース（主32・追加8・祠3）と、選択12ケースの実描画を再実行した。3/4人・仲間正逆順・解放/未解放・侵蝕10/不可逆90・祠内外・侵蝕0・魔物化89を含む。全ケースでTab/ShiftTab双方を巡回する。正規import_stateによる診断初期化であり、通常プレイ到達とは区別する。ケース初期JSONを保存し、有効操作結果の注入はしていない。

職候補の有効↔無効往復、OptionButton/PopupMenu説明、取消、仲間切替、再生成、戻る、無効マウス操作を元のassertで検査。有効転職は既存即時確定（新確認画面なし）、清めるは既存確認・取消・確定をキー/マウスで実行。固定独立期待は転職のHP140→125/70→62、清めるの侵蝕10→0/89→59・専用技消去/共有技とマスター保持、魔物解除HP157→143/78→71・MP30→24/15→12を含む全状態比較。結果40操作のexpected_stateとafter_stateが一致した。

55ケース出現（43診断と描画反復12）の9353件の編成Tabイベントを独立集計。全ケースの両方向で焦点移動とスクロール移動が実際にあり、移動後の焦点全体可視・無効装着/転職/清めるの非選択を確認した。撮影用wheelは元のハーネスのまま残し、その画像だけを追従証明にはしない。

076通常操作52判定、074/075の道具・転移・相互遷移も現候補で再実行。全カスタム24実行、39139判定0失敗。原PNG 257枚を保存。下表は通常操作・診断・反復を混在させたケース合計ではなく実行別の件数。

| 実行 | ケース | 判定 | 失敗 | 秒 | PNG |
| --- | ---: | ---: | ---: | ---: | ---: |
| actions-3-forward-locked | 4 | 2645 | 0 | 51.89 | 0 |
| actions-3-forward-open | 4 | 2667 | 0 | 55.26 | 0 |
| actions-3-forward-render | 4 | 2683 | 0 | 63.81 | 16 |
| actions-3-reverse-locked | 4 | 2649 | 0 | 51.98 | 0 |
| actions-3-reverse-open | 4 | 2673 | 0 | 58.65 | 0 |
| actions-4-forward-locked | 4 | 2645 | 0 | 54.26 | 0 |
| actions-4-forward-open | 4 | 2667 | 0 | 66.74 | 0 |
| actions-4-reverse-locked | 4 | 2649 | 0 | 50.64 | 0 |
| actions-4-reverse-open | 4 | 2673 | 0 | 57.75 | 0 |
| actions-4-reverse-render | 4 | 2685 | 0 | 83.95 | 12 |
| actions-extra-3-forward | 2 | 1322 | 0 | 30.33 | 0 |
| actions-extra-3-forward-render | 2 | 1330 | 0 | 49.86 | 8 |
| actions-extra-3-reverse | 2 | 1327 | 0 | 29.70 | 0 |
| actions-extra-4-forward | 2 | 1322 | 0 | 33.39 | 0 |
| actions-extra-4-reverse | 2 | 1327 | 0 | 30.15 | 0 |
| actions-extra-4-reverse-render | 2 | 1332 | 0 | 47.55 | 5 |
| actions-locations-3-forward | 3 | 2019 | 0 | 53.38 | 0 |
| actions-reproduction-render | 4 | 38 | 0 | 37.92 | 12 |
| combined-3-render | 8 | 668 | 0 | 49.46 | 46 |
| combined-4-render | 8 | 722 | 0 | 51.39 | 46 |
| follow-normal-render | 1 | 52 | 0 | 47.18 | 17 |
| items-boundaries-render | 8 | 394 | 0 | 42.77 | 16 |
| items-normal-render | 5 | 44 | 0 | 27.98 | 15 |
| travel-render | 16 | 606 | 0 | 70.89 | 64 |

## 既存検査

既存コマンド・検査器・時間上限を保持。R-01〜R-08は全PASS。各生ログも収録する。ローカル検査をGitHub CI成功とは扱わない。

| 実行 | コマンド | exit | 秒 |
| --- | --- | ---: | ---: |
| editor-import | `timeout 600 /workspace/RPG-maker/.tools/godot/4.7.2/godot --headless --editor --import --quit` | 0 | 86.02 |
| headless-import | `timeout 600 godot --headless --import` | 0 | 20.26 |
| assets-strict | `python3 tools/validate_assets.py --strict` | 0 | 24.33 |
| frozen | `python3 tools/check_frozen_files.py` | 0 | 0.08 |
| locked | `python3 tools/run_locked_checks.py` | 0 | 213.16 |
| first-region-screen | `timeout 180 godot --headless --path . --script res://tools/check_first_region_screen.gd` | 0 | 8.18 |
| second-region-coast | `timeout 180 godot --headless --path . --script res://tools/check_second_region_coast.gd` | 0 | 5.64 |
| region2-port | `timeout 180 godot --headless --path . --script res://tools/check_region2_port.gd` | 0 | 6.99 |
| village-regression | `timeout 180 godot --headless --path . --script res://tools/check_region2_village_regression.gd` | 0 | 31.82 |
| saved-position | `timeout 120 godot --headless --path . --script res://tools/check_saved_position_relocation.gd` | 0 | 6.30 |
| integrated-ui | `timeout 240 godot --headless --path . --script res://tools/check_integrated_ui.gd` | 0 | 9.64 |
| coastal-legacy | `timeout 180 godot --headless --path . --script res://tools/check_coastal_travel.gd` | 124 | 180.05 |
| baseline-editor-import | `timeout 600 /workspace/RPG-maker/.tools/godot/4.7.2/godot --headless --editor --import --quit` | 0 | 130.17 |
| baseline-coastal-legacy | `timeout 180 godot --headless --path . --script res://tools/check_coastal_travel.gd` | 124 | 180.07 |

旧check_coastal_travel.gdは候補・共通基点とも`return_learned`参照のSCRIPT ERROR（34行）後、既存180秒でexit124。両stdoutはバイト一致する。この失敗は保持し、全検査成功とは書かない。今回範囲外の旧検査を変更していない。

X11実描画にはV-Sync変更非対応のWARNINGがある。Xorg側の通知も生ログのまま保持。エラー・警告・リークはaudit.jsonに別集計し、無視/消去して成功化しない。

## 実画像・証拠・残件

view_imageで10枚の未加工原PNGを実表示し、通常再現のwheel前焦点、逆Tab後の無効装着除外、通常Tab06の下部追従、転職説明/有効ボタン、清める確認/再表示、074/075の有効対象と全員無効時の戻るを確認した。各ファイルのSHA/dimensions/所見はvisual-verification.json。全PNGを目視したとは扱わない。物理コントローラー・仮想joypad・利用者PC・初見操作感は未検証。

各実行は専用ディレクトリを排他作成し既存成果への上書きを拒否する。stdoutとartifactsがその実行の一次証拠。generatedは実行終了時に更新ファイルを収集したsnapshotで、並行した既存検査由来の更新が入る可能性があり、排他的な生成者証明には使用しない。.import/runtime/cacheは配布から除外。save prefixはrun起動値とハーネス内PID値を区別する。

from-branch.patch / from-main.patch / from-common-base.patchを各固定treeの独立indexへ適用し、同一引渡しtreeへ一致することを監査する。14payload全文・両親原文・競合原文・原ハーネス/差分・全原ログ/JSON/PNG・manifestをtask-078-main-integration.zipへ格納。全ZIP項目のCRC・bytes・SHA256を検査し、候補tree・manifest・監査を引渡す。新commit、push、PR変更、main mergeは実行しない。

AGENTS/素材規約/企画・体験仕様/台帳/契約は既読版とbytes一致を確認。storyteller skillはゲーム実装対象外、指定Godot skillは配置なし。今回の明示的な未commit・親台帳保持・外部証拠指示を一般規定に優先した。

Libraryのcurrent skill/helper取得は`skill package is not available`を返した。原因不明として原文をlibrary-availability.jsonへ保存し、旧helperは流用していない。保存用connectorは公開されているため、その現在の呼出仕様で保存を試み、confirmed ID/bytesと元ZIP SHA256は保存結果を確認して最終引渡しに記す。保存失敗時は原文と元ZIP SHAを引渡し、成功とは扱わない。

残件は親の検収・正式保存・全GitHub CI・統合反映、既存coastal検査の失敗、実機/物理入力と人間評価。範囲内の追加承認待ちはない。
