# 022 道具屋・武器屋の話し手表示を明確にする

依頼者採用Aを適用し、道具屋と武器屋の話し手表示だけを変更した。021の提出履歴と最新mainの親文書を通常mergeで保持した。main統合・追加委譲は行わない。

## 開始と変更範囲

登録・開始SHAは `733ccc93a4b4eb3c49893c75bb5001f809fea3c3`。開始時の未コミット変更・未pushの作業コミットは0件。ブランチは `codex/task-022-clarify-shopkeeper-labels`。

| 対象ID | 変更前 | 変更後 | 保持した配置・画像ID |
| --- | --- | --- | --- |
| oasis_date_farmer | ナツメヤシの農夫 | 道具屋の店員 | 道具屋8,4・npc_oasis_date_farmer |
| oasis_camel_keeper | ラクダ飼い | 武器屋の店員 | 武器屋8,4・npc_oasis_camel_keeper |

実装SHAは `25bad742963d3ecec4be807bd6aa03d8dcb427c9`。本番JSONの差分はlabel2箇所のみ。開始JSONへこの2値を戻すと、JSON全体が一致する。原画・assets全体・素材台帳・scripts/data・tools・.scope-lock/test・workflow・project.godot・AGENTS.mdは開始SHAと同じtree/blob。人物ID・配置・reach・会話本文・サービス条件・他人物表示・検査・上限は不変。原画の農夫/ラクダ飼いという役名と出所記録は歴史として保持した。

mainの親文書は `39cf2230c273be1e76e69c3f22d0eacb99c24c3f`、続いて最新main `6b63b291c07c86b8782c149aad2874a722ffa7ba` を `d12f0426cf8a6c03d178fdd5e0d0d9fbf6cc7a45` で通常mergeした。衝突なし。`docs/STATUS.md`、`docs/director-next-preparation.md`、014/015依頼書は最新mainと全バイト一致。親担当文書の独自編集は0件。

## 検証と通常操作

Godotは公式 `4.7.2.stable.official.ed1daf0bf`。公式ZIPのSHA-256は `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` でCIの固定値と一致。標準4.6.3は検査へ使用しない。XDGの設定/キャッシュ/保存とX11/Vulkan llvmpipeを `/tmp` へ隔離した。aptの標準パッケージ一覧が使えなかったため、別一覧で公式Debianパッケージを取得し `/tmp` へ展開した。プロジェクトの検査器・上限は変更しない。

表示変更の通常画面は既存 `capture_task007_services.gd --rooms` の道具屋・武器屋画像を保存する。専用検査が本番save_gameで作った港保存をタイトルの通常ロードで読み、以後は方向/決定/メニューキーと画面ボタンで港から村の扉・受付へ歩いて会話する。瞬間移動や状態注入で画面を作らない。既存画像は別checkoutの検査出力とし、リポジトリの007/021証拠を上書きしない。

| コマンド | 結果 |
| --- | --- |
| `godot --headless --editor --import --quit`（600秒） | 各main取込後とも終了0。警告/エラーなし |
| `python tools/validate_assets.py --strict` | 終了0。画像1140・音15・字体2・パレット3、問題なし |
| `python tools/run_locked_checks.py` | 終了0。R-01〜R-08全8件PASS、tests_ran=True・parser_failed=False |
| `python tools/check_frozen_files.py` | 前後とも終了0。保護26/26一致 |
| `python tools/check_task007.py --completed 776ad944723d21c1e250a1ee5fd56d35da42cfed --godot /tmp/task022-bin/godot` | 実装SHAの別checkoutで終了0。固定/最新007・021全てPASS |
| 読取専用Git/JSON照合、会話PNG比較 | label2値のみ変更。PNGの話し手文字の外は全画素一致 |

ローカルの全通しは検証対象 `25bad742963d3ecec4be807bd6aa03d8dcb427c9` へ固定した別checkoutで行った。固定007は当時の検査器と当時の名前・配置を全項目保持し、素材・サービス299件・外観49件11枚・4室113件22枚が成功。最新は既存検査器をそのまま実行し、表示名の正常変更を受理して素材・サービス293件・外観51件11枚・4室118件22枚が成功した。通しログは [task007-021.log](../../verification/task-022/local/task007-021.log)、全結果は [task007-summary.json](../../verification/task-022/local/task007-summary.json)。続くmain取込はSTATUSだけで、本番・素材・検査器がこの実装SHAと同じであることを照合済み。最終提出SHA自体のCIも全ジョブ終了を確認して親へ返す。

本番会話speakerの実測もbaseline/restoredの両記録で「道具屋の店員」「武器屋の店員」に一致した。021の正負例8ケースは実装SHAに一致し全て期待どおり成功。baseline・inn-fixture・inn-relocated・restoredは各293件PASS。宿の正常移動に対する通常操作は外観51件/11枚（75.216秒）・4室118件/22枚（63.430秒）PASS。inn-unreachableは283件中1件の独立assertionで終了1、shrine-cleared-lossは293件中24件の独立assertionで終了1となり、両負例を拒否した。timeout・構文/実行エラーや警告を負例成功として扱っていない。全ケースは [task021-summary.json](../../verification/task-022/local/task021-summary.json)。既存の各180秒・600歩・3000入力・300戦闘ターンの上限は保持した。

[道具屋の通常会話](../../verification/task-022/item-shop-dialogue.png) と [武器屋の通常会話](../../verification/task-022/weapon-shop-dialogue.png) を目視し、採用済みの表示を確認した。[比較画像](../../verification/task-022/before-after-dialogues.png) は左が固定007の当時表示、右が022。上が道具屋、下が武器屋で拡縮なし。両側は今回同じGodot/描画環境で通常撮影した。差分は道具屋が矩形 `[48,349,240,373)`、武器屋が `[48,349,192,373)` の話し手文字だけで、人物・背景・配置・会話本文・UI枠を含むそれ以外の全画素が一致する。[画素照合](../../verification/task-022/image-comparison.json)・[通常入力記録](../../verification/task-022/normal-input-rooms.json)・[変更範囲](../../verification/task-022/scope.json)。通常入力記録は118件/22枚の全体記録であり、本提出で保存するPNGは該当2枚と比較1枚に限定する。

## GitHub CI

実装SHA `25bad742963d3ecec4be807bd6aa03d8dcb427c9` のpush CIを接続済みGitHub GETで直接取得し、両workflowと全20ジョブがcompleted/successで終了したことを確認した。登録SHAや021の旧HEADの結果で代用していない。

| job | 個別URL | 結果 |
| --- | --- | --- |
| acceptance-and-regression (fixed) | [111567638655](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638655) | completed / success |
| normal-input-and-rendering (fixed, restart-1) | [111567638689](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638689) | completed / success |
| normal-input-and-rendering (latest, restart-0) | [111567638714](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638714) | completed / success |
| normal-input-and-rendering (fixed, details) | [111567638722](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638722) | completed / success |
| normal-input-and-rendering (fixed, journey) | [111567638723](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638723) | completed / success |
| normal-input-and-rendering (latest, restart-4) | [111567638730](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638730) | completed / success |
| normal-input-and-rendering (latest, restart-1) | [111567638735](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638735) | completed / success |
| normal-input-and-rendering (fixed, restart-0) | [111567638743](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638743) | completed / success |
| normal-input-and-rendering (fixed, restart-4) | [111567638755](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638755) | completed / success |
| lifecycle-audit | [111567638767](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638767) | completed / success |
| normal-input-and-rendering (latest, restart-3) | [111567638770](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638770) | completed / success |
| normal-input-and-rendering (latest, details) | [111567638777](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638777) | completed / success |
| normal-input-and-rendering (latest, restart-2) | [111567638785](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638785) | completed / success |
| acceptance-and-regression (latest) | [111567638843](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638843) | completed / success |
| normal-input-and-rendering (fixed, restart-2) | [111567638865](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638865) | completed / success |
| normal-input-and-rendering (latest, journey) | [111567638901](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638901) | completed / success |
| normal-input-and-rendering (fixed, restart-3) | [111567638995](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314213/job/111567638995) | completed / success |
| 素材検査 | [111567638594](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314246/job/111567638594) | completed / success |
| 試遊前の通常戦闘・案内・画面・復帰検査 | [111567638761](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314246/job/111567638761) | completed / success |
| Godot・凍結受入テスト | [111567638816](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37247314246/job/111567638816) | completed / success |

Godotジョブの直接取得ログでもR-01〜R-08の全8件PASS、tests_ran=True・parser_failed=False、前後の保護26/26一致、固定/最新のassets/services/outside/rooms、`TASK021_PASS: cases=8`、実装SHAに一致する `TASK007_PASS` を照合した。全jobは [code-all-jobs.json](../../verification/task-022/ci/code-all-jobs.json)、ログ抜粋は [code-markers.log](../../verification/task-022/ci/code-markers.log)。Godotジョブは2026-10-05T00:25:03Z〜2026-10-05T00:38:06Zで既存25分以内。

報告と証拠だけの提出commitには最新mainの親文書保全も含まれる。本番・素材・検査器は上の実装SHAと同じ。提出commitにも既存全20CIが走るため、push後に全ジョブ終了を確認し、最終SHA・CI URL・結果を最終返信で親へ返す。この表は検証済み実装SHAの記録として固定し、文書提出commitの結果と区別する。

## 変更ファイル

- `world/region2_village.json`：label2箇所のみ。
- `docs/decision-log.md`：採用Aの適用理由と復旧方法。
- `docs/tasks/022-clarify-shopkeeper-labels.md`：状態行のみ。
- `docs/tasks/reports/022-clarify-shopkeeper-labels.md`：本報告。
- `docs/verification/task-022/`：通常会話画像・比較・実行/CI証拠。

main取込の差分は親文書の保全だけであり、本担当の独自変更とは分けて記録した。

## 未達・未検証と親への引継ぎ

022の依頼範囲に未達・未検証はない。依頼書状態は報告済みとする。採用済み007の見た目を保持し、021と合わせた独立最終レビューへ親に引き渡す。main統合と統合後CI、STATUSと全体計画は親担当。本作業でmainへのmerge/push、追加委譲、後続商品・施設・物語の実装は行わない。追加の判断依頼なし。
