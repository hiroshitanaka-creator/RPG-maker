# 085 遺跡の場面・遭遇・別操作の報酬

基点：main `2a4fae60868d59f355839b524d22729704dd54f7`。084を再実装しない。2026-10-29 I-20261029-004の本人A採用（場面・通常4種＋ボス1種・厳密41種）と、以後の制作判断の継続委任に基づく単一逐次作業。

採用全文：lucca-workspace `005c4c9094777bbbf9b04bead88786f1818531d2` の `projects/rpg-maker/drafts/s11-record-scene-proposal-20261029.md` と `s11-battle-proposal-20261029.md`。鍵の対応先調査 `bbf5019a8aa583a7180c59f761e78b1d0237fcb8` は次タスクの準備資料であり、新室を今回実装しない。

## 実装範囲

- room3 [18,15]で22行の採用原稿を既存会話UIへ統合。最終通常確認のみ読了。再訪2行、中断後は未読から再開、旧保存の現在地は保持する。
- 記録後は自由移動・待機・メニュー・帰路を可能にする。ボスの明示的な調査操作で戦闘、勝利後の別操作で箱から遺跡の鍵を取得。旧保存が既に広間にいる場合は調査時に記録を先行し、終了後の再操作で戦う。
- 採用通常4種＋ボス1種だけを本番登録。原36種は全定義不変。7候補の素材台帳は保持。既存技・AI・normal/boss報酬値を使用。最下層通常無遭遇。階段・入口・出口・移動失敗で遭遇しない。
- GameSessionの厳密数、沿岸検査の旧30＋沿岸6＋新5条件、および敵行動検査の厳密41＋沿岸6/新5の完全集合条件だけを承認された契約移行として改訂。保護、CI、他の検査強度・上限は変更しない。
- AGENTS.mdの創作確認だけを最新の明示委任と整合する。親所有のdocs/tasks/README.mdとdocs/decision-log.mdは変更しない。

## 予定パス

既存：AGENTS.md、data/catalog.json、scripts/game/game_session.gd、scripts/world/{region2_ruins,first_region,first_region_view}.gd、scripts/ui/game_root.gd、world/region2_ruins.json、tools/{task011_ruins_defs,build_task011_ruins}.py、tools/check_second_region_coast.gd、tools/check_enemy_encounters.gd。
新規：data/region2_ruins_scenes.json、scripts/world/region2_ruins_story.gd/.uid、tools/check_region2_ruins_s11.gd/.uid、tools/check_region2_ruins_s11.py、tools/capture_region2_ruins_s11.gd/.uid、本依頼書、docs/tasks/reports/085-region2-ruins-s11.md、docs/verification/task-085/**。

## 機械受入

- 本文・話者・順序を採用原稿と固定比較。不正ID・実行番号・ページ、重複通知、他会話/戦闘中開始、移動・古いUI操作の拒否を検査。
- 中断/再実行、未読地点上の保存、旧広間内保存、再訪、読了前/勝利前/勝利後受取前/受取後の通常保存・checkpointを検査。侵蝕89/90/91、職、不可逆性、HP/MPは記録で変えない。
- 原36件の固定比較、新5件の完全ID/能力/技/参照、41件厳密数、保留2除外、4階の遭遇表と遷移歩無遭遇、敵の予定列・MP消費、敗北無報酬・勝利boss報酬・箱の一度だけ取得を検査。
- 通常の実進行から到達した戦力で道中・ボス・帰路・補給・再挑戦を測定し、人工境界状態と分けて保存する。
- Godot 4.7.2で取り込み後にR-01〜R-08、保護26件、素材strict、関連082/083/084回帰、011固定/最新の原検査を上限・assertion不変で実行。旧段階限定条件は完全SHA固定側へ保持し、新機能の置換条件と区別する。
- 実Godotの本番キー操作と代表画面を保存し、目標画像と比較。人間の初見プレイ・約60時間実測は機械合格と分離する。
- 全変更を通常作業ブランチへcommit/push、ネタバレを避けたdraft PRを作成し、同じremote HEADの全CI終了を確認。main push/approve/merge/force push/外部委任なし。

## 報告

別報告に実変更パス、コマンドと実結果、コミット/PR/最終CI、判断理由・戻し方、未達/未検証を残す。新しい鍵の対応室・扉は後続作業であり、節目7全体/ゲーム全体の完成とは扱わない。

## 親の依頼範囲訂正（継続修正）

2026-10-29、親が本人の原質問/回答を再読し、厳密36→41承認は2ファイルに限定されていないことを確認した。claim `13386ee1cabddb4cedf1919166b066e37f8355b2be4dfc34df6f0ff127afbb24` / seq369により、同じ085・同ブランチの継続修正としてtools/check_enemy_encounters.gdを追加する。保護26/全protected_pathsに該当しないことも親が照合した。新しいゲーム規則の採用ではない。

当該ファイルは厳密総数・完全ID集合とその説明/成功メッセージだけを移行する。元mainの全bytes固定コピーと元assertion全件、旧AI/連戦/UIを保持する。check_region2_ruins_s11.pyの当該1ファイルの旧全文不変条件は、固定旧コピーhash/main一致と、5置換以外の全bytes不変・6負例の厳密検査へ置換する。他の旧全文不変条件は維持する。

変更対象追加はこの2検査器、本依頼書、別報告、docs/verification/task-085/**のみ。AGENTS/本番処理/親2文書/CI/test/.scope-lock/その他保護/画像/台帳は継続修正では変更しない。拒否済みdraft PRは再試行せず親の別の原文照合を待つ。

新規証拠パスはdocs/verification/task-085/corrective/{check_enemy_encounters-main-2a4fae6.gd.txt,assertion-migration.json,migration.patch,migration-checks.json,commands.json,source-hashes.json,ci-before-resume.json,task011-components.json,task011-evidence.tar.gz,locked-checks.json,locked-logs.tar.gz,task027-diagnostic.json}。ログは同corrective/logs/{import,enemy,s11-data,s11-runtime,route,resupply,balance,capture,locked,assets,frozen-before,frozen-after,shrine-data,shrine-runtime,s10-static,coast,saved-value-types,task011,task011-boundary}.logへ保存する。実行前にcommands.jsonへ各コマンド・元上限を列挙し、実結果を追記する。

継続修正の追加実ログ：corrective/logs/s10-static-data.log、s10-static-data-first.log、fetch-s10-reference.log、port.log。前述の固定参照不足と元180秒の通知撮影TIMEOUTは原ログ保持し、未到達検査を成功扱いしない。checker2件を固定したcb5c762での実結果・固定コピー・assertion対応・R-01〜R-08と実画像は別報告へ記録する。
