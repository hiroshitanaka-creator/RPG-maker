# AGENTS.md — RPG-maker 作業契約

このファイルは作業を始める前に必ず読むこと。
ここに書かれた内容は、個別の依頼文より優先する。依頼文と矛盾する場合は、実装せず矛盾点を報告して止まる。どちらかを勝手に採用しない。

報告・コミットメッセージ・コメントは日本語で書く。

---

## 1. 固定事項（変更禁止）

| 項目 | 値 |
| --- | --- |
| エンジン | Godot 4.7.2-stable |
| 言語 | GDScript |
| ジャンル | 2D 見下ろし型 RPG（ドラゴンクエスト7・ファイナルファンタジー5 系） |
| 内部解像度 | 512 × 288 px |
| タイルサイズ | 32 × 32 px |
| v1 の目標尺 | 1周 約60時間（2026年9月20日に依頼者が正式変更） |
| 成果物の置き場 | この Git リポジトリのみ |

- 別エンジン、別言語、別フレームワークへの移植を実装しない。提案として書くのは可。
- 上表の値を変更する必要があると判断した場合も、実装せず提案として出す。

## 2. 成果物の扱い

- 作業の成果物はすべてこのリポジトリに置き、作業終了時に必ず commit して push する。「後で入れます」「ローカルに置きました」で終了しない。
- 画像生成機能を使った場合、生成先フォルダ（既定では `~/.codex/generated_images/` 等）に残したまま終了しない。`assets/` 配下の規定位置へ移動し、`assets/registry.json` を更新し、commit する。
- 外部での公開・ホスティング・デプロイを行わない。提案もしない。ChatGPT 上での公開、Web ホスティング、itch.io、GitHub Pages を含む。ブラウザ版の作成は v1 の対象外。
- API キー、トークン、個人情報をコミットしない。
- 生成物（`.godot/`、`export/`、`*.import` の一時物）はコミットしない。`.gitignore` を参照。

## 3. 作業前に読むファイル

- `docs/asset-spec.md` — 素材規約
- `docs/` 配下の企画書（職業・魔物化システム）
- `assets/registry.json` — 素材台帳

読んでいないファイルを読んだことにしない。存在しないファイルを参照したことにしない。

## 4. 画像の扱い

**既存素材の修正は、画像生成ではなくスクリプトで行う。**

1フレームだけの描き直し、位置のずれ、パレットの不統一、スプライトシートの再構成は、`tools/` 配下の Python スクリプト（Pillow）で決定論的に処理する。生成モデルで描き直すと、フレーム間の輪郭・配色・接地位置の整合が壊れるため、明示的な指示がない限り禁止する。

- 新規素材を生成する場合も、`docs/asset-spec.md` の解像度・パレット・透過・フレーム数に適合させる。適合しない画像をコミットしない。
- 素材が不足している場合、代わりの画像を勝手に作って埋めない。不足素材リストを出す（`python tools/validate_assets.py` が出力する）。
- 外部で作成した画像（Gemini 等）の取り込み手順は `docs/asset-spec.md` の「外部素材の取り込み」に従う。

## 5. 完了の定義

次をすべて満たしたときだけ「完了」と書く。

1. CI（`.github/workflows/ci.yml`）が緑である。
2. 依頼された項目がすべて実装済みである。または未達の項目が明示的に列挙されている。
3. 変更が commit され、push されている。

次は禁止する。

- 未実装・未検証の項目を「完了」「実装しました」と書く。
- 実行していないテストやコマンドの結果を書く。
- 「動作するはずです」を検証の代わりにする。
- 依頼された機能を「MVP」「簡略化」「安全のため」を理由に無断で削る。削る必要があるときは、削った項目・理由・復旧に必要な条件を報告する。
- 仕様の空欄を、報告せずに自分の判断で埋める。

## 6. 報告形式

作業終了時に次を出す。前置き、意気込み、自己評価は不要。

- 変更したファイル一覧
- 実行したコマンドとその結果（CI の結果を含む）
- 未達・未検証の項目
- 判断が必要な事項（あれば3件以内）

## 7. コミット

- 作業単位ごとに1コミット。1行目に日本語の要約を書く。
- 複数の無関係な変更を1コミットに混ぜない。

## 8. 検証コマンド

```bash
# 素材の検査（不足素材リストもここに出る）
python tools/validate_assets.py --strict

# Godot プロジェクトのインポート検査（Godot がある環境で）
godot --headless --import
```

<!-- BEGIN SCOPE-LOCK -->
## Scope discipline (enforced, not advisory)

`.scope-lock/spec.lock.json` holds the frozen requirement list for this
repository. It is a contract, not a starting point for negotiation.

- Every requirement ships. None may be dropped, deferred, narrowed, stubbed,
  or re-interpreted to fit what currently works.
- A requirement is done only when its `verify` command exits 0. Your own
  judgement that it is finished carries no weight.
- Never edit `spec.lock.json` or any file under `protected_paths`. Those writes
  are blocked at the tool level.
- Placeholders (TODO, FIXME, `pass`, NotImplementedError, mock returns, skipped
  tests) mean the dependent requirement is not done, whatever the tests say.
- If a requirement genuinely cannot be met, write
  `.scope-lock/escalations/open/<short-id>.md` with what you tried and the
  evidence, then continue with other requirements. Do not implement a reduced
  version and do not stop to ask.
- Do not end the turn while any verify command fails. Expect a long run.

Check status with: `python3 D:\Codex\.codex\scope-lock\scripts/verify_cli.py`
<!-- END SCOPE-LOCK -->

## 停止条件

- 人間プレイテストの必要性を、作業停止の理由にしてはならない。
  該当項目は PLAYTEST_QUEUE.md に追記し、次の独立タスクへ進むこと。
- 停止してよいのは、残タスクを依存関係で再分類した結果、
  独立して着手可能なタスクが実際にゼロの場合のみ。
- 停止する場合は、残タスク一覧と各タスクのブロック理由を
  明示すること。「人間の確認待ち」だけでは理由として不十分。

## 受入条件の書き方

- 新規タスクの受入条件は、必ず機械検証可能な形で記述する。
- 主観判断が必要なものは受入条件に含めず、
  PLAYTEST_QUEUE.md に分離する。

## 依頼者の初見体験と目標変更

- 2026年9月20日、依頼者は「60時間を正式目標に戻す」と回答した。従来の5〜6時間は過去の目標であり、現在の完成条件には使わない。
- 短い版やMVPの完成を、60時間のゲームを作るための条件にしない。目標尺の実測と、機械検証の成功を区別する。
- 依頼者本人の初見体験を温存する。通常の進捗報告には物語の解答・結末・未体験の展開を含めず、検査結果・不具合・残作業を伝える。
- 目標尺以外の変更禁止事項と、R-01〜R-08の保護テストは維持する。今回の目標変更を、機能削減やテストの弱化に利用しない。

## 2026年9月25日の承認済み改訂

- 依頼者の「行動回数条件を採用して契約・実装・テストを改訂して下さい」に基づき、R-02・R-04をJPと職別成功行動回数の両条件へ改訂する。この改訂に必要な保護テスト・共有入力・凍結ハッシュの更新を認め、旧版と改訂理由を残す。
- 実績システムの禁止は外部実績・独立した実績一覧に適用する。今回採用した職業修練の回数管理はその禁止に含めない。
- 盗賊の盗み成功10回、僧侶の蘇生5回、獣系の状態異常付与20回を保持する。旧保存の取得済みマスターは維持するが、未記録の行動回数は補完しない。
- 暫定設計値の最終確定も依頼者が指示した。確定した設計値と、未実施の人間評価・約60時間の実測を区別する。
- 続く「人間試しプレイ以外のタスクを完了させて下さい」に対し、提示済み残件であるAC-01〜AC-03のscope-lock正式登録を準備する。既存8条件・保護テスト・固定入力・数値・予算は維持し、登録前の契約を保存する。自動承認レビューから具体的な契約ファイルへの書込み承認を求められたため、その操作は確認中。進捗文書の整理と改訂案の検証は独立して続ける。

## 2026年9月25日の承認済み改訂（世界マップ攻略型）

- 依頼者は、ゲームの形を `docs/experience-spec-v2.md`（世界マップ攻略型）へ変えることを承認した。ゲームの形・進行・拠点・移動・転移に関する判断では、この仕様書を `docs/` 配下の他の企画書・記録より優先する。
- 旧本編（章の選択による進行、長編80話、町のメニューからの「世界地図へ」「本編へ」）は凍結した素材として扱う。削除しないが、この構造の上に新しい機能を追加しない。
- 仕様書の「体験の核」のうち機械で確かめられる部分は受入条件にし、手触りの評価は `PLAYTEST_QUEUE.md` に分ける。
- 作業は依頼文ごとに1段階ずつ行う。依頼文の範囲外の段階（次の地方、転移呪文、R-07の差し替えなど）へ自分から進まない。この規則は「停止条件」より優先する。
- 仕様書の未決事項（地名、呪文名、物語の大筋、時間配分など）を自分の判断で埋めない。仮名は仮名のまま使う。
- R-01〜R-08は維持する。R-07の差し替えは、受入テストを依頼者が確認した後に、依頼者が `spec.lock.json` で行う。
- 市販ゲームの地名・呪文名・マップ配置・画像・音・コードを使わない。参考にするのは遊びの形だけとする。
- `addons/gut/gui/GutSceneTheme.tres` のフォント参照から古いUIDを除いた1行の変更は、依頼者が承認した資源参照の修正である。テストロジック・アサーション・結果判定・警告検出は変更しておらず、非交渉事項の「GUTの改変による成功」には当たらない。GUTのそれ以外の変更は、引き続き禁止する。
