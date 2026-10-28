# 083 採用済み静止人物のS10画面統合 実装計画
- 状態：発注準備。実行受付は別記録。
- 担当：Codex、GPT-6.1 Sol / High。ルッカは採否・依頼書・親受入・親記録。
- 基点：RPG-maker main a4dc7c9d0d705f3181391fdccee4e4c825ddcaaf。082本体PR63と親記録PR64、最終全38CI/R8/前後保護26確認済み。
- 依頼日：2026-10-28 JST。
- 作業ブランチ案：codex/task-083-s10-static-placement-20261028。main直書き・マージは担当範囲外。draft PRまで。
- 他の実装タスクなし。registry変更と082結果依存があるため1本のみ逐次発注。

## Goal / Architecture / Tech Stack / Spec
Goal：採用済み32×48静止表示をroom4の[8,6]へ置き、082の会話・通常移動・保存復帰・実描画と矛盾なく接続する。
Architecture：既存npc占有を用い、表示専用属性で新会話を発生させない。静止画は歩行シートへ偽装せず既存_object描画経路を使う。
Tech Stack：Godot4.7.2/GDScript/Python/Pillow、既存素材・台帳・検査。
Spec：本人I-20261028-008、質問Sentinel_f02fdc7cda008191ae47fea143effba8に対するB。提示画像commit d46151a633a2b5701bf0c583bf01344f39095929（lucca/s10-placement-preview-20261028）。
本人原文B、受信2026-10-28T05:35:56.315527+00:00、message Sentinel_449ed1f483d48191b0bcfcfd48dd4dd8。
採用は提示された表示案とB中央[8,6]。新人物設定・本文・任意職規則・戦闘・報酬を作る許可ではない。

## 入力
- 採用画像：d46151a の docs/verification/s10-placement-preview/ner-static-proposal.png、SHA256 121010a316a31b88dca753ed48bc9404f176a4fe5f0d6dd5508ebf0615559f5d。
- 原画：assets/_incoming/owner-2026-10-05-grok-batch3/oasis-shrine-keeper-chibi.png、SHA256 7fb285a7c31839ff33350c328f39dfd97e94ea57a0fe6567ef862f8fb19a9aa5。
- conceptは参考だけ。原画2点のbytes不変。別人物の似た素材で代用しない。
- d46151a のプレビューscript/README/manifestと5PNGを確認。静的合成は実ゲーム画面ではないので、実Godot撮影で置き換える。
- 082正式報告 docs/tasks/reports/082-report.md、既存tools/check_region2_shrine_story.gd、本文検査。本文・scene/run/page・初期4職/旧共通ゲート境界を維持。

## 変更予定ファイル
本番・検査補助：
1 world/region2_village.json
2 scripts/world/first_region_view.gd
3 scripts/game/game_session.gd
4 assets/characters/ner/event_standing.png（新規）
5 assets/registry.json（この1素材の追加だけ）
6 assets/source_records/s10-ner-static.json（新規）
7 tools/validate_assets.py（既存出所拒否条件を保ち、承認chibi原画の固定path/SHAを1件許可一覧に追加するだけ）
8 tools/import_s10_ner_static.py（新規。採用原画からの再現と採用PNGのSHA照合）
9 tools/check_s10_static_display.py（新規）
10 tools/check_s10_static_display.gd と .uid（新規）
11 tools/capture_s10_static_display.gd と .uid（新規）
依頼書・報告・証拠：
12 docs/tasks/083-s10-static-placement.md（この依頼文の写し。意味を変更しない）
13 docs/tasks/reports/083-report.md
14 docs/verification/task-083/：commands.json、checks.json、manifest.json、各実行原ログ、実Godot画面。具体的生成ファイルを作業前の報告に列挙。
d46151aからの参照保存8ファイル：
tools/preview_s10_placement.py
docs/verification/s10-placement-preview/{README.md,manifest.json,comparison.png,source-comparison.png,placement-A.png,placement-B.png,ner-static-proposal.png}
参照8ファイルはそのcommitを取り込むか同bytesで保存し、採用画像を親のローカルパスに依存させない。原資料の未採用表記は当時記録として保持、今回の採用を083報告で示す。

予定外の本番path追加が必要なら理由を報告して親と照合。ログファイルの追加は検証証拠の範囲内。親担当 docs/tasks/README.md と docs/decision-log.md は変更しない。

## 禁止・保持
.scope-lock/、test/、保護検査、CI設定、project.godot、原画、既存パレット、保存形式、082本文は変更しない。削除・強制push・履歴改変・検査弱体化/省略/上限延長なし。
新規色・新ポーズ・反転・歩行コマの複製なし。採用PNGのbytesをそのまま使う。
長老[12,6]、入口[8,10]、出口[8,11]、既存台詞/宿/扉/entry_lockを保持。任意4職の旧保存移行、S11、鍵/報酬/戦闘は範囲外。

## Task1：素材と出所
- [ ] 固定原画/採用画像のhash、寸法、自然色16色以内、alpha0/255、足元47を検査する新規正負例を作る。
- [ ] owner出所の既存許可一覧にchibiの固定path+SHAだけを追加。誤path・改変原画は拒否し既存拒否例も維持。
- [ ] 再現scriptは原画読み取り専用、周縁連結薄灰色マスク・最近傍・既存自然色減色を採用記録どおりに行う。出力SHAが採用画像と違えば保存/採用を捏造しない。
- [ ] character_event（1×1）の既存台帳方式で登録。原画を別の日付フォルダへコピーして出所検査を回避しない。
- [ ] 素材strictと再生成bytes一致を実行・保存。

## Task2：既存占有と静止描画
- [ ] 先に、[8,6]占有・入口/退出/長老到達・既存人物維持・表示専用操作不変の失敗例を作る。
- [ ] room4.events にkind:npc、display_only:true、static_spriteを持つ1件を追加し既存npc占有を使う。新しい会話本文なし。
- [ ] FirstRegionViewはstatic_spriteだけ既存_object(32,48)で描き、通常歩行人物は従来経路。人物bottom=y+1、overlay bottom_row-0.5を維持。
- [ ] GameSession.interact_first_regionはdisplay_onlyをface_event/本文分岐前に除外し、向き保存・会話・082再演を発生させない。既存FirstRegion.walkable/relocate_unwalkableは変更不要の想定。
- [ ] 旧保存のプレイヤー[8,6]を安全な入口へ復帰させ、所持品・編成・既存進行不変を確認。単に表示だけ置いて人物をすり抜ける実装にしない。

## Task3：実描画・回帰・正式保存
- [ ] 082既存293条件、本文照合/負例、初入室・中断冒頭復帰・完了後非再演・古い入力拒否・通常ロード/チェックポイントを再確認。
- [ ] 512×288の実Godot画面で入室、会話中、完了後、再入室、旧保存復帰、主人公前後の重なりを撮影。静的合成を実画面の証拠にしない。欠落/境界/会話窓遮蔽を実ピクセル確認。
- [ ] main取り込み後 godot --headless --editor --import --quit を実行してから検査。実際のコマンド・終了値・warnings/errorsを記録。
- [ ] check_frozen_files.py前後、素材strict、新規集中検査、082/保存/通常入力関連回帰、R01〜R08、全CIを最終SHAで確認。段階限定検査は当時固定完成SHAで元assertion全保持、最新継続条件とは分ける。
- [ ] 通常コミット/pushしdraft PRを作成。原ログ/hash/変更全path/未確認と副作用を083報告に保存。主観の手触りは機械検査と分離。mainへはマージしない。

## Review Focus
- 占有セル上の既存保存でソフトロック/所持品消失しない。
- 表示専用NPCを決定しても新台詞/向き保存/完了後再演が起きない。
- 連打・タイトル中断・旧画面通知で082の排他が壊れない。
- 主人公前後・部品上層・会話窓で人物が消失しない。
- 静止画像を歩行シートとして矩形外参照せず、既存長老の表示/移動を変えない。

## 完了
採用画像bytes・[8,6]・既存経路保持・082互換・実Godot描画・最終CI/R8/保護確認と正式保存が揃う。全ゲーム完成や任意4職移行完了とは報告しない。
