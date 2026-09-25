# 現在の実装・受入・残作業

2026年9月25日更新。このページを進捗の入口とする。各時点の失敗、提案、制作途中の記録は履歴として保存し、現在の未達へ再計上しない。

## 現在の範囲

Godot 4.7.2-stable、GDScript、512×288、32pxタイル、3〜4人、人間12職・魔物8職。正式目標は約60時間。20連作80話、49拠点の広域探索と内部、職業修練・魔物化・装着枠・人物表示・保存を接続済み。全編の自動完走を人間の約60時間の実測とは扱わない。

現在の数値と修練条件は [確定設計値](v1-final-values.md)、機械受入は [凍結契約](../.scope-lock/spec.lock.json)、追加条件の対象・保存範囲は [追加受入条件](additional-acceptance-v1.md) を参照する。

## 今回の残件対応

| 項目 | 状態 | 根拠・検証 |
|---|---|---|
| 保護台帳23件の反映とmainへの取込み | 済み | d129bb0。mainのCI 36087252136も全12ジョブ成功。`python tools/check_frozen_files.py` |
| AC-01〜AC-03の正式登録 | 改訂案の全11条件PASS、保護ファイルへの書込み承認待ち | `check_acceptance_registration.py --proposal`も11件・不一致0。契約本体はまだ8条件。登録前の不足2件は旧記録へ保持 |
| 検証結果の集計 | 追加受入の結果形式に対応 | `test_locked_check_reporting.py`。空実行、片側だけの保存、重複試行、GUTの保留を成功扱いにしない |
| 保存契約の実行方法 | 全718状態の実保存・読込みが成功、300秒上限内 | 元の経路検査はCIに保持。型付きの入力だけを再利用し、過去の結果をPASSとして流用しない |
| 過去と現在の文書整理 | 現在の入口と履歴表示を統一 | `python tools/check_progress_docs.py` |

登録後は `python tools/run_locked_checks.py` でR-01〜R-08とAC-01〜AC-03の全11件を実行する。登録済みであることと、実際のverifyが成功したことを分けて記録する。

改訂案の実行は `--spec docs/verification/acceptance-registration-proposed.json`。結果は `verification/scope-lock-proposed-current.json` に分離し、契約本体の `scope-lock-current.json` と混同しない。保存の元の通しは4人だけで約356秒かかるため、300秒の契約予算へそのまま登録する案は不成立だった。`verification/acceptance-registration-before/` にその結果を保持する。

正式契約の8条件と改訂案の11条件は、それぞれ別実行でPASS。未定義verifyはどちらも0。検証結果集計の回帰5件、文書26本、元の受入入力、保護ファイル23件、素材108件の検査も通過した。独立した実装・検証・文書整理の残件はない。残る操作は保護契約への反映と、その反映後の登録照合・再検証であり、具体的な書込み承認を必要とする。人間試遊を停止理由にしていない。

`check_save_contract.gd` は、3人・4人それぞれ359状態の型付き入力から、検証対象の実装で毎回保存・別インスタンスへの読込みを行う。入力を組む段階ではJSON用の型正規化を使わず、採取した配列型を保持する。比較後の型変換・配列ソート・比較項目の除外はしない。元の通し検査と比較器の7種類の異常検出検査も維持する。再採取は `check_save_complete.gd -- --automated-playtest --capture-save-cases`、3人は `--three-member-party --teaching-first` を追加する。

CIは [GitHub Actions](https://github.com/hiroshitanaka-creator/RPG-maker/actions/workflows/ci.yml) の対象コミットで判定する。以前の実行結果を後のコミットの検証として扱わない。今回の実結果は `verification/scope-lock-current.json`、各CIのログとartifactを参照する。

## 人間入力との境界

初見の時間、気づき、面白さ、探索・報酬・難易度・反復感は [PLAYTEST_QUEUE.md](../PLAYTEST_QUEUE.md) に分離する。全21項目はNOT_RUN。54〜66時間という判定幅と評価方法の採用は、実測・良い評価の取得を意味しない。依頼者本人の試遊を必須にしない。

提供画像の外部生成条件・他用途の許諾は提供者情報が未確認。現在の利用指示は受領済みで、公開・外部配布は対象外。これを個人利用の制作の停止理由にはしない。未提示の条件を推測して確定しない。

過去の職別行動条件の仕様衝突は採用・実装・保護台帳反映で解消済み。凍結契約への追加3条件の登録とは別件である。
