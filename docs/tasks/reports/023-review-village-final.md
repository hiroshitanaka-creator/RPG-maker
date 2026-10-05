# 023 村のサービス検査・店員表示の独立最終レビュー

**PASS。020の2指摘は元反証の再実行で解消を確認し、022の表示名2値限定と対象全20CIの成功を確認した。**

## 作業前の計画

- 登録SHA：13c442d8a3e8486bc27bf9996a188940b2179a61。対象022最終：e9fe3432c7756f4d1aea948b59aff8ddd69acd43。021最終：c3cfd7524aaae0ab9bb01d51f221b13b867133d2。020報告：79b8141ca03a3b4fe987a43192e3d28f719cd74a。
- 020/021/022の依頼・報告・実差分を読み、対象SHAの一時checkoutで020の受付正常移動・受付不達・祠cleared消失を再実行する。通常操作撮影、位置4項目以外の状態保持、固定007・最新回帰・既存上限、表示名限定差分と画像、対象SHAの全CIを確認する。
- 変更先は本報告と023依頼書の状態行のみ。開始時の未コミット変更0件、登録SHAに対する未pushコミット0件。コード修正・追加委譲・監査層追加・main統合は行わない。採用済みの人物と表示名は再判断しない。

## 差分・旧検査・上限の照合

020報告は指定79b8141と現行で同一。021報告も指定c3cfd752と現行で同一。021登録2ea69006d54ba39ae685bea7f54a17f4a73b82b3から021提出までの40ファイルは、指定の検査6ファイル（uidを含む）、021証拠・報告、decision-log、007/021状態行に限定される。固定007完成点は776ad944723d21c1e250a1ee5fd56d35da42cfedのまま。

- P2-1：`task021_service_position.gd` はID一意・床・NPC占有を確認し、入口から通常通行可能な位置をBFSで列挙する。宿では歩けない受付台を挟む距離2以上の位置を選ぶ。回復・料金なし・戦闘拒否・回復/対面以外の全状態保持のassertionは維持。撮影器はその位置へ既存 `_walk` の通常入力で歩き、決定キーで会話する。探索用の複製辞書へのplaceは経路判定用であり、本番をそこへ移す処理ではない。
- P2-2：祠成功前後のoverworld全体を、侵蝕値の正境界4例・魔物化全8系統・通常操作で比較する。従来祠との横比較はlayer/node/room/cellだけを正規化して、状態辞書全体を比較する。`FirstRegion.place` 自体もこの4項目だけを書き換える。cleared・transport・residents・facing・entry_lockを含め、残りの全キーは除外していない。拒否時の全状態保持も維持。
- 固定007は別checkoutで当時のassets/services/captureを実行し、初期配置・会話文の19件を含むサービス299件、外観49件11枚、4室113件22枚を保持。最新は初期セル/文言を要求せず、サービス293件・外観51件11枚・4室118件22枚。元の保存/補正、正逆向き、宿・祠の各assertionは残り、上記の状態比較が追加される。021の対応表を実diff・固定版の実コードと照合した。
- `check_task007.py` の変更は既存の固定/最新実行後に021の一時変異8ケースを呼び、総合判定へ含めるもの。新しい固定manifest・固定点・workflow・再帰監査層なし。assets検査器と撮影の継承元も007提出から同一。
- `.github` 全treeが021登録時から同一。Godot job25分、preplay35分、村job15分、import600秒、サービス/撮影各180秒、600歩/3000入力/300戦闘ターンを保持。skip・continue-on-error追加やassertion削除による成功化なし。

021登録から対象022まで、assets・scripts・data・.scope-lock・test・.github・project.godot・AGENTS.mdのtree/blobが全て一致することを独立に照合した。021自体のworldも不変。022のworld差分は次節の2値だけ。原画SHA-256は `495769b171adf3ba88fd5ba5fc4749dd67c0454d8606e248dad065d8645365c8` と実ファイルから再計算して一致。原画・素材・台帳・パレット・保護26件を変更していない。

## 022表示名・画像

c3cfd752からe9fe3432の本番差分は `world/region2_village.json` の次の2値だけ。JSONを読み、2値を元へ戻して文書全体の一致もassertした。

| ID | 旧表示 | 採用表示 |
| --- | --- | --- |
| oasis_date_farmer | ナツメヤシの農夫 | 道具屋の店員 |
| oasis_camel_keeper | ラクダ飼い | 武器屋の店員 |

人物ID・sprite・配置・reach・会話本文・サービス条件・その他の人物表示は同一。原画の役名と出所は歴史として保持されている。

[道具屋](../../verification/task-022/item-shop-dialogue.png)、[武器屋](../../verification/task-022/weapon-shop-dialogue.png)、[前後比較](../../verification/task-022/before-after-dialogues.png)を実際に開いて確認した。役割に対応する表示が枠内に収まり、受付の人物・操作人物・背景・本文・UI枠に目視差分なし。人物と店員表示は依頼者採用済みであり採否を再質問しない。

比較PNGの左右を1024×576で読み出し、右側が各提出PNGと全画素一致することをassert。RGB差分の外接矩形を独立に再計算すると、道具屋 `[48,349,240,373)`、武器屋 `[48,349,192,373)`。文字の外は全画素一致し、既存image-comparison.jsonと一致した。PNGのSHA-256もそれぞれ `c8a1474ea8117937df1b7d4d15e2900287d8d35ea4b24c665256d5cebc583aa0` / `964c510f88f194ebffb0103ceb1591dc5a6b233181c0475996401413d299b529` と一致。これは022提出画像の独立照合であり、本レビューで原画像を再保存してはいない。

## 対象完全SHAのCI直接確認

GitHub CLIのGETはForbiddenだったため、接続済みGitHubのGETで対象e9fe3432c7756f4d1aea948b59aff8ddd69acd43のpush実行を取得した。022ブランチの [CI 37248458952](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458952) と [固定受入/最新回帰 37248458906](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906) はともにcompleted/success。jobsをper_page=100で直接取得し、全20件のhead_sha・終了・successを確認。報告中の旧実装25bad742のCIでは代用していない。

| job | 直接確認したjob | 結果 |
| --- | --- | --- |
| Godot・凍結受入テスト | [111570991666](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458952/job/111570991666) | completed / success |
| 素材検査 | [111570991870](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458952/job/111570991870) | completed / success |
| 試遊前の通常戦闘・案内・画面・復帰検査 | [111570991882](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458952/job/111570991882) | completed / success |
| acceptance-and-regression (fixed) | [111570991483](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991483) | completed / success |
| normal-input-and-rendering (latest, restart-0) | [111570991605](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991605) | completed / success |
| lifecycle-audit | [111570991623](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991623) | completed / success |
| acceptance-and-regression (latest) | [111570991660](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991660) | completed / success |
| normal-input-and-rendering (fixed, details) | [111570991732](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991732) | completed / success |
| normal-input-and-rendering (fixed, journey) | [111570991742](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991742) | completed / success |
| normal-input-and-rendering (fixed, restart-3) | [111570991764](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991764) | completed / success |
| normal-input-and-rendering (fixed, restart-2) | [111570991771](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991771) | completed / success |
| normal-input-and-rendering (latest, restart-1) | [111570991779](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991779) | completed / success |
| normal-input-and-rendering (latest, journey) | [111570991792](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991792) | completed / success |
| normal-input-and-rendering (fixed, restart-1) | [111570991822](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991822) | completed / success |
| normal-input-and-rendering (latest, details) | [111570991829](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991829) | completed / success |
| normal-input-and-rendering (latest, restart-2) | [111570991842](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991842) | completed / success |
| normal-input-and-rendering (latest, restart-3) | [111570991847](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991847) | completed / success |
| normal-input-and-rendering (fixed, restart-0) | [111570991858](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991858) | completed / success |
| normal-input-and-rendering (fixed, restart-4) | [111570991859](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991859) | completed / success |
| normal-input-and-rendering (latest, restart-4) | [111570991880](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37248458906/job/111570991880) | completed / success |

Godot job111570991666の生ログを直接取得し、R-01〜R-08全8件の `PASS (exit=0, tests_ran=True, parser_failed=False)`、実行前後の「保護対象26件、一致26件」を確認。さらに固定/最新のassets/services/outside/roomsが全てPASS、`TASK021_PASS: cases=8`、`TASK007_PASS: completed=776ad944723d21c1e250a1ee5fd56d35da42cfed latest=e9fe3432c7756f4d1aea948b59aff8ddd69acd43` を確認した。固定/最新の撮影は76.646/58.170秒と73.851/57.937秒、021移動後撮影は74.036/57.452秒。Godot jobは約13分で既存25分以内。固定007全通し、R8、他の既存CIはこの対象SHAの直接取得ログを根拠とし、本レビューで全CIをローカル再実行したという意味ではない。

## mainの親文書の保持

読取取得した最新mainは9159ec22b5dc4edfde125fab408e4767b34d8841。022が取り込んだ6b63b291c07c86b8782c149aad2874a722ffa7baのSTATUS・director-next-preparation・014/015依頼書は、対象e9fe3432で全バイト保持されている。最新mainだけの追加差分はSTATUSの023発注・022完了記録で、本ブランチは共通祖先からそのSTATUSを変更していない。準備文書と014/015も最新mainと一致。

親は最新main上で本レビュー提出ブランチを通常の3-way mergeすれば、STATUSの最新追記と本ブランチの007/021/022実装・報告を双方保持できる。古いブランチ側のSTATUSで上書き・reset・force-pushしない。統合後に親文書と保護を照合し、素材importと全CIを確認する。本レビューではmainへのmerge/pushは行っていない。

## 独立再実行（本レビューで実測）

対象e9fe3432のdetached worktreeを `/tmp/review023/target` に作成し、その未変更の `check_task021_regressions.py` を実行した。内部でさらに一時コピーを作り、020と同じJSON変更・成功直前のcleared消去1行を適用する実装を読んで確認した。保存した全結果のexecution_shaもe9fe3432に一致。作業ブランチの本番・検査・既存証拠は上書きしない。

公式Godot 4.7.2.stable.official.ed1daf0bfを取得し、ZIP SHA-256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` をCI固定値と照合。標準4.6.3は使用しない。XDG保存/設定/キャッシュと公式DebianのXvfb/Vulkan llvmpipeを/tmpへ隔離した。標準apt一覧の取得失敗は別の公式Debian一覧で解消。検査器・renderer・上限は変えていない。

| 実行 | 結果 |
| --- | --- |
| `timeout 600 <Godot4.7.2> --headless --editor --import --quit` | 終了0、警告/エラーなし |
| `python tools/validate_assets.py --strict` | 終了0、画像1140・音15・字体2・パレット3、問題なし |
| `python tools/check_frozen_files.py` | 対象と作業ブランチ、実行前後とも26/26一致 |
| `python tools/check_task021_regressions.py --godot <Godot4.7.2>` | 終了0、TASK021_PASS: cases=8 |
| Git tree/blob・JSON・Pillow読取比較 | 上記不変範囲、label2値限定、文字外全画素一致 |

| 元反証・復帰ケース | 終了 | 実測 | 判定 |
| --- | --- | --- | --- |
| baseline | 0 | 293件、8.110秒 | PASS |
| inn-fixture（12,3・reach2） | 0 | 293件、7.898秒 | PASS |
| inn-relocated（11,3・reach2） | 0 | 293件、7.619秒 | PASS |
| 移動後の通常外観操作 | 0 | 51件・11枚、77.128秒 | PASS |
| 移動後の通常4室操作 | 0 | 118件・22枚、63.808秒 | PASS |
| inn-unreachable（12,3・reach1） | 1 | 283件中1失敗、7.729秒 | 実assertionで拒否 |
| shrine-cleared-loss | 1 | 293件中24失敗、7.808秒 | 実assertionで拒否 |
| restored | 0 | 293件、8.006秒 | PASS |

正常移動は客側11,5・上向き[0,-1]・reach2。宿の4人HP/MP回復、料金なし、回復/対面以外全状態保持、戦闘拒否が成功。通常入力はX11で外観203歩/215入力・室133歩/213入力、戦闘ターン0、各上限以内。通常セーブ/再開、祠確認/取消/実行後のoverworld不変も成功した。

受付負例は `宿IDの床・占有・reach・入口到達` の失敗。祠負例は020と同じ `if _state["overworld"]["node"]=="region2_village":_state["overworld"]["cleared"]=[]` の1行だけで、`祠成功前後のoverworld全体不変` と `従来祠との同条件・同全状態`、全8系統の対応assertionが失敗した。timeout・parse error・実行エラー・警告を拒否成功としていない。元バイトに戻すと293件成功し、対象checkoutのworld/scripts/toolsも対象SHAと一致。

実測ログとJSONは一時checkoutに出力して内容を確認し、本節へ結果を記録した。提出範囲が専用文書だけのため、既存証拠の更新や別の検査・画像ファイルの追加はしない。

## 結論・未確認・提出範囲

**PASS。依頼範囲の要修正指摘なし。** 020のP2-1/P2-2は元反証の再実行で解消を確認。022は採用済み表示名2値だけであり、原画・保護・旧検査・上限を保持している。対象SHAの全20CI、R8、固定007/最新回帰も直接確認した。

未確認は人間による長時間プレイとmain統合後のCI（親担当）。採用済みの見た目を再審査せず、全コードの悪意変更や後続機能など依頼外へ広げていない。範囲内の未達・追加判断依頼なし。

変更ファイルは `docs/tasks/023-review-village-final.md` の状態行（報告済み）と本報告のみ。対象e9fe3432の検証結果と、この文書提出コミットのCIは区別する。文書提出後のSHA・push結果・CI確認状況は最終返信に記載する。main統合・後続発注・コード修正・新規監査層・追加委譲は行っていない。
