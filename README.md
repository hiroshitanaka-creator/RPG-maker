# RPG-maker

職業・アビリティ装着・魔物化を中心にした、1周5〜6時間のオリジナルRPG企画。

## 作業前に読む資料

- [作業契約](AGENTS.md)
- [RPG企画書 v1 — 職業・魔物化システム](docs/rpg-plan-v1.md)
- [仕様資料の位置付けと未解決事項](docs/spec-status.md)
- [素材規約](docs/asset-spec.md)
- [素材台帳](assets/registry.json)
- [提供画像5点の受領記録](docs/asset-intake-20260919.md)

[振り返りと回収の連鎖の設計案](振り返りと回収の連鎖_設計案_v1.md)は、企画書受領前の提案として保存している。4人固定・可変の装着枠・侵蝕度システムへの適合修正は未実施。

## 素材の検査

PythonとPillowを用意して、リポジトリ直下から実行する。

```bash
python tools/validate_assets.py --strict
```

`placeholder`の未作成素材は不足一覧に表示されるが、検査エラーにはならない。パレットが未作成の場合はパレットへの適合検査を省略する。検査の終了コード0だけで画像素材の完成とは判断しない。

GitHub Actionsの定義は[ci.yml](.github/workflows/ci.yml)。`project.godot`がない段階では、Godotのインポート検査はスキップされる。
