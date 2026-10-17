# 取得元とローカル調整

- 取得元：https://github.com/haxqer/godot-skill
- 固定コミット：`037c03e9858ae748bf66c010aeb9942dbe9b93d6`
- 元のディレクトリ：`skill/godot`
- 取得方法：`git clone --depth 1` による選択コピー（2026-10-14）。
- ライセンス：MIT。上流の著作権・許諾文は [LICENSE](LICENSE) に保持。
- 変更者：RPG-maker リポジトリの実装担当 Codex（2026-10-14）。
- 変更箇所：`SKILL.md` の description を実装・検証用途に限定し、本文冒頭に Repository Override と本リポジトリ向け適用範囲を追加。上流本文と同梱コードは変更しない。
- `agents/openai.yaml` があるスキルは、表示説明・既定プロンプトも同じ適用範囲へ変更。
- 上流の同梱コードは参考資料として保持し、製品コードへの組み込み・自動実行・他スキルの導入は行わない。

## 2026-10-17：PR42-DOC-01 のローカル案内追記

- 変更者：Codex。`SKILL.md` の「RPG-maker での適用範囲」に、`scripts/test/run_tests.py --init-mini` が検査を実行せず別の例を作るため不使用であること、上流のmini導入例を例外としないこと、既存の `python tools/run_locked_checks.py` へ誘導する案内を追記した。
- 今回の変更はローカル案内と本変更記録のみ。既存description・上流本文・同梱コード・ライセンスの変更なし。PR head `2249d0c877ebc1d79c0b303518942a7ddb277612` とのバイト照合で確認した。上流ツール全体の安全性や受入成功を認定するものではない。
