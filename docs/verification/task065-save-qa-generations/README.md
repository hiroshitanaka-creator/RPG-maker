# 065 世代分離の原証拠

固定059と最新HEADを分けた診断・世代契約・原bytesの証拠。保存全体や全CI受入の成功証明ではない。

- `code-fixed-sha.txt`: 065完成コードの完全SHA。文書・証拠を含む最終提出SHAとは区別する。
- `assertion-map.json`: 旧112箇所と新11条件の対応。旧条件式・AST hash・配置先を照合する。
- `local-results.json` / `local-artifacts.tar.gz.b64`: 準備、途中版、修正前のschema格下げ誤受理、旧scopeの拒否、shallow検証、使用した一時検証スクリプト、原stdout/stderr。
- `linux-results.json` / `linux-artifacts.tar.gz.b64`: 完成コードの実診断、独立ZIP、R8、原取引、16伝播、codec、全原bytes。
- `windows-results.json`: NOT_RUNと理由。架空のWindows archiveは作らない。
- `ci-results.json`: API拒否の原記録と未確認範囲。全job数を推測しない。
- `scope-diff.json`: 20許可パスと実変更集合。`hashes.json`は自身を除く証拠・提出code/文書のサイズとSHA-256。

各base64を厳格decodeするとgzip/TARになる。内部`archive-manifest.json`に全regular memberのサイズ/SHA-256、symbolic link targetの原bytes記録、directory一覧がある。manifest自身は外側archive hashで照合する。展開前にmember名の重複、絶対パス、親参照、非regularを拒否する。付属の一時packスクリプトは書込み後に全memberを再読取りし、集合・サイズ・hashを照合した。

巨大なGit checkout・.godotキャッシュ・公式engine本体をarchiveへ複製していない。コードは完全Git SHA、engineは公式固定URL・ZIP/実行体hashで識別する。QAの原ログ・process記録・入力/出力・型付きbytes・configは保持する。16伝播の重複コピーは既存validatorが作るnegative-deltaと原resultsから全fileを復元でき、`propagation-reconstruction.json`で全16集合のhash一致を確認済み。ケース削除や証拠欠落の正規化ではない。

`generation-tests`内の合成JSONはvalidatorの専用fixtureであり、実12/27/12sampleの成功証拠とは区別する。実際の診断結果はarchiveの`diagnostic-latest`にある。過去の誤受理、原scopeの非0、CIアクセス拒否も原exitのまま保存している。

実行HEAD: `3fe9d836efcc818230bca321eca4293db44669ef`。065完成コード: `03fbc3e0f19f32b303bf53d11a84f9302cdbc29c`。059固定: `41a34ea33fe184274e6722c88cdbca2a7ffd3708`。最終提出の文書/証拠追記は別SHAで、全CIは親確認待ち。
