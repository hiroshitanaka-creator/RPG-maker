# 065 世代分離・pins修正の原証拠

完成コード `7aa7c6ff6eba620b93b741d58290fb698fb7cf5e`、実行HEAD `b04ffade8faf3a722dac35d072dba50818d50cec`。最終提出SHA/CIは別に親へ引き継ぐ。保存全体・F1/S3の成功証明ではない。

- `code-fixed-sha.txt`: 現在の完成コード完全SHA。
- `assertion-map.json`: 旧112 assertionと新14条件。固定059の元AST/条件式から再照合する。
- `hashes.json`: 自身を除く提出18fileのサイズ/SHA-256、完成code inventory、オフライン復元用`pin_objects`。1128元commit/tree/必要blobをGit SHA照合する。
- `local-results.json`と`local-artifacts.tar.gz.b64`: 独立clone準備・元object欠落/復元・修正前期限同値・実30秒枠の失敗と成功・56正負・実argv/stdout/stderr・一時検証スクリプト・親CI連絡。
- `linux-results.json`と`linux-artifacts.tar.gz.b64`: 独立cloneの正常/破損pins実診断、独立ZIP、全原process/log/計測bytes。
- `windows-results.json`: 修正後NOT_RUN。旧提出の親確認結果は別欄。架空archiveなし。
- `ci-results.json`: 旧提出37の親報告41成功/9失敗/1取消と、修正後NOT_VERIFIEDを区別。API拒否の迂回なし。
- `scope-diff.json`: 20許可パス、実変更19、依頼状態行以外の不変確認。

各base64は厳格decodeでgzip/TARになる。内部`archive-manifest.json`に全regular memberのサイズ/SHA-256、directory、link target原bytes記録を持つ。全member集合・安全な相対path・サイズ/hashを再読取り照合済み。巨大checkout/.godot/engine本体は対象外。

`prior37`は初回提出37be1af2eea8f8612033607faed67e8a33eb94dbの元結果/報告/証拠。local側に元local archive、linux側に元linux archiveをそのままgzipで内包した。`preservation.json`の元base64 hashは、内包gzipをbase64へ戻して改行1つを付ければ照合できる。初回のR8・保護26・172/2178/97kill・16伝播・codecと失敗はこの元archiveへ保持し、修正後のCI成功へ転用しない。

`generation-tests`内の合成記録は専用validator fixtureであり、実診断は`valid/diagnostic-latest`と`invalid/diagnostic-latest`。破損時のFAIL/exit1/NOT_RUNを原値で保存する。親CIメッセージは当方によるCI原bytes照合とは区別する。
