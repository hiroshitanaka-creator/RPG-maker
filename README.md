# RPG-maker

職業・アビリティ装着・魔物化を中心にした、1周5〜6時間のオリジナルRPG企画。

現在の受入基準は[scope-lock契約](.scope-lock/spec.lock.json)。Godot 4.7.2-stable / GDScript、人間職12種＋モンスター職8種、3〜4人パーティで実装している。v1の完成や5〜6時間の実測を確認済みとはしていない。

## Windowsでの起動

```powershell
.\tools\get_godot.ps1
.\tools\launch_game.ps1
```

固定版Godotを公式配布から取得し、SHA-256を照合する。実行ファイルはGit管理対象外の`.tools/`へ置く。Godotのエディターからは`project.godot`を開いて実行できる。

タイトル画面で3人または4人を選ぶ。矢印キーまたはWASDで移動し、黄色の印でEnter・E・「調べる」を使う。編成では転職と習得技の装着ができ、セーブは探索中に行う。魔物職はマスターすると魔物化し、町の祠での解除には定義した条件と技の消失が伴う。

水路・地下回廊で最初の戦闘を終えると「周辺で戦う」で育成できる。探索中の「町へ帰還」から休息・編成を行い、「探索へ戻る」で元の位置へ戻れる。帰還中のセーブにも対応する。転職候補の能力値比較、技の効果・習得までのJP、祠での解除確認を[通常プレイの説明](docs/gameplay-progression.md)に記載した。

魔物職での戦闘と魔物専用技の実使用で侵蝕が増える。戦闘中には終了時の見込みを表示し、90へ達する戦闘開始・ターン実行の前に確認できる。[侵蝕度の規則と調整案](docs/erosion-choices.md)を参照する。

第1章クリア後は「物語を続ける」から6章案の結末まで進める。探索中の「手帳」で手掛かりを読み返し、第5章では町の教習と番人への応答の順を選べる。最後の水門では3人に堅守と響きの波を装着して担当を選ぶ。[物語の接続記録](docs/story-campaign-v1.md)に仕様と未達の物量を記載した。

本編には敵30種を配置し、後半は1地点につき3戦を行う。各戦の間に帰還・休息・編成・保存ができる。敵の行動予定と対象を見て、防御や攻撃を選べる。[敵と連戦の説明](docs/enemy-encounters-v1.md)を参照する。

必要な画像が未取込の場合は一覧を表示して探索を開始しない。未完成の代替画像を本番素材として扱わない。

現在は素材台帳37画像の取り込みと、R-01〜R-08のローカル検証が通っている。[初回の素材取り込み](docs/art-import.md)と[提供モンスター画像の取り込み](docs/user-monsters-20260919.md)に、加工手順と使用先を記載した。[開発状況](docs/development-status.md)も参照する。第1章の検証を、本編全体の完成や5〜6時間の確認とは扱わない。

## 凍結要件の検証

```powershell
. .\tools\prepare_scope_env.ps1
python tools\check_frozen_files.py
python tools\run_locked_checks.py
```

[受入テストの説明](docs/scope-lock-review.md)と[実行記録](docs/verification/scope-lock-current.json)を参照する。verifyの文字列は依頼者の入力どおり。テスト・スキーマ・起動設定を変更して合格にすることは禁止する。

`tools/check_world_data.gd`は第1章の経路と連続戦闘の追加検査であり、画像と実画面を使うR-07の代わりにはならない。現行のpre-commitフックは要件のFAILが残るcommitを止める。

## 作業前に読む資料

- [作業契約](AGENTS.md)
- [scope-lock契約](.scope-lock/spec.lock.json)
- [受入テストと保護範囲](docs/scope-lock-review.md)
- [RPG企画書 v1 — 職業・魔物化システム](docs/rpg-plan-v1.md)
- [仕様資料の位置付けと未解決事項](docs/spec-status.md)
- [素材規約](docs/asset-spec.md)
- [素材台帳](assets/registry.json)
- [提供画像5点の受領記録](docs/asset-intake-20260919.md)
- [追加画像10点の受領記録](docs/asset-intake-20260919-batch02.md)

[振り返りと回収の連鎖の設計案](振り返りと回収の連鎖_設計案_v1.md)は、企画書受領前の提案として保存している。現行の3〜4人・可変装着枠への適合は、実装データと[物語の接続記録](docs/story-campaign-v1.md)に反映した。

## 素材の検査

PythonとPillowを用意して、リポジトリ直下から実行する。

```bash
python tools/validate_assets.py --strict
```

`placeholder`の未作成素材は不足一覧に表示されるが、検査エラーにはならない。パレットが未作成の場合はパレットへの適合検査を省略する。検査の終了コード0だけで画像素材の完成とは判断しない。

GitHub Actionsの定義は[ci.yml](.github/workflows/ci.yml)。`project.godot`がない段階では、Godotのインポート検査はスキップされる。

プロジェクトがある現在は、固定版エンジンの取得、インポート、全8つのverify、保護ファイルのハッシュ照合を実行する。Godotのエラーログを終了コード0で見逃したり、空のGUT実行を成功として扱ったりしない。
