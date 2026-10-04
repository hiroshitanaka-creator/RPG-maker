# 013 固定監査の独立レビュー

## 開始計画

- 最新main・012提出: `5be5aeecf1a3c73a5242d18f75975eb02fa55cda`。
- 013登録: `0585583d99e29e2bde0bc8fa9dc6c42357354b6b`。最新mainを取り込んだレビューcheckout: `9c1f75f0454fc2a56cfcc274535e840149e3277b`。
- 固定006: `5f1c2ba231191b25b9b32a814b616a9f8d0a54ce`、固定009: `ce07fdada0466138260ab678c10fd78e61c0c63d`、固定012: `c327e7c439c9c8c8f1fd640e6cda6df7550fb26a`、固定記録: `9e647b3d6d0f91b061f7de974dbb5411937a2bb9`。
- 012状態が報告済みであることを読み、開始時の未コミット・未pushは0件。013依頼書を保持してmainをmergeした。
- `docs/verification/task-009/assertion-map.json` / `.md`（135箇所）、continuing-contract、007引継ぎ表を元assertionと比較する。
- 固定SHAの独立checkout・当時の範囲監査・最新本番回帰の分離、依頼書追加/状態変更/別範囲変更/merge後の再発、NPC床/占有、空イベント/サービス追加への適合を確認する。
- GitHub最終2runの全jobと実行SHA・証拠を直接取得する。取得できない結果は未確認とする。既存報告を独立検証の代用にしない。
- 実行・反証はクラウドの一時コピーだけ。元repoの変更は013状態行と本報告のみ。007以降を開始せず、009/012の状態も変更しない。
- 使用スキル: verification-before-completion。追加AI委譲なし。実行環境の既定Godotは4.6.3のため、固定版4.7.2の検証成功には算入しない。

結論・証拠は以下に追記する。

## 結論

**差し戻し（2件）。** 012で009完成点の`git log`による可変選択は解消している。通常の依頼書登録・状態編集・main取込みでは006/009/012の選択は動かず、最終mainのCI全20jobも実物で成功を確認した。しかし、012自身の固定点の独立性と、007の正当なNPC配置への適合には下記の抜けが残る。CI緑だけを理由に009/012を確認済みとすること、007へ進めることは推奨しない。レビュー担当は修正せず、親が必要な修正依頼を判断する。

### F1・優先度高：012の固定点が最新manifestとの自己一致になっている

- 対象：main `5be5aeecf1a3c73a5242d18f75975eb02fa55cda`、固定検査器`c327e7c439c9c8c8f1fd640e6cda6df7550fb26a`。
- 根拠：`tools/test_task012_pinned_audit.py:170–181`。`show(current, latest, MANIFEST)`から`expected012`を取得し、CLI/workflow/checkout/treeをその値に合わせて確認する。006/009のような独立の固定012期待値や、固定記録`9e647b3d6d0f91b061f7de974dbb5411937a2bb9`との照合がない。`wrong012-sha`負例（同ファイル240行付近）はworkflowだけを変えるため、manifestとの同時変更を捕まえない。
- 再現：クラウドの独立Gitコピー内だけで、c327e7cの012依頼書の状態行だけを変更した子commit `37b9ccc0e6ab1291534aae03f726eb0753c03408` を作成。最新mainを親に、workflowの012 SHA（envとcheckout）とmanifestのcompleted_sha/treeをその子commitへ同時変更した `8cc86bd4fe21023609ec50f28401055cd994589d` を作成。子commitの**変更していない元検査器**を別checkoutから既存CLIで実行した。
- 実測：終了0、`status=PASS`、17ケース全PASS、4.686秒。承認されたc327e7cと異なるSHA/treeを012完成点として受理した。状態行だけの通常編集では移動しないが、固定参照の誤更新を独立に拒否する保証がない。
- 影響：固定012完成点が動いていても「012固定記録と一致」「誤SHA拒否」を成功と報告できる。完成点の不変性という今回の主要条件が満たされない。
- 最小修正案：完成後に保存した既存の固定記録commitを信頼基点として、現在のmanifest・workflow・checkoutをそこに記録された012 SHA/treeと独立照合する。状態だけ変えた別commitと、workflow＋manifest＋checkoutの同時付替えを負例に加える。当時の検査器と当時の全条件を保持し、新たな完成点探索や無限の固定用タスクを導入しない。

再現の中核（`test_task012_pinned_audit.py`の既存helperを一時cloneで使用。repoは一時clone、latestは上記main、originalはc327e7c）：

```python
state = a.normalized_request(a.show(repo, original, a.REQUEST012)).replace(
    b'- state: excluded', '- 状態：後続状態変更（013反証コピー限定）'.encode())
moved = a.synthetic(repo, original, {a.REQUEST012: state})
manifest = json.loads(a.show(repo, latest, a.MANIFEST))
manifest['completed_sha'] = moved
manifest['completed_tree'] = a.run(repo, 'rev-parse', moved+'^{tree}').decode().strip()
workflow = a.show(repo, latest, a.WORKFLOW).replace(original.encode(), moved.encode())
current = a.synthetic(repo, latest, {
    a.MANIFEST: json.dumps(manifest).encode(), a.WORKFLOW: workflow})
```

currentとmovedをそれぞれ別checkoutし、次を実行。固定009はce07fdaの別checkout。commit時刻でコピーのSHAは変わり得るが同じ結果を確認できる。

```sh
timeout 180 python <moved-checkout>/tools/test_task012_pinned_audit.py \
  --current-path <current-checkout> --fixed009-path <ce07fda-checkout> \
  --completed012-sha <moved> --latest-sha <current>
```

### F2・優先度中：家具裏のNPC足元への到達要求が007の配置を誤拒否する

- 根拠：`tools/check_region2_village_regression.gd:189–193`。全セル検査は170–176行で床と占有を分離したが、`contract.targets`への到達は占有を区別せず、全座標へのBFSと実歩行を要求している。`docs/verification/task-009/continuing-contract.json`のitem/weaponの`counter_back=[8,4]`は店員を置ける床でもある。007本文は自然な位置の店員配置を許可し、009報告S06は「最新継続検査をそのまま運用」と記載する。
- 再現：最新mainの一時コピーの`world/region2_village.json`で、`site.rooms[2].events`だけを`[{"id":"task013_counter_copy","kind":"npc","cell":[8,4],"text":["コピー限定"]}]`へ変更。地形・本番コード・検査器・固定fixtureは変更しない。固定版Godotで既存`check_region2_village_regression.gd`を直接実行（故障注入実験なので未commit変更を拒否するPythonラッパーの成功とは扱わない）。
- 実測：終了1、7644 checks、25.137秒、失敗は「リンク判定を除いたBFSの客側・家具前後到達」「本番移動経路: (8, 4)」の2件のみ。SCRIPT ERROR/ERROR/WARNING/Parse Errorなし。
- 対照プローブ：既存回帰を継承した一時スクリプトで、固定地形が床、実NPC占有、足元への移動拒否と全状態保持、入口→隣接`[7,4]`→室外→村外`[168,88]`を本番APIの通常歩行で確認。終了0、70 checks、1.210秒。入口閉塞や到達不能を正当と誤認した反証ではない。
- 影響：承認範囲内の店員配置なのに、昔の空床への歩行条件で最新CIが落ちる。すべてのNPC配置が失敗するという意味ではなく、009の外観`[20,25]`正例だけではこの衝突を検出できない。007の6人・宿・祠が実装済みとの主張もしない。
- 最小修正案：当時の家具裏セルへの全到達は固定006に保持する。最新側では地形・出入口・客側経路を維持しつつ、占有された店員位置は到達可能な隣接/会話位置と占有拒否を検証する。カウンター裏NPCの正例と、実際の入口/通路閉塞を拒否する負例を追加し、対応表S06とA082（および歩行helper）を整合させる。撮影の固定座標との衝突も007の配置確定時に同様に検証する。保護された既存検査の変更は別途承認範囲を定める必要がある。

## PASSと未確認の切り分け

| 観点 | 判定・証拠 |
| --- | --- |
| 006全項目の当時実行 | PASS。workflowは完全SHAの別checkout、旧Python/GDScript/撮影器を使用。固定runtime7592・20保存・5再起動9/26/37/51/43、7描画mode137/34/17×5・49枚を最終CIログで確認 |
| 009の完成点選択 | PASS。ce07fda固定checkoutの旧scope検査器を実行。tree `655312a33364d8e3fe97f09bd9bd3c415ed1ceae`との独立照合。旧git log選択による親登録拒否の負例も残る |
| 012の通常後続編集 | PASS。main上の既存17ケースを再実行。013登録＋main取込みの実merge `9c1f75f0454fc2a56cfcc274535e840149e3277b` でも17ケースPASS（2.765秒）。012の同時付替え耐性はF1で差し戻し |
| 最新本番の検査 | PASS。currentで指定SHA=checkout HEADを検証し、本番/検査/期待値のdirtyを拒否。最新runtimeは実mainを動かし7662・20保存・5再起動10/27/38/52/44。固定006の成功で代用していない |
| 元assertion対応 | 135箇所=当時だけ10・最新継続121・007置換4、未分類0。固定ソース列挙・fixture固定006照合はPASS。旧/新GDとcaptureの差分を読み、空events・受付無反応・祠不可・capture無反応の4箇所が固定側に残ることを確認。対応表の機械検査は最新関数の存在までで意味同値は保証しないため、F2も別途検出した |
| NPC正負例 | CI実物の床配置前後は各39項目、外観NPC付き回帰7656成功。占有無視負例は実assertion2件失敗、誤接続・不正保存も該当assertionと終了1を要求。timeout/parse errorでは成功しない。追加のカウンター裏はF2 |
| 保存・帰還・撮影 | 最新の20全状態保存、非初期値、旧保存、不正型/room拒否、補正、5別プロセス、帰還の正負例を保持。描画は通常入力で7mode、最新132/34/17×5・49枚。サービス操作の正負例は007のS01〜S06へ引継ぎ、未実装・未検証 |
| 後続008/010/011 | 依頼書を確認。文書編集は固定scopeに混ざらず、011本文には段階限定の固定受入と最新不変条件の分離が明記済み。実装・保存/階段等の成功は未確認。物語内容は本報告へ転載しない |
| 保護・原画・既存検査 | ce07fda→mainのassets/scripts/world/data/test/.scope-lock/addons/project.godot/既存ci.ymlは差分0。c327e7c→mainのtoolsも差分0。保護26/26の独立ローカル照合とCI R-01〜R-08全PASSを確認 |
| 検査弱体化/予算 | 012の差分は選択と反証追加。既存17job・固定/最新のmatrix・各job15分、import600秒、実行/描画180秒、内部180000ms/600移動/3000入力/300ターンを維持。通常CI上限35分/25分/素材未指定、Rverify300秒。continue-on-errorなし。matrixの反対世代だけのskipを、未実行ジョブの成功と混同しない |
| 欠損/古い証拠 | 最新ラッパーは対象JSONを実行前に削除し、結果欠損/誤SHAをFAILにする。固定側は過去JSONを先に削除しないが、この最終runは旧コマンドの実行・全件数をログで確認。artifactには過去世代も同梱されるため、名前だけで今回証拠に数えない。失敗時や欠損時の全パターンを故障注入したわけではない |

## 最終main CIを直接確認した証拠

対象は両runとも`5be5aeecf1a3c73a5242d18f75975eb02fa55cda`。通常のgh APIは403だったため、接続済みGitHubコネクタで全job・steps・全20jobのログ・artifact一覧を直接取得した。012報告内の過去60job一覧の転載ではない。

- 専用 [37199190377](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377)：17/17 completed/success。全matrixの本来実行するstepはsuccess。固定006/009/012と最新SHAをログ中のJSONで区別し、17反証＋既存7正負例も全PASS。
- 通常 [37199190393](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190393)：3/3 completed/success。job111427172199に`PASS R-01`〜`PASS R-08`、各exit=0/tests_ran=True/parser_failed=Falseを確認。
- 最新runtime artifact [11302636151](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/artifacts/11302636151) を実際にダウンロード。ZIP SHA256 `efd7e887a03c682f9fe9c024aad32781f80fbb9058a63580cb949dc74299c5e3` がAPI digestと一致。直下のruntime-checks/regression-summary/restart-0〜4の7JSONは全PASS・main完全SHA一致。runtime7662/保存20を確認。同梱の描画サブディレクトリには旧`842306feadaef19760022240c3f37004b2ae69c6`も含まれるので、それを今回の描画証拠には使っていない。今回描画の根拠は各描画jobの直接取得ログ。

以下の秒数は取得ログの最初と最後のtimestamp差（四捨五入）で、課金時間ではない。過去版と同一条件の負荷比較は実施しておらず、増加量・利用量・費用は不明。

| job（実物ログ） | 結果 | ログ区間秒 |
| --- | --- | ---: |
| [lifecycle-audit](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427171804) | success | 198 |
| [acceptance-and-regression (fixed)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427171932) | success | 122 |
| [normal-input-and-rendering (latest, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427171979) | success | 155 |
| [acceptance-and-regression (latest)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427171986) | success | 121 |
| [normal-input-and-rendering (fixed, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172092) | success | 185 |
| [normal-input-and-rendering (latest, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172104) | success | 226 |
| [normal-input-and-rendering (fixed, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172123) | success | 154 |
| [normal-input-and-rendering (fixed, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172124) | success | 134 |
| [normal-input-and-rendering (fixed, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172135) | success | 163 |
| [normal-input-and-rendering (fixed, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172136) | success | 251 |
| [normal-input-and-rendering (latest, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172143) | success | 213 |
| [normal-input-and-rendering (latest, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172146) | success | 139 |
| [normal-input-and-rendering (latest, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172158) | success | 227 |
| [normal-input-and-rendering (latest, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172165) | success | 156 |
| [normal-input-and-rendering (latest, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172166) | success | 169 |
| [normal-input-and-rendering (fixed, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172173) | success | 158 |
| [normal-input-and-rendering (fixed, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190377/job/111427172181) | success | 154 |
| [試遊前の通常戦闘・案内・画面・復帰検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190393/job/111427171960) | success | 269 |
| [素材検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190393/job/111427172106) | success | 97 |
| [Godot・凍結受入テスト](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37199190393/job/111427172199) | success | 191 |

## 独立実行コマンド・制約

- `git fetch origin main codex/task-013-review-pinned-audits`、`git ls-remote`で登録SHA/main一致を確認。013登録をcheckoutしてmainを通常merge。依頼書本文の保存をGit差分で確認。
- 固定版ZIPを取得し上記workflowのSHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`と照合、`--version`は`4.7.2.stable.official.ed1daf0bf`。
- 最初の既定Godot importは4.6.3で、固定版の検証に算入しない。固定版の初回importにもクラウドのconfig書込み先エラーがあったため成功と数えず、XDG_CONFIG_HOME/XDG_CACHE_HOME/XDG_DATA_HOMEを/tmp配下に設定して`timeout 600 <固定Godot> --headless --path <mainコピー> --editor --import --quit`を再実行。終了0、SCRIPT ERROR/ERROR/WARNING/Parse Errorなし。その後に動作検証した。
- `timeout 180 python <c327e7c>/tools/test_task012_pinned_audit.py --current-path <mainコピー> --fixed009-path <ce07fda> --completed012-sha c327e7c439c9c8c8f1fd640e6cda6df7550fb26a --latest-sha 5be5aeecf1a3c73a5242d18f75975eb02fa55cda`：終了0、17ケースPASS。013実mergeへの再実行も上記のとおりPASS。
- `python tools/check_task009_assertion_map.py`：終了0、135箇所、未分類0。`python tools/check_frozen_files.py`：終了0、26/26一致。
- 一時mainコピーで`python tools/check_region2_village_regression.py --commit HEAD --godot <固定Godot>`：終了0、runtime7662（24.039秒）/restart10,27,38,52,44（1.209/1.111/1.302/1.204/1.108秒）すべてPASS。F2注入前に実行し、反証後には本番3ファイルが元mainとバイト一致することを再確認。
- F1とF2の実測・再現は前掲。実験用Git objects/index、NPCデータ変更、継承プローブ、出力JSON/logは/tmpのコピーだけで扱い、元repoの本番/検査へ混入させていない。
- 固定006の全描画、最新の全描画、R全8の今回の成功根拠は直接取得した**最終main CI**。クラウドでそれらすべてを再度手動実行したという意味ではない。007の6人/宿/祠の統合正負例・人間試遊・60時間実測は未実施。
- 指定モデル/effortは依頼書どおりの希望として保持。実効モデル名/effortを環境から照合できるAPIはなく、独立に確認済みとは記載しない。追加AI委譲・ローカルPC利用なし。

## 変更範囲と提出時の自己点検

- 変更ファイルは`docs/tasks/013-review-pinned-audits.md`の状態行と`docs/tasks/reports/013-review-pinned-audits.md`だけ。main取込みの差分は既存mainの保持であり、本レビューによるコード修正ではない。
- 完全SHA、全20job終了、固定側毎回実行、最新側本番実行、対応表、保護不変を照合。判明した失敗をCI成功で隠していない。
- 013を報告済みにして登録ブランチへ通常commit/pushする。提出commit自身のCIは最終応答に結果または未確認を記載する。レビュー対象mainの成功と混同しない。
- F1/F2が残るため本レビューからmainへは反映しない。009/012を確認済みに変更しない。007/008/010/011は開始・発注せず、報告済みで本件を終了する。
