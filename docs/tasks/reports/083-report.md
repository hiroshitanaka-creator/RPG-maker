# 083 採用済み静止人物のS10画面統合

基点main：`a4dc7c9d0d705f3181391fdccee4e4c825ddcaaf`。開始時のorigin/mainと一致。082は再実装しない。
本番実装固定SHA：`6e2567638416a86c0b0b94c5300f95f8ac4c4a9f`。既存撮影の座標対応を含む回帰基準SHA：`611c5986f3d960d3c306c48d971833de7f5a9523`。本番コードの追加変更なし。
ブランチ：`codex/task-083-s10-static-placement-20261028`。この実装コミットの通常pushは成功し、ls-remoteで同SHAを読戻した。mainへの書込み・マージなし。

## 採用根拠と変更

I-20261028-008、質問Sentinel_f02fdc7cda008191ae47fea143effba8への本人回答B（2026-10-28T05:35:56.315527+00:00、Sentinel_449ed1f483d48191b0bcfcfd48dd4dd8）に基づく。正式依頼書は `docs/tasks/083-s10-static-placement.md` に固定GitHub正本の写しを保存した。

- `world/region2_village.json`：room4 [8,6]へ `kind:npc / display_only:true / static_sprite` の1件だけを追加。既存npc占有で通行を止める。新会話・巡回・人物設定なし。
- `scripts/world/first_region_view.gd`：static_spriteだけを既存 `_object` の32×48で描く。bottom=y+1、overlay bottom_row-0.5を保持。歩行人物・長老の描画は既存経路。
- `scripts/game/game_session.gd`：display_onlyを `face_event` と本文分岐より前で除外し、向き保存・新会話・082再演を発生させない。
- `assets/characters/ner/event_standing.png`、`assets/registry.json`、`assets/source_records/s10-ner-static.json`：採用PNGを同bytesで1×1のcharacter_eventとして登録。原画の固定path/SHAと本人採用根拠・変換処理を記録。
- `tools/validate_assets.py`：owner原画の既存許可一覧へchibi固定path/SHAの1件のみ追加。拒否条件の変更なし。
- `tools/import_s10_ner_static.py`：原画を読取専用で再現。周縁連結の薄灰色マスク、最近傍、既存自然色16色の減色を採用時と同じ順序・式で処理し、採用SHA不一致なら保存せず停止する。
- `tools/check_s10_static_display.py`、`tools/check_s10_static_display.gd` とUID、`tools/capture_s10_static_display.gd` とUID：素材の正負例、占有/到達/保存/操作の正負例、本番UI実撮影と非遮蔽全画素の照合。
- `tools/preview_s10_placement.py` と `docs/verification/s10-placement-preview/` の7件：参照commit `d46151a633a2b5701bf0c583bf01344f39095929` の8ファイルを同bytesで保存。当時の「未採用・未接続」の表記は歴史資料として保持し、今回の採用と実接続を本報告で示す。
- `tools/capture_task009_village_regression.gd`：後述の旧描画CI失敗を受け、room4の全画素可視の撮影入力だけ[8,5]から隣の[7,5]へ対応。全assertion・閾値・終了判定・180秒上限は不変。保護対象外であり、AGENTS.mdの「検査の座標を新しい配置に合わせる」既存許可に従う。
- 本依頼書・本報告・`docs/verification/task-083/`：原ログ・実行記録・検査結果・実画面・比較・hash目録・独立レビュー・PR拒否記録。

変更全pathは `docs/verification/task-083/changed-paths.txt` と `manifest.json` に保存する。親担当 `docs/tasks/README.md` と `docs/decision-log.md` は変更しない。

採用画像SHA256：`121010a316a31b88dca753ed48bc9404f176a4fe5f0d6dd5508ebf0615559f5d`（2032 bytes、32×48、16色以内、二値alpha、足元47）。
chibi原画SHA256：`7fb285a7c31839ff33350c328f39dfd97e94ea57a0fe6567ef862f8fb19a9aa5`（1152×1728）。concept原画と共に基点の全bytesを保持。新色・反転・ポーズ・歩行コマの複製なし。再現出力と本番PNGは採用PNGの全bytes一致。

## 先行の失敗と実描画

`runtime-red.log` は配置前の占有/保存補正の失敗13件を保持。`display-only-red.log` は配置だけを追加し、除外前の決定で向きが保存され本文参照エラーになる失敗18件を保持する。face_event前の除外後は新規集中77条件全件成功。南/西/東/北からの決定反復、通常移動のすり抜け拒否、入口/出口/長老への迂回と既存台詞、未完了/完了の占有位置保存補正と全状態不変・再保存・再入室を確認した。

`asset-red.log` の最初の素材検査には検査入力の誤った寸法/原画名とPillow非推奨警告が含まれる。原画の現物寸法と固定パスを確認して検査入力を訂正し、`asset-red-corrected-fixture.log` で未実装3条件の失敗を確認した。素材の正負例は最終36条件成功。誤path・未採用concept・固定pathで改変された原画SHA・PNG改変・寸法・色数・パレット・半透明・接地の負例を含む。本番原画を変更せず一時rootで拒否を確認する。

初回GL撮影 `capture-first.log` はV-Sync警告、会話窓に完全に隠れる主人公、出口遷移後のセルを検査側が誤判定した4件の失敗を保持する。検査入力/期待値を既存UIと既存扉へ合わせ、本番設定は変更していない。以降はCLIでForward Mobile/Vulkanを選び、workspace内に展開したXvfb/Mesaで警告・エラーなしに撮影した。出所・パッケージhash・エンジンhashは `environment.json`。上限180秒は維持。

実Godotの512×288画面9枚：`entry-dialogue.png`、`conversation.png`、`interrupted-resume.png`、`completed.png`、`player-front.png`、`player-behind.png`、`reentry.png`、`old-save-relocated.png`、`overlay-behind.png`。118条件成功。採用人物・長老・主人公の非遮蔽全画素を許容差1以内で照合し、人物の前後関係と既存上層の部分遮蔽を確認。採用人物は画面境界や会話窓に欠落しない。会話中の入口に立つ主人公は既存会話窓に隠れるため、その既存挙動と採用人物の可視性を区別した。

`review-board.png` はBの歴史的静的案・実Godot・既存目標の比較。実画面は人工境界保存から本番入力を実行した検証記録であり、本人の初見プレイ記録ではない。原画の瞳・顔の細線は32×48では同じ精細さで読めない。採用bytesを変更して補正していない。独立レビューは重大・重要な指摘なし（`review.json`）。

## 固定SHAの回帰とCI

最初の実装SHAの別checkout `/workspace/task083-verification`、および撮影座標対応後の旧撮影座標修正の固定SHA `611c5986f3d960d3c306c48d971833de7f5a9523` の別checkout `/workspace/task083-final-verification` の両方で24コマンドを実行し、いずれも全件終了0・警告/エラーなし・PASS。最終記録 `final-corrected/commands.json`（初回は `final-validation/commands.json`） にコマンド・環境・開始/終了・元上限・終了値・原ログhashを保存し、`checks.json` に結果を記録した。R-01〜R-08は原verify/原 `run_locked_checks.judge_output` の判定をそのまま使用し全件PASS。保護対象26件は前後とも26件一致。素材strict・新規36/77/118条件・再現全bytes一致・082本文9ページ/13負例・082実行時293条件・既存導入/通常画面/戦闘復帰/保存型/位置補正/081継続APIが全件成功。既存検査が出力した082等の証拠は別checkoutで受け、`runtime-records.tar.gz` に保存した。作業ブランチの082原記録は変更しない。

段階限定の081検査は当時固定完成SHA `7d85b1100b7d8bea9cdffdad67c4ece72c739bbf` で別実行し原1235条件全件成功（`historical-stage-081.json` / `historical-081.log.gz`）。継続1190条件も成功し、`continuity-checks.json` に対応付けた。新規出所許可1件以外の検査関数AST・既存全素材の出所判定を083基点と照合する。検査・assertion・基点・上限を変更せず、歴史的な「追加は当時1件だけ」という条件を最新treeへ流用しない。

旧撮影座標修正の固定SHA `611c5986f3d960d3c306c48d971833de7f5a9523` のGitHub CIは、push起動の全5ワークフロー・38ジョブがcompleted/success。`github-corrected-final.json` に各ID/URL/開始/終了/結論を保存した。CLIのAPI読取りはHTTP Forbidden、PR専用取得APIはpush実行を返さなかったため、その空結果を成功や未実行と扱わない。CI設定や検査の変更はない。この後の証拠保存コミットに対するCIもGitHub側で全件終了を再照合する。


最初のGitHub CIは38件中36成功・2失敗。旧村journey撮影の `05-room-4-front` と、それを正例として再利用するlifecycle-auditの `counter-back-capture` がFAIL（`github-initial-final.json`、`ci-journey-red.log`、`ci-lifecycle-red.log`）。入力点[8,5]の主人公に新人物[8,6]が正常に重なり、既存検査の「人物全画素が可視」という前提が成立しなくなった（`ci-journey-red.log`、job 122657259093）。全画素可視検査点だけを隣[7,5]へ移し、旧[8,5]は083新規撮影のplayer-behindで正常な人物遮蔽と非遮蔽全画素を確認する対応にした。固定世代009の当時コード・座標・全assertionは変更しない。追加レビューでも検査弱化・保護対象変更の具体的懸念なし。修正後SHAの同検査器で、準備の7624条件・5室の別プロセス再起動（10/27/38/52/44条件）が全件成功。journey実撮影は132条件・28枚・124.984秒で終了0、errors=[]、元上限180秒以内でPASS（`journey-corrected/commands.json` と原ログ/全出力archive）。


### 全assertionの対応と入力経路

`assertion-migration.md` / `assertion-migration.json` は083基点の旧撮影補助の全48 `castle_check` 呼出しについて元行・最新行・全式・実行モード・固定版/最新版/後続検査の対応を列挙する。全式・順序は同一。コメントとroom4撮影入力1値以外のコードも同一で、継承元・既存009/016対応表・判定器の全bytesは基点不変。固定実描画は006完成 `5f1c2ba231191b25b9b32a814b616a9f8d0a54ce` の当時の `capture_region2_village_connections.gd` を全7撮影モードで実行する。009完成 `ce07fdada0466138260ab678c10fd78e61c0c63d` は別のscope/lifecycle対応監査であり、固定7モードの実行SHAとは区別する。083基点の48式は最新側で同一のまま維持する。最新journeyの132条件を固定版の件数へ置き換えたり、元のassertionを削ったものではない。

旧 `journey` と故障注入の `counter-back-capture` は、継承元の `_walk → _step_direction → _key → Viewport.push_input` による通常キー経路である。CLI `python tools/test_task009_lifecycle.py --fixed-path ../fixed --godot ../godot` が最新611c598の別コピーで正例132条件/28枚/終了0を確認した。`ci-lifecycle-green-611c598.log` に原ログ、`counter-back-negative-proof-611c598.json` に正負の結果を保存。占有無視・拒否時の状態破損・客側閉塞・出口閉塞・誤接続・不正保存受理は各々終了1/runtime FAIL、parser errorなし、timeoutなしで正しく失敗し、外側の負例判定はPASSである。正例をtimeoutやparse errorで失敗させて負例成功にはしていない。

新規 `capture_s10_static_display.gd` のAPI入力と、この通常キー経路を同じとは断定しない。元のAPI入力撮影118条件を全件そのまま残し、実方向キーで[8,5]↔[8,7]を迂回往復する追加ケースと `normal-keys-behind.png` を設けた。最終のローカル実Godot撮影は141条件・10枚・終了0、警告/エラーなし。元API撮影9枚に実キー用 `normal-keys-behind.png` を追加した。実コマンド・環境・180秒上限・開始/終了・実終了値・原ログhashは `normal-keys-verification.json`。元118条件が新141条件の順序付き完全一致部分列で残ることも機械照合した（`normal-keys-verification.json`、script SHA固定）。実キーの[8,5]における人物遮蔽も全非遮蔽画素で確認する。これは旧counter-backシナリオの代替ではなく、旧CIの通常キー検証に追加する別のS10検査である。

**新規S10のPython/GDScript集中検査と撮影はCI未接続。** 本依頼で明示したローカル実行の証拠を使い、毎回のpush/PR CIで実行されるとは記載しない。最終証拠保存HEADでは本番・旧撮影補助は611c598と同bytes、新S10撮影scriptは上記141条件を実行したSHAと同bytesであり、GitHubの全38既存ジョブを最新HEADで別に再照合する。

## PR作成のブロック

2026-10-28 05:52台UTC、同ブランチから `hiroshitanaka-creator/RPG-maker` のmainへのdraft PR作成をGitHub連携APIで1回実行し、自動承認レビューに拒否された。理由は「この083のPR/作成先について信頼できる本人承認を確認できない。外部リポジトリへのコミットメントと実装/証拠の共有に当たる」。本実行依頼に作成指示があることと、レビューがそれを信頼できる承認として認識しなかった結果を区別する。

拒否後の同head/all state検索はPR 0件。作成は未実行であり結果不明ではない。再試行・別経路のPR作成は行っていない。対象・理由・読取り照合・必要な次の一手を `pr-blocker.json` に保存した。新しく関連する本人根拠を拒否後に受領した場合だけ、PR未作成を再照合して同APIを1回再判定できる。実装・検証・通常push・証拠保存は独立して継続した。

## 未達・範囲

- draft PR作成は上記拒否で未達。mainマージは本依頼の範囲外で実行しない。
- 人間による手触り・本人の初見プレイは未実施。機械検証と別扱い。
- 任意4職の旧保存移行、S11、鍵、戦闘、報酬の新規則は本依頼の範囲外。全ゲーム完成とは報告しない。
- 開始時から未追跡の `scripts/game/equipment_rules.gd.uid` と `tools/check_equipment_rules.gd.uid` は083のコミット/pushへ含めない。

再現前提：浅いcheckoutでは `git fetch --no-tags origin a4dc7c9d0d705f3181391fdccee4e4c825ddcaaf d46151a633a2b5701bf0c583bf01344f39095929` を先に実行する。新規Python検査の固定参照用であり、比較対象を作業ツリーに変えない。

親記録用の技術判断：表示専用NPCを既存npc占有と既存保存補正へ接続し、会話だけface_event前で除外した。表示は既存_objectで静止1枚として扱う。理由は採用範囲を守り歩行sheet偽装と新規会話/保存形式追加を避けるため。戻す場合は実装コミットを新しい訂正コミットで差し戻せる。
