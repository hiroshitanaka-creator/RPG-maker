# 049 S2検証証拠

完成コードは99e9d03d4e095b4627b510efd4806f82276617c9。fixed049/には原結果と実行記録、fixed049-original.tar.gzには全raw/native型付き入出力と伝播13件の実fixture/logがある。archive-members-sha256.jsonで全memberを照合できる。Godotのdocument.gdv/input.bin（dictの場合）はvar_to_bytes形式。JSON/gzipの場合のinput.bin、encoded.binは生bytes。

cases.mdは独立固定期待と実結果の全112ID表。実行のargv/完全対象SHA/engine hash/時間/exit/予算/ソースhash/担当差分はfixed049/execution.json、原入力/出力hashとpath付き拒否はcodec.json。before/after保護26照合は原log。

regression/は別checkoutでのR8・装備・S1・旧142/10の原log/全文実物/以前の独立期待との全bytes一致。旧ソース保全はpreserved-source.json。最終CODEC専用CIの固定側はこのコードSHA、最新側は最終headを実checkoutする。両側は全112ケース/型/順/純粋性/進行後一般検証/非回復/移行差分を同じ条件で検証する。既存の036/038/041固定・旧入口・比較・R/asset/006回帰workflowは変更しない。

attempt-93031f9-original.tar.gzは初回106/689成功と伝播13実物。最終点検でencodeの既存metadata破損を消去してしまう欠点を修正し、正1/負5追加後に新固定コードを実行した。development-first-failure.logは開発途中の包み型不正/NaN値比較失敗の原logであり、完成証拠とは別。

再実行：`python tools/fixtures/equipment-save-codec/run_ci.py --profile fixed049 --source-sha 99e9d03d4e095b4627b510efd4806f82276617c9 --godot <照合済み4.7.2実体> --output <新規の絶対パス>`。出力先を既存原証拠へ向けない。fixture旧sourcehashのa×64はS1の固定入力として使用し、decodeのraw hashは実旧rawの55040da8837a4cae90a69de9a329137e07fd5a405670cd18f68c1e5a5b15ad8cを独立期待と照合する。

最終SHA/全CIは自己参照を避け最終応答およびdraft PR #32で補足する。
