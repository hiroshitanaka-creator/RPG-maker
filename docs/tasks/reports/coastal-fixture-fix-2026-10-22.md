# coastal fixture 限定修正報告（2026-10-22）

承認済み2行を修正し、クラウド内検証は成功した。正式GitHub保存・提出SHAのCI・統合は親担当のため未実施であり、リポジトリの完了定義を満たしたとは扱わない。使用量は不明。

基点・現在HEADは `e677896d3e61b8fe8136ef60c5c76f41ad76701d`。変更は `tools/check_coastal_travel.gd` の15・57行、本報告、`docs/verification/coastal-fixture-fix-2026-10-22/` の証拠だけ。room5を `[8,7]`・上、room7を `[8,5]`・上へ既存撮影の開始位置に合わせた。その他の全バイト、check・期待値・拒否条件・ケース数・上限は不変。追跡7738ファイル中、他7737ファイルは開始時SHAと一致した。

既存Godot `4.7.2.stable.official.ed1daf0bf` を使用。ZIPは固定SHA `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` と一致し、実行体もZIP内と全バイト一致。既存検査の固定出力先を変えずに別証拠の上書きを避けるため、同じクラウド内の `/tmp/coastal-fixture-fix-2026-10-22/project` で実行した。

修正前後ともeditor importを先行し、同一Godot・同一180秒上限で境界検査を実行。前は09:15:45〜09:18:45 UTC、34行の `return_learned` 参照エラーでexit124（180.011秒）。後は09:19:17〜09:19:24 UTC、93項目PASS・exit0（7.316秒）。元ファイルと失敗原ログを保持した。

| 検証 | 結果 |
|---|---|
| editor import前後・通常headless import | 全exit0 |
| R-01〜R-08 | 全PASS・exit0。R-07は14項目、R-08は25 tests / 3046 assertions、failed/pending 0 |
| check_frozen_files.py | 前後と元作業ツリーで26/26一致・exit0 |
| assets strict | 画像1154・音15・パレット3・字体2、問題なし・exit0 |
| 港配置・船素材 | 9部屋/16扉、4方向/3桟橋/2接岸地点、PASS・exit0 |
| 航路・通常画面・第2港・村回帰・保存位置 | 91・10・935・7631・199項目、全PASS・exit0 |

修正後とR全原ログにSCRIPT ERROR・ERROR・WARNING・Parse Error・実行時リーク診断なし。収集補助がテスト名末尾の `leak` を誤検出して一度停止したが、原ログを調べて分類を訂正した。検査の再実行・改変なし。経緯と初回例外は `collection-audit-note.json` に保持した。

証拠ディレクトリの `commands.md` と各実行JSONに全19コマンド・開始終了UTC・exit・環境、同名stdout/stderr.logに原出力、`results/` に生成結果とR全原ログ162ファイル、`exact-code.diff` に正確な差分、`two-line-audit.json` と `scope-audit.json` に範囲照合を保存。`SHA256SUMS` は自己を除く証拠・修正ファイル・本報告のハッシュ一覧。元ファイルSHA-256は `24f38e348ab2fb68b460ed3a1cdbd1f97c3a5e8fa35561b8873bcfa22b59f0bf`、修正後は `e094d8105f34d63e4bb2389a5eddd84c7de629b6699c6a130851e8e38e111aa3`。

080・保存処理・親文書・本番コード・地図・NPC・会話・素材・保護検査・契約は変更なし。利用者PC、Library uploadと診断通信、commit/push/PR/mergeは使用・実施していない。通常プレイ撮影・利用者実機の確認は今回未実施。ローカル実装上の阻害点なし。正式保存・CI・統合は未実施の引渡し事項であり、拒否や成否不明の操作はない。
