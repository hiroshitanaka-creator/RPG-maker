# 064 第4地方の採用原画11枚を保管・記録

- 作成：2026-10-10（日本時間）
- 状態：確認済み（原画11枚の保管・記録・ローカル検証済み。draft PRのCI監視・main取込は親担当）
- 対象：hiroshitanaka-creator/RPG-maker
- 依頼者の明示依頼：2026-10-10、このチャットのSentinel_c87288ee56388191a750a1c5d5cadebd
- 採用：依頼者がGrokで制作、Claudeが内容を確認、依頼者が2026-10-10に11枚を採用済み。
- 先行条件：062の城と飛行船 → 主の居場所4枚 → 今回11枚の順。先行2件がmainへ入るまで今回の実装・PR作成を開始しない。共通のdocs/roadmap-v2.mdを並列編集しない。
- Codex担当：原画取出し・記録・検証・PR作成。GPT-6 Astra／High。実行環境・正式番号・作業branch・開始main完全SHAは発注時に確認する。
- ルッカ担当：依頼書、受入、タスク表、決定ログ、最終マージとmain上の照合。

## 目的
第4地方（薄暮の花原と湖）を後で作るため、採用原画の場所・中身・用途を記録する。今回は原画保管と記録だけ。ゲームへの組込み、背景制作、通行地図、場所・敵データ、コードは追加しない。

## 重要な取出し方
元ブランチ：incoming/owner-2026-10-10-grok-region4-shrine-v2
提示先頭：bcac337（開始前に完全SHAを取得して固定）
元フォルダ：assets/_incoming/owner-2026-10-10-grok-region4/

Grokのregion4 incomingは前の枝に順に積み重ねられており、途中の履歴に不採用の部屋4枚が残る。どのregion4 incomingブランチもmerge・cherry-pickせず、最新mainから新しい作業ブランチを作り、固定先頭の下記11ファイルだけを取り出し、11枚の追加を1回のコミットにまとめる。例：git checkout <固定完全SHA> -- assets/_incoming/owner-2026-10-10-grok-region4/。ただし事前にフォルダが指定11枚だけであると確認する。
git add -fで指定11パスを追加する。incomingコミットをmainの祖先へ入れない。原画を再保存しない。
region4 incomingブランチは全て残す。削除・上書き・履歴改変は禁止。

## 全変更予定ファイル
- assets/_incoming/owner-2026-10-10-grok-region4/region4-world-map.png
- assets/_incoming/owner-2026-10-10-grok-region4/region4-lake-town-exterior.png
- assets/_incoming/owner-2026-10-10-grok-region4/region4-room-inn.png
- assets/_incoming/owner-2026-10-10-grok-region4/region4-room-item-shop.png
- assets/_incoming/owner-2026-10-10-grok-region4/region4-room-weapon-shop.png
- assets/_incoming/owner-2026-10-10-grok-region4/region4-room-shrine.png
- assets/_incoming/owner-2026-10-10-grok-region4/region4-town-residents-10.png
- assets/_incoming/owner-2026-10-10-grok-region4/region4-flower-field-enemies-4.png
- assets/_incoming/owner-2026-10-10-grok-region4/region4-lake-enemies-4.png
- assets/_incoming/owner-2026-10-10-grok-region4/region4-battle-flower-field.png
- assets/_incoming/owner-2026-10-10-grok-region4/region4-battle-lakeshore.png
- docs/roadmap-v2.md（付録Bの今回節のみ追記）
- docs/tasks/064-record-region4-art.md（Codexは状態のみ）
- docs/tasks/reports/064-record-region4-art.md
ルッカのみ：docs/tasks/README.md、docs/decision-log.md。Codexはこの2文書を編集しない。正式登録時に064を確定して全パスを照合する。

## 採用原画の提示値
以下は依頼者提示値。実バイト照合前は検証済みと扱わない。
### region4-world-map.png：世界マップの見本
- パス：assets/_incoming/owner-2026-10-10-grok-region4/region4-world-map.png
- 中身：夕方の空、一面の紫と白の花原、白い幹の林、大きな湖（奥は霧で隠れている）、湖のほとりの小さな町と船着き場
- SHA-256：f732c4ea34b63e9554eed19094b837e5b6c3ae87dce567abc90aae5898f33647
- バイト数：1726130
- 用途：第4地方の世界マップを作るときの見た目の手本

### region4-lake-town-exterior.png：湖の町の外観
- パス：assets/_incoming/owner-2026-10-10-grok-region4/region4-lake-town-exterior.png
- 中身：湖に囲まれた町。左上に宿屋、左に道具屋、中央に三日月の飾りの祠、下に武器屋、中央に噴水と花壇の広場と水場、右下に花畑と木工の作業場、右上に船着き場、左下に花のアーチの門（町の出口）
- SHA-256：8ec72d2497ded1ed1c60c80ebf8c975995aa3f9526090fabac4f39e54457012d
- バイト数：1842390
- 用途：一枚絵の背景（町の外観）

### region4-room-inn.png：宿屋の中（描き直し版）
- パス：assets/_incoming/owner-2026-10-10-grok-region4/region4-room-inn.png
- 中身：形の違う4つの寝床（普通・2倍の幅・巣・水を張った石の寝床）、左の受付の台、右の色の違う椅子の丸いテーブル、湖の見える窓。下の真ん中に幅2の入口
- SHA-256：5bbe986b3e58e7cae1ed910662c2608f8c139f429c194c464601c674368a71a1
- バイト数：901924
- 用途：一枚絵の背景（建物の中）

### region4-room-item-shop.png：道具屋の中（描き直し版）
- パス：assets/_incoming/owner-2026-10-10-grok-region4/region4-room-item-shop.png
- 中身：奥に薬瓶と乾かした花の棚と受付の台、右に鉢植え・袋・籠の台。下の真ん中に幅2の入口
- SHA-256：5b6d56b2d21ae7f1995ed42c4fe0c4b5de7914a1feb8f0085638b0001e852330
- バイト数：964613
- 用途：一枚絵の背景（建物の中）

### region4-room-weapon-shop.png：武器屋の中（描き直し版）
- パス：assets/_incoming/owner-2026-10-10-grok-region4/region4-room-weapon-shop.png
- 中身：奥に剣・槍・盾・鎧の棚、左に弓、右に大きな籠手と形の違う鎧（体に合わせて作り直した道具）、中ほどに兜と籠手の台2つ。下の真ん中に幅2の入口
- SHA-256：dd618aeea7d71776ced9a2e3616047c23b449b4a6266f52b439e4fe4daa9af6b
- バイト数：1310750
- 用途：一枚絵の背景（建物の中）

### region4-room-shrine.png：祠の中（描き直し版）
- パス：assets/_incoming/owner-2026-10-10-grok-region4/region4-room-shrine.png
- 中身：奥の中央に三日月の飾りの白い石の祭壇と三日月の掛け布、ろうそく、敷物2枚、壁ぎわの鉢植えと壺。下の真ん中に幅2の入口
- SHA-256：636ebaacaef8fcce7a0613ace584356fa040e3fd06f6de42eee4f45dfd0731f4
- バイト数：1165890
- 用途：一枚絵の背景（建物の中）

### region4-town-residents-10.png：町の住人10人
- パス：assets/_incoming/owner-2026-10-10-grok-region4/region4-town-residents-10.png
- 中身：1列に10人。体が変わって元に戻れなくなった町の人たち（羽、獣の耳と尾、背中の殻、葉、竜のうろことしっぽ、すきとおった体、光る輪郭、青白い肌など）
- SHA-256：cf79e9e12af2847759ede03aa7feb0eec9517180f3d4db704a7692daebac1fa3
- バイト数：860784
- 用途：町の住人の絵の元

### region4-flower-field-enemies-4.png：花原の敵4体
- パス：assets/_incoming/owner-2026-10-10-grok-region4/region4-flower-field-enemies-4.png
- 中身：左から、夜光の蛾、花をまとった狼、目のある花の株、蝶の群れの人影（呼び名は仮）
- SHA-256：2b9d4ba8c43cd5bc322102da479be7204305c535ab120bde0e4a18180faa9ceb
- バイト数：971134
- 用途：戦闘の敵の絵の元

### region4-lake-enemies-4.png：湖の敵4体
- パス：assets/_incoming/owner-2026-10-10-grok-region4/region4-lake-enemies-4.png
- 中身：左から、灯りのクラゲ、睡蓮のカエル、灯りを持つ霧の人影、葦の大蛇（呼び名は仮）
- SHA-256：0d1ac4099b7c27f4ee1462f982cf0ac851d2b91ac437205eeac8d245313232f9
- バイト数：889700
- 用途：戦闘の敵の絵の元

### region4-battle-flower-field.png：花原の戦闘背景
- パス：assets/_incoming/owner-2026-10-10-grok-region4/region4-battle-flower-field.png
- 中身：夕方の空、遠くの丘と白い幹の林、手前に背の低い花の花原
- SHA-256：1d45d98c0df92e9a4e3f6cdac2f9b2f20b0ecb266cbe77aa41e2cb392a26d259
- バイト数：1314939
- 用途：戦闘背景の元。原画は3:2。後の組込み時に上の空を少し切って16:9にする想定

### region4-battle-lakeshore.png：湖のほとりの戦闘背景
- パス：assets/_incoming/owner-2026-10-10-grok-region4/region4-battle-lakeshore.png
- 中身：夕方の空、霧のかかった湖（建物なし）、手前に短い草と小石の岸、左右に葦と睡蓮
- SHA-256：9e25c8f438612780b0d906fb0e15707ed002d36476e5f58240b1f8321e336716
- バイト数：1270386
- 用途：戦闘背景の元。原画は3:2。後の組込み時に上の空を少し切って16:9にする想定


## 付録B追記へ記録する内容
062と主の居場所の既存形式を実際に読んでから、既存本文を保持して新節を追加する。
- 11枚すべてのパス・取出し元ブランチ・固定完全コミット・SHA-256・バイト数・中身・用途を記載する。
- 宿屋・道具屋・武器屋・祠の4枚は描き直し版を採用した。incoming/owner-2026-10-10-grok-region4-inn、同item-shop、同weapon-shop、同shrineの最初の版は不採用・未取り込み。実在する枝名と元SHAを読み取りで確認して記録する。
- 町と部屋の入口は、大きな体や尾のある人も通れるよう、普通の2倍の幅（幅2）で依頼した。
- 採用日は2026-10-10。正式名や台詞の採用とは区別する。
- 未決：町と地方の正式名、住人10人の名前・役割・台詞、敵8体の正式名と強さ、湖の奥の場所（後半の大事な場所のため今回の絵には描いていない）。
- 2戦闘背景の16:9化は後の組込み時の想定として記録し、今回は一切切り抜かない。

## 作業前の検証
1. AGENTS.md・原画保管規則・062と主の居場所の付録B記録を読む。
2. 指定ブランチを取得し、先頭bcac337の完全SHAと対象フォルダの11枚限定を確認する。
3. 11枚を実際に閲覧し、原バイトのSHA-256とバイト数を提示表へ全件照合する。不一致時は原画を変更せず対象と実測値を報告する。
4. 元incoming枝の一覧・先頭と積層履歴を取得し、古い部屋4枚と最終版を区別する。
5. 最新mainへ先行2件が取り込まれ、関連作業が同じファイルを編集していないことを再確認する。

## 禁止
ゲームへの組込み、素材台帳追加、原画の切抜き・縮小・色調整・改名・再保存、地名・人名・物語の新規決定、region4 incomingのmerge・削除は行わない。
CI・保護・test・.scope-lock・検査契約・時間上限を変更しない。本番コード・データ・assets/registry.json・project.godotを変更しない。

## 受入・報告
- 11枚は1回の追加コミットで入り、region4 incomingコミットは今回のbranch/main履歴の祖先に含まれないことをGitで確認する。
- 部屋4枚の採用hashを照合する。武器屋は提示表の完全SHA-256 dd618aeea7d71776ced9a2e3616047c23b449b4a6266f52b439e4fe4daa9af6b を実測と比較する（依頼末尾の短縮表記dd618aeaとは文字が異なるため完全値を使用）。
- 指定フォルダは11枚限定。全原画のhash/bytes不変を確認する。
- Godot import、R-01〜R-08、check_frozen_files.pyなど既存検証を条件・時間上限不変で実行する。PR最終headの全CIを成功確認する。
- Codexは報告書と1件のdraft PRを作り親へ返す。mainへ勝手にmergeしない。
- ルッカが全差分・全CI・R8・保護不変を照合し、全条件成立後にPR経由でmainへ取り込む。main上の11hash/bytes、描き直し4枚、余分なファイルなし、incoming履歴の非混入、記録の全項目、incoming全枝残存を再確認する。
- 最終報告はPR・取込コミット、11枚のhash照合結果、記録ファイルと節、CI結果。物語の詳細はチャットへ書かない。

## 正式登録時の確定事項（本文の未確定欄より優先）
- 基点main：a6cb2ebd3d86100b20978bca3503e8ddd4a5d911。作業branch：codex/task-064-record-region4-art。
- 062はPR #34、5116756cで取込済み。PR時全74CI、取込後mainの4workflowも全成功。063はPR #35、上記mainで全74CI成功後に取込済み。R8・保護26不変も最終pushログで確認済み。063状態欄が報告済みのままでも親の受入・取込完了を優先する。
- 原画取出し元の完全SHA：bcac33726578b80d2ce3e9d0bd3678c306c6bf1f。指定フォルダtree：5a9e80566b8982a419db9f0ba45dd90d4ffc7419。親が11件限定・全サイズ一致をGitHubで確認済み。実バイトhashと実画素は実行担当が確認する。
- 原画追加11枚を1回のコミットへまとめる。そのcommitに文書を含めてもよいが、原画の追加を複数commitへ分散しない。region4 incomingの15コミットをmerge/cherry-pickしない。
- 実行場所：接続確認済みMSIのローカルCodex環境。モデルGPT-6 Astra／High、使用量影響不明。現在他Codex稼働なし。先行063と同じファイルを並行編集しない。
- 全14ファイルは本文の11PNG＋docs/roadmap-v2.md＋docs/tasks/064-record-region4-art.md（状態だけ）＋docs/tasks/reports/064-record-region4-art.md。親は先行取込後のREADME・decision-log・063状態を別途逐次更新するため、Codexはこれらを変更しない。
- 既存checkoutの変更を保全し、独立cloneで作業する。既存Godot4.7.2の実体とself-contained指定_sc_を専用checkoutへ使用できる。OS設定変更・新ソフト導入なし。初回importエラーを成功と扱わない。
- PR作成後、最終headとclean/未push0、ローカル検証・原画照合結果を報告して親へ返す。全CIの長時間待ち・マージは親担当。
