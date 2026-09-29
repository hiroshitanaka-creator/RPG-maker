# 4人×12職の侵蝕模様：反映前の確認

2026年9月29日。平常・兆候（30〜59）・変異（60〜89）の比較。

**本番への反映は未実施。スプリント4は未完了。** 元の衣装を変えず、人物別の発光色を重ねた合成画像41シートが現行の色数上限を1色超える。規約変更の承認を待っている。以下は準備した画像を一時的に読み込んだ撮影であり、通常のゲームに接続済みという意味ではない。

## 一覧と画面

| 人物 | 戦闘・12職×3段階 | 歩行・12職×3段階×4方向 |
| --- | --- | --- |
| カイナ | [戦闘](pc_01-battle.png) | [歩行](pc_01-walk.png) |
| リオネ | [戦闘](pc_02-battle.png) | [歩行](pc_02-walk.png) |
| ハルド | [戦闘](pc_03-battle.png) | [歩行](pc_03-walk.png) |
| スイナ | [戦闘](pc_04-battle.png) | [歩行](pc_04-walk.png) |

- [平原](mixed-1-plains.png)：カイナ平常、リオネ兆候、ハルド変異、スイナ不可逆。
- [洞窟](mixed-2-cave.png)：カイナ変異、リオネ平常、ハルド兆候、スイナ変異。
- [死者の国](mixed-3-underworld.png)：カイナ不可逆、リオネ変異、ハルド兆候、スイナ平常。

一覧の各行はGodotの標準ウィンドウ1024×576から撮影し、拡大縮小せず縦につないだ。戦闘は内部72px・標準ウィンドウ144px、歩行は内部32×48px・標準ウィンドウ64×96px。画像ビューアの「100%」で標準ウィンドウと同じ大きさになる。チャット内の自動縮小は表示側の処理。

戦闘一覧は待機、歩行一覧は各方向の歩行コマを掲載した。攻撃・被弾と歩行の残りのコマも作成し、別の機械検査で確認した。混在画面は本番の戦闘描画と段階の印を使用。検査用の保存状態から撮影しており、物語上の到達を示すものではない。不可逆90以上は採用済みの魔物姿の例。

## 模様の位置と色

元の絵から顔・肩・肘・手首の位置候補を求め、職業・人物・動作ごとの座標を `assets/source_records/erosion-costume-anchors.json` に記録した。武闘家の突き出した腕、薬師の小瓶、僧侶や魔法使いの杖、吟遊詩人の楽器などに合わせて補正した。`pc_0N-anchor-review.png` は位置確認用の線を重ねた記録。

兆候は片腕と頬、変異は両腕・首・頬。鎧や兜・帽子では、同じ身体部位に当たる衣装の上にも描く。目を避けるため、頬の模様は記録した顔領域の下側45%へ制限した。後ろ向きは見えない頬を描かず、腕と首を示す。模様は元の不透明部分に収める。

変異の輪郭光は戦闘2画素・歩行1画素で、元の輪郭の内側に置く。人物の大きさ・透過・足元を変えない。カイナは水色、リオネは赤茶、ハルドは淡い金、スイナは紫で、中心は白に近い共通色。すべて既存の natural.gpl から選び、新色は追加していない。

採用済みのカイナ戦士の模様・合成画像8枚はそのまま使う。その他の衣装も原本のPNGは変更せず、模様を重ねる場所の外側は画素単位で保持する。

## 検査結果の区別

- `preparation-checks.json`：192合成シート・1,440コマの寸法、二値透過、接地、部位の描画、変異の輪郭光、兆候から変異への範囲の増加、原本と模様外の画素保持は成功。
- `board-checks.json`：下書きの撮影296項目が成功。撮影した行の画素と一覧の画素も一致。
- `mixed-checks.json`：下書き接続での保存状態・職業・段階・印など36項目が成功。
- `prepared-color-limits.json`：41シートの色数超過は未解決。最大は戦闘21色・歩行17色。**この項目は合格にしていない。**
- 本番の台帳、人物素材の接続、素材規約、共通パレットは開始時の `decffbd443b14e65a43d09b3e806cdf3a92382ad` から未変更。
- `python tools/validate_assets.py --strict`：本番の673画像・14音・3パレット・2字体が成功。未登録の下書きの色数超過を合格としたものではない。
- `python tools/check_frozen_files.py`：保護対象26件が一致。
- `python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .`：R-01〜R-08すべて成功。R-07は52.0秒、R-08は17.6秒。
- Godotのインポートと撮影が終了コード0で完了。CIの終了結果は、この差分のpush後に確認する。

## 再現コマンド

PythonではPillow・NumPy・SciPy、撮影では固定版Godotを使用する。

```powershell
. ./tools/prepare_scope_env.ps1
python tools/prepare_erosion_costume_anchors.py
python tools/build_erosion_costumes.py
python tools/check_erosion_costume_preparation.py
godot --headless --editor --import --quit
godot --path . --rendering-method gl_compatibility --script res://tools/capture_erosion_costume_boards.gd -- --draft
godot --path . --rendering-method gl_compatibility --script res://tools/capture_erosion_mixed.gd -- --draft
```

## 残作業と停止理由

色数の扱いの決定後、合成素材を本番へ登録し、通常の素材参照で撮影・検査・CIを行う。未承認の上限変更や、指定の発光色を職業ごとに変える処理は実施していない。

[承認案](../../proposals/erosion-composite-colors.md)は、侵蝕の合成だけ戦闘21色・歩行17色を認める案を推奨する。元衣装と発光色を両方保てるため。もう一つは現行上限を保ち、光の縁の色を衣装ごとの既存色へ寄せる案。どちらもGitで戻せる。

確認が必要な根拠は `AGENTS.md` の「テスト・契約ファイル・保護ファイルの変更」は実行前に確認する規則と、`docs/asset-spec.md` の戦闘20色・歩行16色の規約。依存しない位置調整・一覧・混在画面の準備を終えてから、この判断のために止める。スプリント5には進まない。
