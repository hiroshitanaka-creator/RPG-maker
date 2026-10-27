# 080 正式保存・原本対応

原候補は `codex/task-080-original-20261027` の `d1d30b4db174952e125697a0754ea99bd3d559f3`。treeは原ZIPの候補 `524b72d4cb8682b4d77197a9934defea247a199e` と完全一致。元の378ファイルをそのまま通常commitした。元候補に親台帳2ファイルの変更はない。

統合ブランチ `codex/task-080-walking-foundation-20261027` は元候補にmain `bc5d827457e2b67164a217ce41bf7ca1a9b1e67b` を通常mergeした `c1ee2614c040aaa21f2c40af42e4797ea9684386` に、引渡し資料だけを追加する。mainのcoastal修正・原証拠・親台帳を保持。`main-integration-files.txt` は取込元mainから得た変更一覧で、担当が親台帳を編集した一覧ではない。

原ZIPはローカルでそのまま保持している。Git上では元ZIP全419項目を `original-archive-map.json` に対応付けた。payload378件は元パス、残り41項目はoriginal-package配下へ原bytesまたは可逆gzipで保存。旧ZIP2本もearlier-archivesに原bytesで保存。

原ZIP再構成（既存出力を上書きしない）：

```bash
python3 docs/verification/task-080-formal-save-20261027/rebuild_original_zip.py . /tmp/task080-original-rebuilt.zip
```

実測で164546599 bytes、SHA256 `f7d97291e6458b820303434267d2c26bfe39e229b6e8d8d8e3f75975d0fb8019` のバイト完全一致を確認。原ZIPの縮小・分割・改変ではなく、Git保存された全項目とZIP属性から同じ原本を再構成できる対応。rawログはgzip.decompressで原bytesへ戻せ、各SHAと照合できる。

検証の対象はmain統合コミット。既存検査器は変更しない。旧080の段階限定範囲検証は原候補に保存された当時の記録として保持し、最新では全378payloadの一致・main変更の全保持・親台帳一致・構造の正負例をcurrent-integrity.jsonで確認する。継続する通常入力・描画・保存は同じ080 GDScriptで再実行する。

Draft PR作成は自動承認レビューに拒否され未実行。draft-pr-denial.jsonを参照。別経路で再送しない。CI読取りは公開GitHub接続のGETで行う。正式検収・マージは親担当。
