# 取得元とローカル調整

- 取得元：https://github.com/TheMarco/godot-game-skills
- 固定コミット：`06c2366a90ed6f5a286583e069c8358a351696d8`
- 元のディレクトリ：`skills/godot-game-verification`
- 取得方法：`git clone --depth 1` による選択コピー（2026-10-14）。
- ライセンス：MIT。上流の著作権・許諾文は [LICENSE](LICENSE) に保持。
- 変更者：RPG-maker リポジトリの実装担当 Codex（2026-10-14）。
- 変更箇所：`SKILL.md` の description を実装・検証用途に限定し、本文冒頭に Repository Override と本リポジトリ向け適用範囲を追加。上流本文と同梱コードは変更しない。
- `agents/openai.yaml` があるスキルは、表示説明・既定プロンプトも同じ適用範囲へ変更。
- 上流の同梱コードは参考資料として保持し、製品コードへの組み込み・自動実行・他スキルの導入は行わない。

## 2026-10-17：PR42-DOC-01 のローカル案内追記

- 変更者：Codex。`SKILL.md` の「RPG-maker での適用範囲」に、同梱 `scripts/run_checks.py` の通常WARNING検出・固定Godot版照合・既定出力先の制約と、そのPASSを受入証拠にしないことを追記した。既存の検査入口・版とSHA-256の照合・警告判定・成功マーカー・件数・締切・`.tools/` と依頼書指定の原資料保存先を維持し、出力先変更だけを実行許可と解釈しない案内を明確にした。
- 今回の変更はローカル案内と本変更記録のみ。既存description・上流本文・同梱コード・ライセンスの変更なし。PR head `2249d0c877ebc1d79c0b303518942a7ddb277612` とのバイト照合で確認した。上流ツール全体の安全性や受入成功を認定するものではない。
