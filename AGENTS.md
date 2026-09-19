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
| v1 の目標尺 | 1周 5〜6 時間 |
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
