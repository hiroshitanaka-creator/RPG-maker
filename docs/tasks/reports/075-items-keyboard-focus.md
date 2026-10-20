# 075 どうぐメニューの無効項目とキーボード操作・報告

- 検証日：2026-10-19 UTC（2026-10-20 JST）
- 基点main：`8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`
- 正式依頼HEAD：`786f5532c3ec5c6ef573f9b17769bc917319066a`
- ブランチ：`codex/task-075-items-keyboard-focus`
- ローカル修正・検証・原資料引渡し。GitHub正式保存・全CI・統合は親の実施対象であり、まだ完了とはしない。

## 再現と変更

通常の「新しくはじめる」→Escape→Enterでどうぐを開き、Down→Enterを送ると、満HPのカイナへ選択枠が移り、決定が無反応になる実害を変更前に確認した。通常到達の再現は状態注入なし。実画面で灰色文字の無効項目を白い選択枠が囲むことを確認した。

別に3人/4人・正順/逆順の診断状態をGameSessionへ注入し、満HP・負傷・戦闘不能を混在させた。同じ通常メニュー操作で無効な先頭へ移り、負傷者へ薬を使用できないことを確認した。診断注入を通常プレイでの到達証明とは扱わない。

`first_region_screen.gd` の `_button` に次の1行だけを追加した。

```gdscript
if screen_mode=="items" and not enabled:button.focus_mode=Control.FOCUS_NONE
```

itemsの既存disabled条件に従う。使用可否、薬効果、所持数、死亡条件、保存、初期focus処理は変更しない。074のtravel変更は混ぜていない。正式依頼HEADと基点mainの差分は075依頼書だけであり、今回のUI差分は上記1行のみ。

変更予定/実変更は次の3件だけ。

- `scripts/ui/first_region_screen.gd`：上記1行。
- `docs/tasks/075-items-keyboard-focus.md`：状態行のみ「報告済み」。
- `docs/tasks/reports/075-items-keyboard-focus.md`：本報告。

## 比較結果と境界

変更前と変更後に同一の `items_probe-v1.gd` 入力を使用した。通常ニューゲーム1件と診断4件の計5件、44判定で変更前は10失敗、変更後は0失敗。変更後の通常経路ではDownで「戻る」へ移り、Enterで戻れる。診断ではDownが満HPを飛ばして負傷者へ移り、Enterで薬を消費・回復する。原PNGは加工せず保存した。

境界は3人/4人×正順/逆順×地図0/1×薬0/1/3×HP構成4種＝96ケース。HP構成は混在（満HP・30負傷・死亡、4人目も負傷）、全員満HP、全員死亡、1人HP1。各条件で全方向・Tab、無効人物クリック、未所持地図クリック、地図往復、戻る・再表示・Escape、マウス再表示/戻るを検査した。有効時には薬使用・再生成を確認し、残数とHPが許す場合はマウスで続けて使用した。

- 3人正順：24ケース、1092判定、失敗0。
- 3人逆順：24ケース、1093判定、失敗0（実描画保存1件を含む）。
- 4人正順・検査移動補正後：24ケース、1236判定、失敗0。
- 4人逆順：24ケース、1236判定、失敗0。
- 地図なし/薬0・1の実描画境界：8ケース、394判定、失敗0。全員不可と使用後の「戻る」選択、文字・選択枠をPNGで確認。

期待状態は使用直前の全状態を複製し、対象HPを `min(max_hp, hp+50)`、薬個数だけを1減らした独立期待値。状態全体を比較するためMP・金・他の仲間・フラグ・位置・保存対象の意図しない変更も検出する。入力移動・取消・地図・無効クリックでは全状態不変を照合した。focus強制やButton.pressed直接呼出しはハーネスに含まない。

初回4人正順は、ハーネスが下方向の循環を仮定したため対象へ届かず、その後の連鎖を含む176判定が失敗した。下方向だけで末尾から先頭へ移れない実際の入力挙動を確認し、上下方向で対象を探すよう診断側の移動だけを修正した。ゲーム側の変更・期待値・時間上限は増減していない。失敗した原ログ、結果JSON、初回ハーネスを保持し、同じ24条件を再実行して成功した。

## 既存検証

固定エンジン `4.7.2.stable.official.ed1daf0bf` を使用。配布archive SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、binary SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。archive内binaryと実行binaryのbytes一致を確認。

checkout外の固定HEADコピーで実行。既存検査器・test・保護・素材のbytesを固定HEADのmanifestと照合。元checkoutの検査器・CI・原画・registry・project.godotを変更しない。

| コマンド | 結果 |
|---|---|
| `timeout 600 godot --headless --editor --import --quit` | 変更前60.61秒、変更後5.42秒、各exit 0 |
| `timeout 600 godot --headless --import` | 5.84秒、exit 0 |
| `python3 tools/validate_assets.py --strict` | 14.27秒、exit 0。画像1154・音15・字体2・パレット3、問題なし |
| `python3 tools/check_frozen_files.py` | exit 0、保護26件全一致 |
| `python3 tools/run_locked_checks.py` | 152.31秒、exit 0。各verify既存300秒上限のままR-01〜R-08全PASS |
| `timeout 180 godot --headless --path . --script res://tools/check_first_region_screen.gd` | 5.21秒、exit 0、REGION_UI_PASS checks=10 |

R-07はA01〜A14と成功マーカー、R-08は25 tests・3046 assertions・failed/pending 0を確認。原ログを全件保持し、SCRIPT ERROR・Parse Error・ERROR・WARNING・リークを監査した。headlessの成功検査には該当エラー/警告なし。

実描画4実行にはX11/MesaのV-Sync非対応警告 `Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver.` が各1件ある。抑制せず原文を保存。Xorg起動時の非rootソケットディレクトリ作成警告も `logs/xorg.log` に保持し、その後の描画・画像保存は成功。警告ゼロの実描画環境とは報告しない。

## 契約・スキル・境界

AGENTS.md、.scope-lock/spec.lock.json、docs/tasks/README.md、素材規約、既存どうぐ使用コードと地方実装記録を確認。`godot`、`godot-game-verification`、`godot-dev-director` はローカルskill配置と今回取得できたクラウド250件・executor0件に存在せず、導入していない。利用済みとはしない。Library保存には現在のLibraryスキルを使用する。

AGENTSの通常のcommit/push・repo内画像保存規則に対し、今回の明示依頼に従い親による正式保存とcheckout外証拠を採用した。docs/decision-log.mdとdocs/tasks/README.mdへの追記も親担当として行わない。066・074作業・main・remote push/PR/merge・local PC操作は実施していない。074の未統合差分は本提出に含まない。

## 引渡し・未検証

証拠ルート `/workspace/task075-items-focus-evidence/`。`payload/` に3件の全文、`originals/` に基点の原bytes、`changes.patch` に適用検証済み差分。`logs/`、`locked-logs/`、原PNG・全状態/入力/結果JSON、`formal-head-files.json`、`audit.json`、`manifest.json`、固定Godot照合を配布ZIPへ収録する。ZIP全件のbytes・CRC・SHA256を照合し、ZIP外の保存記録にLibrary IDと確認サイズを返す。ローカル環境変数・キャッシュ・一時Git index・Library転送用情報は配布しない。

復旧は1行追加を削除し、依頼状態を戻し、本報告を取り除けば基点の3パスへ戻せる。提出patchは固定HEADへ適用し、全3パスのbytes一致まで検証する。

未検証は親による正式commit後のGitHub全CIと統合、および実機での人間操作。今回のローカル検査成功で代用しない。
