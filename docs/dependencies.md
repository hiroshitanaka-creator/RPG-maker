# 開発依存関係

| 依存関係 | 固定版・出典 | 用途と保存先 |
|---|---|---|
| Godot | [4.7.2-stable](https://github.com/godotengine/godot-builds/releases/tag/4.7.2-stable) | ゲームと受入テストを実行する。Windows実行ファイルは`.tools/godot/4.7.2/`。Git管理対象外。 |
| GUT | [v9.6.1](https://github.com/bitwes/Gut/releases/tag/v9.6.1)、commit `c80954f47bed74a0a2c471d472c0389f98e0a8f6` | `addons/gut/`へ公式ソースを変更せず導入。MITライセンスは`addons/gut/LICENSE.md`。 |
| Python / Pillow | ローカル実行環境のPythonとPillow | 素材の加工・検査・受入コマンドの記録。ゲームの戦闘処理はGDScriptで実行する。 |

取得時に確認するGodot ZIPのSHA-256:

- Windows: `731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953`
- Linux: `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`

公式情報の確認日: 2026年9月19日。GUTの終了コードと各CLIオプションは[公式のコマンドライン説明](https://gut.readthedocs.io/en/latest/Command-Line.html)を参照した。空実行とpendingを失敗にする補助は、公式post-runインターフェースを使う`test/support/gut_gate.gd`であり、GUT本体を改変していない。
