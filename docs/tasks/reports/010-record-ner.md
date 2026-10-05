# 010 ネルの決定原文と正式原画の記録・保管の報告

## 作業前の確認

1. 取り込んだ最新main：`52c36908a146f3ca2aea964bb4400018a0945f29`。発注時に親が全20CI成功を確認した `aaaf3ceedd5f16b28e88fdb9ca85b7e3b869feae` の後に、親による010発注のSTATUS更新が入った版。最新STATUSでは010だけが実行中。008・024は統合・確認済み。作業前の未コミット変更・mainにないコミットは0件。
2. 指定ブランチをfetchし、`git show origin/<指定ブランチ>:<指定パス>` で得た実ファイルのSHA-256を照合。2枚とも依頼書と一致。取り込み先・Gitの登録内容も原本とバイト単位で一致。

| 原画 | 出所ブランチ | 出所コミット | パス | SHA-256 | バイト数 |
| --- | --- | --- | --- | --- | --- |
| 設定画（正式） | `grok/owner-2026-10-05-ner-concept` | `30ea9fd70bdb7c322034e2df08ff69dd7b70e053` | `assets/_incoming/owner-2026-10-05-grok-batch3/ner-oasis-shrine-keeper-concept.png` | `aa72aa35101e0f978c0da832ea5c31c0aca28467fd40bdd281cbab93e81c9921` | 2095857 |
| 2〜3頭身（正式・片目が緑の版） | `grok/owner-2026-10-05-oasis-shrine-keeper-chibi-eye` | `1118ecc485592ce7dddbaf509d460a851d225aa8` | `assets/_incoming/owner-2026-10-05-grok-batch3/oasis-shrine-keeper-chibi.png` | `7fb285a7c31839ff33350c328f39dfd97e94ea57a0fe6567ef862f8fb19a9aa5` | 1627646 |

3. 書き足す前の「依頼者が作画したその他の人物」と「未決事項」の全文を、基点mainから次に記録する。人物節にネルはなく、未決事項の指定2項目もなかった。

<details>
<summary>書き足す前の人物節</summary>

```markdown
### 依頼者が作画したその他の人物

- もう一組の冒険者：不可逆な侵蝕に至った仲間を元に戻す方法を探す4人組の冒険者一行として登場する。初めは太陽の神なら治せると信じている。旅を通じて、変わった身体を持つ本人の「今の自分でもう一度船乗りとして働きたい」という希望を知り、仲間で仕事や役割を分け合う関係へ変わる。最後まで4人組を保ち、不可逆な変化を奇跡で治す展開にはしない。名前、性格の細部、具体的な登場場面と一時同行の実装方法は未決。ゲストとして扱う場合も職業は変えず、戦闘の動作の絵は会話や事件の場面の演出に使う。
- 役の候補：死神は死者の国、鍛冶の親方は武器屋や特別な武器を作る人、白い精霊と森の精霊は各地の守り手、狐面の術師は案内役、狛犬の対は神殿の門番。配置は各地方を作るときに決める。
- 原画はすべて、依頼者がGrokの共有会話（https://grok.com/share/c2hhcmQtMg_2d6106a4-1817-4b58-ba1c-28eb1121196f）で生成した完全オリジナルであり、依頼者が公開とゲームでの使用を承認している。
```

</details>

<details>
<summary>書き足す前の未決事項節</summary>

```markdown
## 未決事項

Codexは、これらの事項に関わる作業に入る前に、依頼者に選択肢と推奨を示して決めてもらう。決まったら docs/experience-spec-v2.md に書き込む。


### 物語・世界

- [ ] 城と城下町の正式名称（仮称：エルヴァ城下町・エルヴァ城）

- [ ] ゲームの題名（物語の細部が決まった後に決める）
- [ ] 地方・町・村の正式名称（最後の地「夕照の都」は確定）
- [x] 洞窟の人の名前と魔物の系統（2026年10月3日採用・mainへ実装済み。名称と本文は採用データ、検査は [導入の技術記録](first-region-intro-implementation.md) に分離。2026年10月4日の名前と甲殻の姿の確認は [洞窟の人物との出会い](#洞窟の人物との出会い2026年10月3日の追加作業) を参照）
- [ ] もう一組の冒険者4人の名前・性格の細部・具体的な登場場面と一時同行の実装方法（侵蝕で戻れなくなった仲間の治療法を探す4人組という目的は確定）
- [ ] 神々・精霊・死神・鍛冶の親方などの役と配置
- [ ] 旧本編80話のうち、どの話を本筋・寄り道・使わないに分けるか
- [ ] 第2地方のオアシスの村（仮）の新住人10人の具体案（名前・人物像・台詞・初の見た目・巡回担当・役割の細部）と店の商品内容
- [ ] 魔物職解放の場所・人物・場面・条件、遺跡の未採用の登場位置・2↔3階の穴の扱い・敵追加と既存36種検査との整合・鍵の名称と受取り方・鍵付き扉の接続先（[10月4日の採用範囲と段階順](#2026年10月4日の採用範囲と段階順) の後続依存。新しい品揃え・装備規則・効果・数値の採用は含まない）

### 遊び・仕組み

- [ ] 防具の購入と装備の仕組み。最初の地方を作り終えるまでに決める。2026年9月28日、依頼者は今回の防具屋を建物・店員・会話までと決定した。

- [ ] 転移呪文・脱出道具・船・飛行手段の正式名（仮名「帰還の風」「脱出の糸」）。飛行手段の形は鷲の頭と翼を持つ空飛ぶ船に決定（2026年9月26日）
- [ ] 「周辺で戦う」を廃止し、ランダムエンカウントにそろえるか
- [ ] 敵との遭遇の頻度と、全体の難易度
- [ ] 時間配分（前半10・中盤20・後半25・最終盤5時間）でよいか
- [ ] 旧保存は職業・熟練度だけ読み込み、位置と進行は引き継がない形でよいか
- [ ] 神の加護を戦闘で使う仕組み（召喚など）を、後で追加するかどうか
- [x] 旧本編の検査ジョブは2026年9月27日に `.github/workflows/legacy-campaign.yml` の手動実行へ分離済み。2026年10月3日の決定に基づく001の文書同期で未決表記を訂正した。普段のCIには凍結受入・新ゲーム・共通機構の検査を保持している。根拠は [CI分離の記録](ci-layout-v2.md)。
- [ ] 道具の効き目の数値と値段、既存の「封印」を沈黙にまとめるかどうか
- [ ] メダルの名前・見た目・総数・配置・交換内容と、交換する人の名前・場所

### 見た目・音

- [x] メニュー画面の見た目の統一は2026年10月1日に実装済み（PR #8・#9）。濃い青の地・白い枠と文字・Noto Sans JPを対象全画面に適用し、23画面の変更前後を記録した。2026年10月3日の決定に基づく001の文書同期で、旧「今回の修正対象には含めない」を実施済みに訂正した。根拠は [メニューの色の記録](menu-colors.md)。
- [ ] メニュー画面の構成の作り直し。見た目の色・枠・字体の統一とは別で、後続の依頼で扱う。

- [ ] 探索画面を全画面にしたあと、さらに縮小表示して広く見せるか
- [ ] 仲間4人の新しい色（自然色パレット）と背景の相性の採否
- [ ] 正面向きの敵の並べ方と、ボスの大きさ
- [ ] 若い4人の正面向きの戦闘動作の絵を、どの場面で使うか
- [ ] 曲と効果音の採否（試聴はまだ）

### 公開・その他

- [ ] 公開や販売をするか。する場合は、その前に素材（スライムの一族を含む）とライセンスの記録を見直す
- [ ] CIのNode.js 20の非推奨警告への対応時期
```

</details>

## 変更したファイル

- `assets/_incoming/owner-2026-10-05-grok-batch3/ner-oasis-shrine-keeper-concept.png`：正式原画を同一パスで保管。加工・再生成なし。
- `assets/_incoming/owner-2026-10-05-grok-batch3/oasis-shrine-keeper-chibi.png`：正式原画を同一パスで保管。加工・再生成なし。
- `docs/design/characters/ner.md`：指定の冒頭文、依頼者の決定の「魔物職の解放の場面の組み立て」と「ネル」の全文を原文のまま転記。原画2枚の出所・パス・SHA-256を併記。
- `docs/experience-spec-v2.md`：「物語の大筋」の人物節に要点・話し方5項目の原文・詳細文書へのリンクを追加。「未決事項」に指定2項目を各1回追加。既存の複合未決行では、今回確定した場所・人物だけを決定済みへ同期し、ほかの依存事項を保持。
- `docs/roadmap-v2.md`：付録Bに「付録B追記：ネルの原画」を追加。正式原画2枚と途中版5ブランチ・不採用理由を記録。同名chibiは指定ブランチとSHA-256で識別。
- `docs/tasks/010-record-ner.md`：状態行のみ更新。
- `docs/tasks/reports/010-record-ner.md`：本報告書。

## 実行した検査

GodotはCIと同じ `4.7.2.stable.official.ed1daf0bf` を使用。配布ZIPのSHA-256はCI指定値 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` と一致。既設4.6.3での検査結果を成功の根拠にはしていない。

| コマンド・照合 | 結果 |
| --- | --- |
| `godot --headless --editor --import --quit` | 終了0。エラー・警告・構文エラー0件 |
| `python tools/validate_assets.py --strict` | 終了0。画像1140件・音15件・パレット3件・字体2件、問題なし |
| `python tools/run_locked_checks.py` | 終了0。R-01〜R-08すべてPASS。各verifyを変更せず実行 |
| `python tools/check_frozen_files.py`（検査前・検査後） | 終了0。保護26件すべて一致 |
| `python tools/check_progress_docs.py` | 終了0。history=26、errors=0 |
| `python tools/test_locked_check_reporting.py` | 終了0。23テスト成功 |
| `git diff --check` / `git diff --cached --check` | 終了0 |
| Pythonによる依頼書の決定本文と人物文書の抽出・文字列比較 | 全文一致。話し方5項目も体験仕様と一致 |
| 指定ブランチのblob・追加先・登録したblobのSHA-256とバイト比較 | 正式2枚一致。途中版の取り込みなし |
| `git ls-tree -rz --name-only <基点main> assets/_incoming` と各原画の比較 | 既存345枚のパス・内容すべて不変 |
| 基点mainからの `git diff --stat` とファイル許可リストの比較 | 指定7ファイルだけ。担当範囲外の差分0件 |

ローカル検査の内訳：R-01=2テスト/765assertion、R-02=5/946、R-03=2/73、R-04=1/293、R-05=2/79、R-06=2/87、R-07=A01〜A14の14件、R-08=17/2302。GUTの失敗・pending・invalidは0。検査が生成した `docs/verification/scope-lock-current.json` は実行前のバイトへ戻し、検査記録の上書きを成果物へ混ぜていない。

初回のインポートでは環境のホーム配下へ書けずデータ・設定・キャッシュの作成エラーが出た。`XDG_DATA_HOME`・`XDG_CONFIG_HOME`・`XDG_CACHE_HOME` を書込み可能な `/tmp/task010-xdg/` 以下に指定して再実行し、エラー・警告0件を確認した。GitHub Actionsの取得はCLIがForbiddenだったため、接続済みGitHubの読取りツールで実際のrun・全jobを取得して確認した。

## GitHub CI

検証対象：記録・原画の制作コミット `8c69a55e03d26add0d4d3603334efb619e9ef4c5`。2026-10-05、全20ジョブがcompleted/successで終了したことをGitHubの実結果で確認。

- [CI（3ジョブ）](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37262847711)：全て成功。
- [006 固定受入と最新回帰（17ジョブ）](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37262847743)：全て成功。

| run ID | job ID | ジョブ | 終了状態 | 結果 |
| --- | --- | --- | --- | --- |
| 37262847711 | 111613489459 | 試遊前の通常戦闘・案内・画面・復帰検査 | completed | success |
| 37262847711 | 111613489656 | 素材検査 | completed | success |
| 37262847711 | 111613489695 | Godot・凍結受入テスト | completed | success |
| 37262847743 | 111613489718 | acceptance-and-regression (latest) | completed | success |
| 37262847743 | 111613489860 | normal-input-and-rendering (latest, restart-4) | completed | success |
| 37262847743 | 111613489925 | normal-input-and-rendering (latest, restart-3) | completed | success |
| 37262847743 | 111613489956 | lifecycle-audit | completed | success |
| 37262847743 | 111613489962 | normal-input-and-rendering (latest, details) | completed | success |
| 37262847743 | 111613489993 | acceptance-and-regression (fixed) | completed | success |
| 37262847743 | 111613489999 | normal-input-and-rendering (latest, journey) | completed | success |
| 37262847743 | 111613490055 | normal-input-and-rendering (fixed, restart-2) | completed | success |
| 37262847743 | 111613490112 | normal-input-and-rendering (fixed, restart-0) | completed | success |
| 37262847743 | 111613490116 | normal-input-and-rendering (latest, restart-2) | completed | success |
| 37262847743 | 111613490125 | normal-input-and-rendering (fixed, journey) | completed | success |
| 37262847743 | 111613490126 | normal-input-and-rendering (fixed, restart-3) | completed | success |
| 37262847743 | 111613490131 | normal-input-and-rendering (latest, restart-1) | completed | success |
| 37262847743 | 111613490133 | normal-input-and-rendering (fixed, details) | completed | success |
| 37262847743 | 111613490160 | normal-input-and-rendering (latest, restart-0) | completed | success |
| 37262847743 | 111613490179 | normal-input-and-rendering (fixed, restart-4) | completed | success |
| 37262847743 | 111613490241 | normal-input-and-rendering (fixed, restart-1) | completed | success |

報告書と状態行を更新した最終提出コミットについてもpush後に全CIの終了を確認し、最終SHAとCIのURL・結果を終了報告に記載する。mainへは統合しない。

## 自己点検

1. 正式原画2枚は指定ブランチ・指定SHA-256と一致。途中版5つは一覧の記録のみで、取り込んでいない。
2. 組み立て・ネルの内容を全文そのまま保持。話し方5項目も原文一致。
3. 体験仕様に人物記録・詳細リンク・未決2項目を追加。解放回数・具体的な場面・台詞・古い記録の言葉は未決のまま。015の分け方は先取りしていない。
4. ロードマップ付録Bに正式2枚と途中版5つの理由を記録。
5. 基点mainとの差分は指定7ファイルのみ。既存原画345枚・ゲーム・データ・素材台帳・検査・保護ファイル・STATUS・ほかの依頼書と報告書は不変。
6. R-01〜R-08・保護ファイル照合成功。GitHub全20ジョブの実際の終了とsuccessを確認。

## 未達・未検証、親への引継ぎ

- **main未統合**。今回の明示指示に従い `codex/task-010-record-ner` にcommit・pushして返す。依頼書の「原画2枚がmainに入る」という統合後の条件は、親の独立確認・統合後に満たす。
- ネルのゲームへの配置・台詞制作・魔物職の解放実装は今回の対象外として未実施。人物文書冒頭にも未実装と記載。
- 記録と原画保管の指定範囲に未達なし。新たな判断事項なし。追加委譲なし。
