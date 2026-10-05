# 021 村のサービス検査の正常変更・状態保持

P2-1・P2-2を修正した。受付内の正常移動を最新回帰で受理し、受付台越しに届かない負例と攻略情報消失をassertionで拒否する。最終実装コードのCI全20ジョブ、R-01〜R-08、固定/最新007、保護照合は全て成功。本番・原画・画像・workflow・時間上限は不変。

## 対象と作業前確認

登録SHA `2ea69006d54ba39ae685bea7f54a17f4a73b82b3` を指定ブランチから取得した。007対象 `0a29a8ada3692d05ea4e552ad2e1233960e77830`、020報告 `79b8141ca03a3b4fe987a43192e3d28f719cd74a`、固定完成 `776ad944723d21c1e250a1ee5fd56d35da42cfed`。最終実装コミットは `1c23008360249919f730efcc7b04de5019e18e0e`。開始時の未コミット変更と登録ブランチの未push差分は0件。作業前計画は [plan.md](../../verification/task-021/plan.md)。007を差し戻しにした。追加委譲なし。

## 修正内容

P2-1：サービス検査の宿と通常操作撮影の6人は、NPCのIDから現在の床・占有・reach・入口到達を検証し、話しかけ位置と向きを選ぶ。宿は歩けない地形を挟んだ受付台越しの位置を選び、内側へ回り込む隣接会話では代用しない。撮影は既存の通常ロード・方向キー・決定キー・画面ボタンでその位置まで歩く。初期値を現在の期待値へコピーせず、回復・料金なし・拒否・状態保持は従来の独立assertionを維持する。

P2-2：侵蝕値の正境界4例と魔物化全8系統、および通常操作の祠成功前後で、overworld辞書全体の不変をassertする。従来の港祠との横比較は、`FirstRegion.place` が移動のため変えた `layer/node/room/cell` の4項目だけを比較直前にそろえる。`cleared/transport/residents/facing/entry_lock` その他すべての項目は比較に残す。全状態からoverworldを除外する処理は撤去した。

021の正負例は、既存 `check_task007.py` の固定/最新実行に続けて、一時コピーへデータまたは本番の1行変異を入れて実行する。再現用の初期位置12,3/reach2はコピーだけへ設定し、最新本番の初期セルを要求しない。受付負例は12,3/reach1に限定する。コピー内の変異だけを戻し、復帰も検査する。新規固定manifest・固定checkout・workflow・再帰監査層は追加しない。元の固定007は当時の検査器で全項目を実行する。

## 旧検査との対応表

| 旧項目 | 固定776ad944での保持 | 最新側の期待値・実行 |
| --- | --- | --- |
| 6人だけ・初期セル・専用素材・短い会話文（19件の段階限定assertion） | 当時のservices `--stage` の299件に全て保持 | ID一意・担当室/役割・会話有無の継続条件を維持。初期セル/文字列を要求しない |
| 床とNPC占有・受付reach・入口到達・正向き/逆向き・対面 | 当時のresidents全assertion | 元のresidents全assertionに加え、宿/撮影も現在ID・床・占有・reach・入口からBFSで位置選択 |
| 宿の4人HP/MP回復・料金なし・回復/対面以外全状態保持・戦闘拒否 | 当時のinn全assertion。話しかけ12,5も残る | 同じ性質を独立assertし、話しかけ位置だけ現在NPCから選択 |
| 祠の室4限定・値0/29/30/60/89/90/100・30低下・全拒否状態保持 | 当時のshrine全assertion | 全assertionを維持し、正境界成功前後のoverworld全体比較を追加。港横比較は位置4項目のみ正規化 |
| 全8系統の解除・姿/職/侵蝕・マスター成長/修練・専用技忘却/共有技保持・港一致 | 当時のforms全assertion | 全assertionを維持し、8系統成功前後のoverworld全体を追加。港横比較は同じ4項目のみ正規化 |
| 6位置の全状態保存/再開・NPC占有保存の入口補正 | 当時のsaves全assertion | 元の動的会話位置と全保存/補正assertionを維持 |
| 外観49件11枚・4室113件22枚、門/6会話/保存/祠の確認・取消・実行 | 当時の撮影器・全画像数/画素/操作assertion | 全assertionを維持。話しかけ位置をIDから選ぶ検査を6件、通常祠のoverworld比較を1件追加（外観51件・室118件） |
| 素材72コマ・原画/出所/再生成・固定差分範囲 | 当時のassets `--stage` の全検査 | 元の最新素材検査を維持。本作業で素材/画像を変更しない |
| 600秒import・180秒サービス/撮影・600歩/3000入力/300戦闘ターン | 当時の上限を保持 | 同じ上限を保持。正負例の各サービス/撮影も180秒 |

## 正負例の実測と全検査

Godotは公式4.7.2-stable、ZIPのSHA-256は `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` と一致。XDG設定/キャッシュ/保存先とX11/Vulkan環境を `/tmp` へ隔離した。成功証拠には標準4.6.3を使用しない。

| コマンド/対象 | 実測結果 |
| --- | --- |
| `godot --headless --editor --import --quit`（600秒） | 終了0、警告/エラーなし。[ログ](../../verification/task-021/local/import.log) |
| `python tools/validate_assets.py --strict` | 終了0、画像1140・音15・字体2・パレット3、問題なし |
| `python tools/run_locked_checks.py` | 終了0、R-01〜R-08全8件PASS、tests_ran=True・parser_failed=False |
| `python tools/check_frozen_files.py` | 実行前/途中/提出前とも終了0、26/26一致 |
| `python tools/check_region2_village_regression.py --godot /tmp/task021-bin/godot` | 終了0、地形/接続/保存7630件、5別プロセス再開10/27/38/52/44件、全てPASS |
| `python tools/check_task007.py --completed 776ad944723d21c1e250a1ee5fd56d35da42cfed --godot /tmp/task021-bin/godot`（af56987での作業中通し） | 固定の素材/299サービス/外観49件11枚/4室113件22枚は全成功。最新の素材/293サービス/外観51件11枚/4室118件22枚も全成功。ただし021受付負例が隣接会話で通ることを検出し、総合終了1。最終コードでは下記GitHub CIの同コマンド全通しが成功 |
| `python tools/check_task021_regressions.py --godot /tmp/task021-bin/godot`（最終1c23008） | 終了0、TASK021_PASS: cases=8。全正負例の記録SHAは1c23008360249919f730efcc7b04de5019e18e0e |

作業中の最初の受付例は11,3/reach1でも10,3から右向きに会話でき、元の12,3/reach1でも11,3から会話できた。受付台越しの不達を、内側からの到達で成功扱いしていたため、宿の選択条件へ歩けない地形を挟む条件を追加した。元の「受付台越し」assertionを明示した修正であり、本番は変更しない。中断した通し（終了130）と初回設定保存エラーは成功扱いせず、[作業中点検](../../verification/task-021/local/preflight-note.md)へ記録した。

### 最終コードの正負例（各180秒）

| ケース | 検査側の実測 | 期待する判定 |
| --- | --- | --- |
| baseline | 終了0・293件・6.226秒 | PASS |
| inn-fixture | 終了0・293件・6.241秒 | PASS |
| inn-relocated | 終了0・293件・6.527秒 | PASS |
| relocated-outside | 終了0・51件/11枚・94.133秒 | PASS |
| relocated-rooms | 終了0・118件/22枚・75.15秒 | PASS |
| inn-unreachable | 終了1・283件・6.041秒・assertion失敗1件 | 拒否成功 |
| shrine-cleared-loss | 終了1・293件・6.349秒・assertion失敗24件 | 拒否成功 |
| restored | 終了0・293件・6.157秒 | PASS |

正常移動はコピーだけでNPC12,3→11,3、客側11,5、上向き[0,-1]、reach2。NPCと話しかけ位置は床、間の11,4は歩けない受付台で、入口から通常到達する。4人のHP/MP回復・料金なし・戦闘拒否・全状態保持が293件の中で成功した。通常入力による外観11枚/4室22枚も成功し、保存/再開と祠の確認/取消/実行/overworld不変も含む。撮影PNGは一時生成物に限り、採用待ち画像を変更しない。

届かない受付はコピー上で12,3/reach1にし、客側から受付台を越えられないことを検出して終了1・283件中1件FAIL。攻略情報消失は020と同じ成功直前の1行だけを追加し、終了1・293件中24件の状態保持/港比較assertionがFAIL。どちらもtimeout・Parse Error・SCRIPT ERROR・WARNINGを拒否理由として使っていない。全データ/本番ソースを元バイトへ戻した後は293件PASS。結果は [summary.json](../../verification/task-021/ci/summary.json)、通常入力記録は [外観](../../verification/task-021/ci/relocated-outside.json)・[4室](../../verification/task-021/ci/relocated-rooms.json)。

### 最終実装コードのGitHub CI

最終実装SHA `1c23008360249919f730efcc7b04de5019e18e0e` のpush CIを接続済みGitHubのGETで直接取得し、全20ジョブがcompleted/successで終了したことを確認した。登録SHAや作業中の旧HEADのCIではない。`gh api` はForbiddenだったため、成功した接続済みツールを使用した。

| job | 個別URL | 結果 |
| --- | --- | --- |
| lifecycle-audit | [111560113610](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113610) | completed / success |
| normal-input-and-rendering (fixed, restart-4) | [111560113706](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113706) | completed / success |
| normal-input-and-rendering (fixed, restart-1) | [111560113718](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113718) | completed / success |
| normal-input-and-rendering (fixed, journey) | [111560113727](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113727) | completed / success |
| normal-input-and-rendering (fixed, details) | [111560113736](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113736) | completed / success |
| acceptance-and-regression (fixed) | [111560113737](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113737) | completed / success |
| normal-input-and-rendering (latest, journey) | [111560113757](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113757) | completed / success |
| normal-input-and-rendering (latest, details) | [111560113772](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113772) | completed / success |
| acceptance-and-regression (latest) | [111560113773](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113773) | completed / success |
| normal-input-and-rendering (latest, restart-2) | [111560113777](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113777) | completed / success |
| normal-input-and-rendering (fixed, restart-3) | [111560113782](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113782) | completed / success |
| normal-input-and-rendering (latest, restart-3) | [111560113803](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113803) | completed / success |
| normal-input-and-rendering (latest, restart-0) | [111560113806](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113806) | completed / success |
| normal-input-and-rendering (latest, restart-1) | [111560113842](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113842) | completed / success |
| normal-input-and-rendering (fixed, restart-0) | [111560113846](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113846) | completed / success |
| normal-input-and-rendering (latest, restart-4) | [111560113861](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560113861) | completed / success |
| normal-input-and-rendering (fixed, restart-2) | [111560114042](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682324/job/111560114042) | completed / success |
| Godot・凍結受入テスト | [111560113034](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682320/job/111560113034) | completed / success |
| 素材検査 | [111560113172](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682320/job/111560113172) | completed / success |
| 試遊前の通常戦闘・案内・画面・復帰検査 | [111560113195](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37244682320/job/111560113195) | completed / success |

Godot jobの直接取得ログからR-01〜R-08の全8件PASS（tests_ran=True・parser_failed=False）、前後の保護26/26一致、`TASK021_PASS: cases=8`、`TASK007_PASS: completed=776ad944723d21c1e250a1ee5fd56d35da42cfed latest=1c23008360249919f730efcc7b04de5019e18e0e` を照合した。固定/最新の各assets/services/outside/roomsと021の両通常操作も全てPASS。実測秒数は [CIマーカー](../../verification/task-021/ci/code-markers.log)、全jobは [直接取得記録](../../verification/task-021/ci/code-all-jobs.json)。Godot jobは2026-10-04T23:41:50Z〜2026-10-04T23:54:40Zで、既存25分以内。

この報告と証拠だけを提出する次のcommitは、検証した実装コードを変更しない。文書提出commitにも既存CIの全20ジョブが走るため、push後に全ジョブ終了を確認し、その提出SHA・CI URLと結果を最終返信で親へ返す。報告内の上表は検証済み実装SHAに結び付く記録として固定し、文書提出commitの結果と区別する。

## 変更一覧と不変範囲

- `tools/check_task007_services.gd`：宿位置選択と祠全状態比較、住人証拠へ向き/reachを追加。
- `tools/capture_task007_services.gd`：6人の現在位置選択と通常祠の状態保持assertion。
- `tools/check_task007.py`：既存実行経路へ021の正負例を追加する最小3行。
- `tools/task021_service_position.gd` と `.uid`：サービスと撮影が共用するID・床・占有・reach・入口到達の選択。
- `tools/check_task021_regressions.py`：一時コピーの基準/宿移動/全通常撮影/受付負例/攻略情報消失/復帰。
- `docs/verification/task-021/`：作業前計画・実測ログ/JSON・範囲証拠・CI結果（PNG追加なし）。
- `docs/decision-log.md`：位置選択と正規化理由/復旧方法。
- 007依頼書の状態行だけ、021依頼書の状態行だけ、本報告。

不変範囲は [scope.json](../../verification/task-021/scope.json) の読取専用Git差分記録で照合した（実行器の入力や固定manifestには使用しない）。登録SHAからassets全体・原画・本番scripts/world/data・.scope-lock/test・workflow・project.godot/AGENTS・親STATUS/準備文書にtree/blob差分なし。PNG/JPG/WEBP差分0件。通常撮影で生成された007の既存証拠も元バイトへ復帰し、021の提出へ混ぜない。007/021の依頼書本文は状態行以外不変。

## 未達・未検証と親への引継ぎ

021の2指摘と正負例に未達はない。人間による人物採否、見た目の採否、main統合後のCIは親/依頼者の担当であり、本作業では未確認。独立して実施可能な021の検査・修正・報告を全て実施した。追加の判断依頼なし。

mainの取得/統合/merge/push、STATUSと親の準備文書の編集、人物/見た目の採否は行わない。007は差し戻しのまま親の再レビューへ返す。021の報告済みは人物採用やmain統合の承認を意味しない。未実装の後続施設/商品/物語には進まない。
