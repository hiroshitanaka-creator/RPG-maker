# 063 4体の主の居場所の採用原画を保管・記録

- 作成：2026-10-10（日本時間）
- 状態：未着手
- 対象：hiroshitanaka-creator/RPG-maker
- 根拠：依頼者の2026-10-10のこのチャットでの明示依頼。原画4枚の採用は依頼者が決定済み。
- 先行条件：062（城と飛行船）のPR #34が全条件を満たしてmainへ取り込まれた後に開始する。docs/roadmap-v2.mdが重なるため並列実装しない。
- 担当：Codex GPT-6 Astra／High。ルッカが依頼書・受入照合・タスク表・決定ログを担当する。
- 実行環境・正式ブランチ・開始main完全SHA：発注時に実際の接続と先行取込を確認して確定する。現在は未確定。

## 目的・範囲
後で4体の主（倒さなくてもよい強敵）との戦いを作る際、居場所の原画の場所・中身・用途をすぐ確認できるようにする。
原画の保管と文書記録だけを行う。ゲームへの組込み、背景加工、通行地図、場所データ、コード、戦闘実装、命名・物語・台詞の新規決定は行わない。

## 変更予定の全ファイル
共通原画フォルダ：assets/_incoming/owner-2026-10-10-grok-lord-places/
- lord-place-undead-archive.png
- lord-place-bird-snow-peak.png
- lord-place-spirit-frozen-lake.png
- lord-place-dragon-sky-island.png
- docs/roadmap-v2.md（付録B追記の今回節だけ）
- docs/tasks/063-record-lord-place-art.md（正式依頼書。Codexは状態欄のみ）
- docs/tasks/reports/063-record-lord-place-art.md（今回報告）
ルッカのみ：docs/tasks/README.md と docs/decision-log.md。Codexはこの2件を変更しない。
実際の変更予定は正式番号を付けて全パスを明記し、同時作業との重複を再照合する。

## 受領予定の採用原画4枚
以下は依頼者提示値。独立照合前の値を検証済みと扱わない。
### lord-place-undead-archive.png
- ブランチ：incoming/owner-2026-10-10-grok-lord-undead-archive-v2
- 先頭コミット（提示短縮値）：018df0a
- パス：assets/_incoming/owner-2026-10-10-grok-lord-places/lord-place-undead-archive.png
- SHA-256：fa64f976a79736c0084fc41eeaa5ac98b3e0c748fff3c206116b84d4a880b4af
- バイト数：1349538
- 中身：不死の主（ジーク）の部屋。遺跡の奥の隠れた書庫。真上から見た砂色の部屋で、下の真ん中に崩れた幅1の出入口、壁ぎわに本棚（一部は傾き・崩れ）、中ほどに本の開いた石の机、床に散らばった巻物と紙、奥に主が立つ空いた床とほこりの円い跡

### lord-place-bird-snow-peak.png
- ブランチ：incoming/owner-2026-10-10-grok-lord-bird-snow-peak
- 先頭コミット（提示短縮値）：7a6bebd
- パス：assets/_incoming/owner-2026-10-10-grok-lord-places/lord-place-bird-snow-peak.png
- SHA-256：fee0b810ddb04bef46126e99c4dd2a9ed6cf2f9dd1a5c69da877ab530bccacf2
- バイト数：1714744
- 中身：鳥の主の場所。第3地方の雪山の頂。下の端の中央から上る山道、雪の広場、奥の中央に段のある平らな氷の台（主が来る場所）、周りの崖と雲海、左上の遠くの火山

### lord-place-spirit-frozen-lake.png
- ブランチ：incoming/owner-2026-10-10-grok-lord-spirit-frozen-lake
- 先頭コミット（提示短縮値）：3ddfa35
- パス：assets/_incoming/owner-2026-10-10-grok-lord-places/lord-place-spirit-frozen-lake.png
- SHA-256：71dde1c4300826cf444f65f06b8907c55fe051f8ca8d89b029f3ff8b07f23ee4
- バイト数：2068322
- 中身：精霊の主の場所。第3地方の凍った湖。下の端の中央の入口から、白い厚い氷の道が湖の中央の円い氷（主が現れる場所）まで続く。歩けない薄い氷は暗い青。周りは針葉樹の森

### lord-place-dragon-sky-island.png
- ブランチ：incoming/owner-2026-10-10-grok-lord-dragon-sky-island
- 先頭コミット（提示短縮値）：f0c32ae
- パス：assets/_incoming/owner-2026-10-10-grok-lord-places/lord-place-dragon-sky-island.png
- SHA-256：bdf3eaf320df2d8b793367b43f7a5f6981e0eee1d52b1b955c3f306bd2860fe7
- バイト数：1541367
- 中身：竜の主の場所。雲の上に浮かぶ岩の島。手前の広い草地（飛行船が着く場所）、奥へ続く土の道、上に突き出た岬（その先の空に主が来る）、周りの小さな浮き岩と雲

## 不採用・未取り込み
- incoming/owner-2026-10-10-grok-lord-undead-archive
- 提示先頭：046de05
- SHA-256：06ad087c7c06d5f8595210dea0b24b4563c8c6830a6978127eac2cbff7bc0e82
- 採用版と同じファイル名。絶対にmainへ取り込まない。途中で切れた200バイトのファイルを追加・削除した履歴も含むため、先頭の正味差分と履歴を分けて調べる。
- このブランチは削除しない。比較に必要な場合以外、旧画像を開く必要はない。

## 開始前の確認
1. AGENTS.md・062記録・原画保管規則を読む。
2. 5つのincomingブランチを取得し完全SHAを固定する。mainとの共通祖先からの正味差分を確認し、このフォルダ内の1ファイルだけを追加していることを確かめる。不採用版の壊れたファイルの途中履歴を取り込まない。
3. 採用4枚と除外1枚をブランチ名・完全SHAで区別する。
4. 062のmain取込、全CI成功、今回作業との変更パス非重複を確認する。
5. 最新mainから今回専用ブランチを作り、1つのPRにまとめる。incoming各ブランチ全体を無条件にmergeせず、確認した採用PNGのGit blobだけを原本どおり取得する。追加し直す場合はgit add -fを使う。

## 文書へ残す内容
docs/roadmap-v2.md の062と同じ「付録B追記」の形で、既存本文を保持して追記する。
- 4枚のパス、元ブランチ、完全コミット、SHA-256、バイト数、中身。
- 用途は4体の主の居場所の「一枚絵の背景」の原画。どの絵にも主は描かれていない。
- 主は採用済み assets/_incoming/owner-2026-10-05-grok-batch4/ の原画から作った絵を重ねる。鳥の主の凍った岩、竜の主の宙に浮いた岩も主の絵ごと重ね、背景には描いていない。空に浮かぶ島では飛行船も重ねる前提。
- 依頼者が2026-10-10に採用。書庫は描き直し版を採用、046de05の最初の版は不採用。
- 竜の主の居場所を「空に浮かぶ岩の島」としたのはClaudeの案を依頼者が採用したもの。
- 未決：4つの居場所の呼び名（docs/design/monster-job-unlock.mdのClaude仮案は決定ではない）、雪山の頂・凍った湖・空の島への行き方、主との戦いの実装時期。
- 今回は保管・記録だけで、ゲーム実装済みと書かない。

## 検証・報告
- 4枚を実際に閲覧し、PNG原本のSHA-256とバイト数を提示値と照合する。再保存・切抜き・縮小・色調整・名前変更はしない。
- フォルダに採用4枚以外がないこと、書庫がfa64f976…b4afであること、旧版06ad087c…0e82や壊れた200バイトファイルが混入していないことを確認する。
- 既存手順・時間上限を変えず Godot import、R-01〜R-08、check_frozen_files.py を実行する。保護・CI・検査・registry・project.godotを変更しない。
- 最新PR headの全CI成功を確認するまでmainに取り込まない。失敗・待ち・未検証はそのまま報告する。
- Codexは報告書とdraft PRを作成し、mainへmergeしない。ルッカが全差分と全CI、R-01〜R-08、保護不変を確認し、タスク表・決定ログを逐次追記して、最終headの全条件成立後にPR経由で取り込む。
- main取込後は4枚全てのhash・バイト数・フォルダ件数・記録の全項目・旧版ブランチ残存を再確認する。
- 最終報告：PR、取込コミット、4枚のhash照合結果、記録ファイルと節、CI結果、不採用・未取り込みブランチ。物語の詳細はチャットへ書かない。

## 正式登録時の確定事項
- 062はPR #34、main 5116756c7b4814fd8cf5f0886983f1949a1ae6d9で取込済み。最終PR head f34efde0の全74CI成功、R8・凍結26一致。main取込後CIは親が確認継続中。
- 今回基点：5116756c7b4814fd8cf5f0886983f1949a1ae6d9。作業ブランチ：codex/task-063-record-lord-place-art。
- 実行：MSIのローカルCodex環境、GPT-6 Astra／High、使用量影響不明。062のCodex作業は終了し、同時のCodex作業はなし。061は別途承認待ちで未発注。
- 全7変更予定パス（以下以外は変更不可）：
- assets/_incoming/owner-2026-10-10-grok-lord-places/lord-place-undead-archive.png
- assets/_incoming/owner-2026-10-10-grok-lord-places/lord-place-bird-snow-peak.png
- assets/_incoming/owner-2026-10-10-grok-lord-places/lord-place-spirit-frozen-lake.png
- assets/_incoming/owner-2026-10-10-grok-lord-places/lord-place-dragon-sky-island.png
- docs/roadmap-v2.md
- docs/tasks/063-record-lord-place-art.md（状態のみ）
- docs/tasks/reports/063-record-lord-place-art.md
- 062と同じ隔離checkout方式で既存未コミットを保全。Godot等は既存実行体を使用し、OS設定変更・新インストールなし。地域4原画は今回取り込まない。
- 原画の受領元完全SHA／Git blob（親の読み取り確認、raw SHA-256は実行担当が再計算）：
  - lord-undead-archive-v2：018df0a75711e68743835a7a0045723c954870b9／d57777e3f454179ebdc98e4bede9b25119f052dc
  - lord-bird-snow-peak：7a6bebd7b6eda5ff5431d45b891ae585401c0028／66ffacedc6ab2c31dbe945b5c04ab549d4c9d852
  - lord-spirit-frozen-lake：3ddfa356650221a4dfe7a28c58b38db290ce4537／1dc052f9138aa09e09e7cf7162efc47f3f46d799
  - lord-dragon-sky-island：f0c32aeef5d97facbe70b8151968733fde50cb0a／767bac061c9e72ec336324d6447baa3c20f8c8bb
- 除外元完全SHA：046de0555195ababbf98ea0baa6a8b540c98ee4e、blob 5f37366a4236ec27e6d5aa5910f96b33570fd7fe。途中4f08671170ddb6340e432c1ad1cb897ca2f2082aで200バイトのbase64文字列を追加、2b79145b699e7110b471d2c1708fe9780896d619で削除した履歴あり。この旧履歴を取り込まない。
- タスク表・決定ログの更新はCodexに委譲しない。親が逐次処理する。PR後は最終headとclean/未push0、検証結果を報告して返し、CI監視とmergeは親が担当する。
