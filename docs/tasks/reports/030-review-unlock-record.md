# 030 決定記録と調査の独立レビュー

## 対象・範囲・照合手順

- レビュー対象015：`5d9a8e86fa1c7250d3884756689eb11773ecc405`。
- 基点main：`8081c9f89d2fb9305d29c230fe356f5275c8b0f5`。
- 030依頼登録・作業開始点：`174b2cd6ea54bd9d895f7e4c7aa63b8214278f4e`。対象015との差は030依頼書だけ。以下の行番号は対象015の実物に対応する。
- 手順：固定SHA間の全差分→015依頼書の決定本文と正本の文字列比較→010の既存記録・指定節の照合→verifyから保護テスト・補助関数・本番コード・データへ追跡→GitHubのrun、全job、凍結受入ジョブログを直接取得。
- 変更は030依頼書の状態行と本報告だけ。レビュー対象を修正せず、014、追加委譲、main・015ブランチへの書込み、マージは行わない。

## 判定

**PASS。差し戻しを要する指摘なし。** 決定・例・未決事項の区別、指定範囲、R-02/R-04と現行の取得判定について、015の記録・調査結果は実物と一致する。これは記録・調査の受入であり、解放イベントの実装完了や後続の対応案の承認を意味しない。

## 文書の照合結果

| 項目 | 根拠と実際の確認結果 |
| --- | --- |
| 変更範囲 | `git diff --name-only 8081c9f89d2fb9305d29c230fe356f5275c8b0f5 5d9a8e86fa1c7250d3884756689eb11773ecc405` は015指定の6文書のみ。229追加・8削除。コード・データ・素材・原画・検査・契約・CI・story-outline・他の依頼書/報告の変更なし |
| 原文 | `docs/design/monster-job-unlock.md:1` に指定の未実装表示。015依頼書の「依頼者の決定」以下から「作業内容」直前までと、新文書の本文をPythonで比較。冒頭文・表題・追加した「台詞の方向の例（未決）」見出しを除き完全一致。表・理由・未決5項目・参考文・2例も一致 |
| 例と未決 | 新文書32〜45行で未決5項目と「台詞の方向の例（未決）」を区別し、「どちらも例で、決定ではありません」を維持。採用済みの台詞として転記していない |
| 前提010 | 基点の010依頼書3行は「確認済み」。`docs/design/characters/ner.md:11-13` は分け方だけを決定へ更新し、4種類を追記、具体的な流れと台詞は未決として保持。それ以外の010の記録・原画参照は差分なし |
| 体験仕様 | `docs/experience-spec-v2.md:93,100,186,193-199,468-483` を照合。変更したH2節は「進行表」「戦闘・職業・アビリティ・魔物化」「未決事項」の3つだけ（Pythonで節ごとに比較）。本筋の節目と任意取得を区別し、既存のマスター・侵蝕・解除条件を保持。未決5項目を列挙し、旧一括/分割の未決は除去 |
| 計画書 | `docs/roadmap-v2.md:13-21` に指定の決定節、正本への参照、未実装・未決表示あり。下部の旧段階記録に残る未決より新決定が優先する旨を明記 |
| 015依頼書 | 状態行を除去して基点と比較し、本文完全一致 |

## R-02/R-04・現行コードの独立照合

| 根拠（対象015のファイル・行） | 確認結果 |
| --- | --- |
| `.scope-lock/spec.lock.json:41-44,53-56` | R-02のverifyは `test/unit/test_job_actions.gd`、R-04は `test/unit/test_monster_form.gd` をGUTで実行。015に記載されたコマンドと一致。JPと職別成功行動回数の両条件が契約にある |
| `test/unit/test_job_actions.gd:3-112` | 固定回数10/5/20、全職のJP単独不成立・両条件・保存・転職後保持・予約等の不加算・旧保存維持を検査。通常進行の地方・時期・受取りを要求していない |
| `test/unit/test_monster_form.gd:4-46` | 各魔物職ごとに新規状態を作り、基礎APIで転職・修練し、能力・技・解除を検査。最後の8は検査した職の総数。同時取得イベントの条件ではない |
| `test/support/game_test.gd:6-18,75-85`、`tools/mastery_action_fixture.gd:4-40` | `new_game()` → `GameSession.new_game()`、`master_job()` → `change_job()`・JP設定・実行動fixture・勝利という経路。`choose_job()` の進行上の取得判定を通さない。fixtureの別API `complete_state()` と実行経路を混同しない |
| `scripts/game/game_session.gd:76-131,178-179,568-613` | 旧初期状態と世界マップ型の区別がある。`change_job()` は存在・戦闘・不可逆等を確認する基礎API。通常選択は `choose_job()` → `job_unlocked()`。世界マップ型では転職全体・魔物職の共通フラグ・上級職フラグを先に判定する |
| 同 `:595-606,616-626`、`data/job_progression_v1.json:4-8` | 魔物職の共通フラグに加え、精霊系には既存の上級条件がある。015は「フラグだけで8種すべて無条件に選べる」とはしていない。既使用職等を許す598行の分岐もあるため、修練条件を毎回要求するという意味には読まない |
| 同 `:475-481` | `actor.unlocked_jobs` は `advanced` にあるIDだけ受理。新規の一般魔物職取得記録をこの配列へ単純追加する案では保存読込みが不正になる。015の注意は正しい |
| `scripts/ui/game_root.gd:1650-1667` | 未解放表示・ボタン判定・操作の `choose_job` への受渡しを確認。画面表示だけの取得制御ではない |
| `data/jobs/13_slime.json`〜`20_dragon.json` | 8定義をJSONとして読み取り。地方・節目・主撃破・受取りによる取得条件はない。各解除定義は祠・上限89・低下30・魔物技消去を保持 |
| `scripts/game/game_session.gd:906-941` | 祠での解除は取得と別。世界マップ型の場所判定と不可逆判定がある。既存仕様の変更を015は実装していない |
| 同 `:159-175,209-290`、`data/first_region_gado_scenes.json` の各 `flag` | 通常謁見で立つのは転職と北の森の許可。会話はデータ内の既存フラグを立てるが、魔物職の取得フラグは含まない |
| `world/region2_port.json:290-305`、`world/region2_village.json:102-119`、`scripts/world/first_region.gd:118-123`、`scripts/world/first_region_travel.gd`、`scripts/world/second_region_coast.gd` | 通常NPC・移動・訪問記録であり、新しい職の取得はない。村の施設準備と解放完了を区別した015の記載に一致 |
| `world/region2_ruins.json:35,73,112,151,746,763-764`、`scripts/world/region2_ruins.gd:1-28` | 各階eventsは空、接続・遭遇・ボスはfalse。地形と階段の準備のみ。新しい任意取得イベントは未実装 |

`rg -n 'monster_jobs_unlocked' scripts data world test tools` の結果は本番 `game_session.gd:595` の読取り1件だけ。新規開始・会話・訪問処理も併読し、通常の第1・第2地方でtrueを設定する処理がないことを確認した。任意に改造した保存や基礎APIによる状態注入を、通常の解放イベントとみなしていない。

015の個別取得記録・通常入口での制御・既存上級条件との経路分離は、報告の冒頭から「案・未採用・未実装」として記述されている。新しい採用決定へのすり替えはない。これらの案が実装後に全保護検査へ適合することまでは、このレビューで実証していない。

## 実行した検査・CIの直接確認

- 作業開始時 `git status --short` は空。指定ブランチを依頼登録SHAから作成し、リモートも同SHAであることを `git ls-remote` で確認。無関係の未pushコミットなし。
- 固定SHAの差分・Pythonによる原文/状態行/節照合：すべて成功。
- `git diff --check 8081c9f 5d9a8e8`：終了0。
- `python tools/check_frozen_files.py`：終了0、26件中26件一致。
- `python tools/validate_assets.py --strict`：終了0、画像1154件、音15件、パレット3件、字体2件、問題なし。
- `gh run list --commit 5d9a8e86fa1c7250d3884756689eb11773ecc405 ...` はForbidden。認証済みGitHubコネクタのGETに切替え、下表4runの `head_sha`・event・完了結果と全40jobを直接取得。全40jobがcompleted/success。

| 対象SHA | event | workflow/run | 結果 |
| --- | --- | --- | --- |
| `5d9a8e86fa1c7250d3884756689eb11773ecc405` | push | [CI / 37410261085](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37410261085) | 3/3 success |
| 同上 | push | [006 / 37410261075](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37410261075) | 17/17 success |
| 同上 | pull_request | [CI / 37410264278](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37410264278) | 3/3 success |
| 同上 | pull_request | [006 / 37410264309](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37410264309) | 17/17 success |

[pushの凍結受入ジョブ112096891175](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37410261085/job/112096891175) の実ログも取得した。checkoutの完全SHAが対象015と一致し、Godotは `4.7.2.stable.official.ed1daf0bf`。2026-10-06 03:46:19〜03:47:48 UTCにR-01〜R-08の各 `PASS (exit=0, tests_ran=True, parser_failed=False)` を確認。前後の保護26件一致も確認した。015報告にある旧SHA `e083927e...` の検査記録だけで最終SHAを成功扱いしていない。

006のmatrixでは固定側/最新側の非該当stepが既存の条件分岐でskippedになる。対応する該当側stepは成功し、jobのskipや検査変更ではない。基点からCI・検査・時間上限の差分はない。

## 確認限界と引継ぎ

- ローカルGodotは版確認だけを実行し、4.6.3とFontconfigのキャッシュ警告を確認した。指定外の版でimportやR検査を代用実行していない。今回のR全8件は上記の指定版CIログを直接確認した結果であり、030担当によるローカル再実行とは区別する。
- 015担当の一時ディレクトリ内の過去のローカルログは取得していない。その過去実行を独立に再現したとは主張しない。
- 依頼者の決定原文の照合元は登録済み015依頼書。リポジトリ外の会話原本との照合ではない。
- 新しい解放・戦闘・選択場面の実動、未決事項の採用、人間試遊、約60時間の実測は対象外・未検証。修正案の採用や014を先取りしない。
- 030の保存コミットは本報告と依頼書状態行の2ファイルのみ。その完全SHAは `git log -1 --format=%H -- docs/tasks/reports/030-review-unlock-record.md` で特定できる。自分自身のコミットSHAを本文に埋める循環を避け、push後の完全SHA・030自身の全CI結果・URLを提出メッセージに明記する。この本文の確定時点では030自身のCIは未実行で、上表の015の成功と混同しない。
- main未統合で親へ返す。追加の判断依頼・修正要求なし。
