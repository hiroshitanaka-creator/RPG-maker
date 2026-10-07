# 047 採用済み装備名と店構成の記録報告

## 開始時の確認と追記位置

- 開始SHA・登録SHA：`c303118a709ca8b1e52e101f8964e36712ce5310`。`git fetch origin codex/task-047-record-equipment-names` のFETCH_HEADと完全一致。
- 基点main：`37fe989b147118af5294256f369fd468beff8858`。登録との差分は047依頼書のみ。親が確認した統合後34CI成功・他稼働なし・PR15との非重複を前提とし、mainを取り込み直していない。
- 指定ブランチへswitchし、開始時の未コミット変更は0、登録SHAからHEADまでの未pushコミットは0。初期checkoutの`work`も基点mainに一致していた。
- 読んだ資料：`AGENTS.md`、047依頼書、031依頼書、035依頼書・報告、036報告、`equipment-content-options.md`の036採用追記、`items-and-equipment.md`、`experience-spec-v2.md`の装備・栞と未決欄、旧職業・魔物化企画`rpg-plan-v1.md`、`monster-job-unlock.md`、素材規約・台帳、既存workflowと凍結検査器。通常ゲームの`game_session.gd`・`integrated_rules.json`と独立基盤の参照も確認した。
- 関連SKILL：catalogの`technical-writing`、同SKILLが指定する`unslop`、`verification-before-completion`を読んで適用。checkoutに`.agents/skills`はなく、環境の`/workspace/.agents`は空。追加委譲は行っていない。
- 追記位置：原本冒頭の実装範囲補足、3節の栞/MAX、4節の旧未決時点・035/036参照・30名称・店24品・未配置6品、変更記録。旧本文の全行を保持した。判断記録は今回の記録方法だけを末尾追記し、新しい採否を決めていない。

範囲外の`docs/experience-spec-v2.md:210,494,506`には、交換の品・装備名・各地方の品ぞろえを未決とする旧記録が残る。今回の2026-10-07採用分との時点差として報告し、その文書は変更していない。旧企画の尺・職業数も現行仕様へ戻していない。

## 変更した4文書と記録内容

| ファイル | 変更 |
| --- | --- |
| `docs/design/items-and-equipment.md` | 通常武器21・防具9の原文名をカテゴリ/段階付きで記録。店は各段階武器5＋防具3、全24品。blade割当てを指定3品に限定し、残6品の入手先未決を別表に記録。MAXの採用2点と未決範囲を記録。旧本文・価格・所持金を保持し、通常ゲームと未接続基盤を区別 |
| `docs/tasks/047-record-equipment-names.md` | 状態行だけを報告済みへ変更 |
| `docs/tasks/reports/047-record-equipment-names.md` | 本報告と再実行できる機械照合コード |
| `docs/decision-log.md` | 047の記録方法・理由・通常打消しによる戻し方を1件追記。既存本文はバイト不変 |

採用日時は18:08 JSTのMAX2点、18:20 JSTの1A/2A、18:22 JSTのblade Aに限定した。名称由来の属性・状態異常・特殊効果、他地方名、追加装飾、売却半額、購入即装備、価格、宝箱配置、栞約100枚、地名、題名は採用していない。MAXの名前・種類数・必要枚数・非消費・解放時期、残6品の入手先、店段階の拠点/進行対応は未決のまま。通常ゲームの名称データ・店・装備機能の実装は今回行っていない。

## 機械照合

固定登録SHAの依頼書から名称と段階を取得し、成果表と照合する。成果表から期待名を生成しない。店24品と残6品の互いに重ならない全30品への分割、MAXの箇条書きが採用2点だけであること、未決/未採用/未実装の明記、旧本文の全行保持、判断記録の旧prefix一致、自身の状態行だけの変更、全変更4文書を検査する。

repository rootで次の抽出コマンドを実行できる。検証コードとログは作業時のみ`/tmp`へ置き、既存検査や担当外文書は編集しない。

```bash
python - <<'PY'
from pathlib import Path
report = Path('docs/tasks/reports/047-record-equipment-names.md').read_text()
code = report.split('```python\n', 1)[1].split('\n```', 1)[0]
exec(compile(code, 'task047-record-check', 'exec'))
PY
```

```python
from pathlib import Path
import re
import subprocess

BASE = 'c303118a709ca8b1e52e101f8964e36712ce5310'
DESIGN = 'docs/design/items-and-equipment.md'
TASK = 'docs/tasks/047-record-equipment-names.md'
REPORT = 'docs/tasks/reports/047-record-equipment-names.md'
DECISIONS = 'docs/decision-log.md'
def git(*args):
    return subprocess.check_output(['git', *args]).decode()
def old(path):
    return git('show', f'{BASE}:{path}')
def section(text, title):
    return text.split(title + '\n', 1)[1].split('\n### ', 1)[0].split('\n## ', 1)[0]
def table(text):
    lines = [line for line in text.splitlines() if line.startswith('|')]
    assert len(lines) >= 3
    return [[cell.strip() for cell in line.strip('|').split('|')] for line in lines[2:]]

source = old(TASK)
expected = [line.split('｜') for line in source.splitlines() if '｜' in line][1:]
assert len(expected) == 10 and all(len(row) == 4 for row in expected)
assert [row[0] for row in expected] == ['剣', '刀', '斧', '拳', '短剣', '弓', '杖', '軽防具', '中防具', '重防具']
doc = Path(DESIGN).read_text()
names = table(section(doc, '### 第2地方の通常装備30名称'))
assert names == expected, '名称・カテゴリ・段階の原文不一致'
assert len({name for row in names for name in row[1:]}) == 30
shops = table(section(doc, '### 第2地方の店24品と入手場所未決の6品').split('残るblade6品', 1)[0])
expected_shops = [[f'{i}段目', expected[i-1][i]] + [row[i] for row in expected[3:]] for i in range(1, 4)]
assert shops == expected_shops and all(len(row[1:]) == 8 for row in shops)
unplaced = table(section(doc, '### 第2地方の店24品と入手場所未決の6品').split('残るblade6品', 1)[1])
expected_unplaced = [[f'{i}段目'] + [row[i] for j, row in enumerate(expected[:3]) if j != i-1] for i in range(1, 4)]
assert unplaced == expected_unplaced
shop_names = [name for row in shops for name in row[1:]]
other_names = [name for row in unplaced for name in row[1:]]
assert len(set(shop_names)) == 24 and len(set(other_names)) == 6
assert not set(shop_names) & set(other_names)
assert set(shop_names + other_names) == {name for row in expected for name in row[1:]}
max_record = section(doc, '### 2026-10-07 のMAXに関する決定')
assert [line for line in max_record.splitlines() if line.startswith('- ')] == ['- MAXを通常3段階より上の段階とする。', '- MAXは桜封の栞との交換で入手する。']
assert 'MAXの名前・種類数・必要枚数・交換時の栞の非消費・解放時期は未決です。' in max_record
for phrase in ['残るblade6品は名称だけ採用済みで、入手場所は未決です。', '店の段階がどの拠点・進行で切り替わるかは未決です。', '各品の価格・装備と敵の具体的な数値・宝箱配置は今回採用していません。', '他地方の名称・追加装飾・売却半額・購入即装備・栞約100枚・地名・題名も今回未採用です。', '名称に陽炎・蠍・刻文等が含まれていても、属性・状態異常・特殊効果を追加する決定ではありません。', '今回047で記録する名称・店構成・MAXは未実装です。', '通常の新規開始・保存I/O・転職・戦闘・UIへ全接続されていません。', '035/036の10:26 JSTの採用原文・仮値']:
    assert phrase in doc, phrase
for timestamp in ['18:08 JST', '18:20 JST', '18:22 JST']:
    assert timestamp in doc
remaining = iter(doc.splitlines())
for line in old(DESIGN).splitlines():
    assert any(current == line for current in remaining), '旧本文の削除・変更: ' + line
assert Path(DECISIONS).read_bytes().startswith(old(DECISIONS).encode()), '旧判断記録の変更'
old_task = old(TASK).splitlines()
new_task = Path(TASK).read_text().splitlines()
assert len(old_task) == len(new_task)
assert [(a,b) for a,b in zip(old_task,new_task) if a != b] == [('- 状態：未着手', '- 状態：報告済み（文書記録のみ。最終SHAの全CI結果は最終応答で補足）')]
allowed = {DESIGN, TASK, REPORT, DECISIONS}
changed = set(git('diff', '--name-only', BASE).splitlines()) | set(git('ls-files', '--others', '--exclude-standard').splitlines())
assert changed == allowed, changed
print('TASK047_RECORD_PASS: names=30 weapons=21 armor=9 shops=24 unplaced=6 MAX=2')
print('TASK047_SCOPE_PASS: files=4 task_status_only=true old_design_retained=true decision_prefix_retained=true')
```

報告書の抽出コマンドと`python /tmp/task047-check-record.py`はどちらもexit0。実出力は次のとおり。

```text
TASK047_RECORD_PASS: names=30 weapons=21 armor=9 shops=24 unplaced=6 MAX=2
TASK047_SCOPE_PASS: files=4 task_status_only=true old_design_retained=true decision_prefix_retained=true
```

## 実行コマンドと結果

| コマンド | 実結果 |
| --- | --- |
| `git fetch origin codex/task-047-record-equipment-names`、`git switch -c codex/task-047-record-equipment-names FETCH_HEAD` | exit0、登録SHA一致、開始時クリーン |
| `python tools/check_frozen_files.py` | exit0、保護26件/一致26件 |
| `python tools/validate_assets.py --strict` | exit0、画像1154・音15・パレット3・字体2、問題なし |
| `python tools/check_progress_docs.py` | exit0、`PROGRESS_DOCS: history=26 errors=0` |
| `git diff --check` | exit0、空白エラーなし |
| `godot --version` | 既定版は4.6.3。Fontconfigの書込み不可メッセージあり。既定版ではゲーム検査を行っていない |
| 公式4.7.2 ZIP取得と`sha256sum /tmp/task047-godot.zip` | exit0、`cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`。既存CI指定hash一致 |
| `/tmp/task047-bin/godot --version` | exit0、`4.7.2.stable.official.ed1daf0bf` |
| `git clone --quiet --no-hardlinks /workspace/RPG-maker /tmp/task047-qa`、登録SHAへdetach | exit0。検査の出力で担当外ファイルを上書きしないため、使い捨てcheckoutを使用 |
| `timeout 600 godot --headless --editor --path /tmp/task047-qa --import --quit` | 公式4.7.2でexit0。`/tmp/task047-import.log`全9684行を確認、SCRIPT ERROR/ERROR:/WARNING:/Parse Error 0件 |

Godot検査時だけ`PATH=/tmp/task047-bin:$PATH`、`XDG_CACHE_HOME=/tmp/task047-xdg/cache`、`XDG_DATA_HOME=/tmp/task047-xdg/data`、`XDG_CONFIG_HOME=/tmp/task047-xdg/config`、`GODOT_SILENCE_ROOT_WARNING=1`を設定した。既存の時間上限・コマンド・判定・期待値は変えていない。

`/tmp/task047-qa`の登録SHAで`python tools/run_locked_checks.py`を実行してexit0。`/tmp/task047-locked.log`と隔離先`docs/verification/scope-lock-current.json`を読み、全8件の実exit0、PASS、tests_ran=true、parser_failed=false、timed_out=false、failure_messages空を確認した。R-07はA01〜A14全PASS。R-08は17テスト・2302assertion、失敗/保留0。検査後の`python tools/check_frozen_files.py`も26/26一致。

```text
PASS R-01 (exit=0, tests_ran=True, parser_failed=False)
PASS R-02 (exit=0, tests_ran=True, parser_failed=False)
PASS R-03 (exit=0, tests_ran=True, parser_failed=False)
PASS R-04 (exit=0, tests_ran=True, parser_failed=False)
PASS R-05 (exit=0, tests_ran=True, parser_failed=False)
PASS R-06 (exit=0, tests_ran=True, parser_failed=False)
PASS R-07 (exit=0, tests_ran=True, parser_failed=False)
PASS R-08 (exit=0, tests_ran=True, parser_failed=False)
```

インポートの終了コードも`subprocess.run`で再取得し、同じ`timeout 600 godot --headless --editor --path /tmp/task047-qa --import --quit`でexit0・エラー/警告0を確認した。記録は`/tmp/task047-import-recheck.log`。ローカルR実行対象は登録SHAであり、文書変更後の最終SHAへの成功は最終CIで別途確かめる。

`gh auth status`はGH_TOKEN無効と表示した。接続済みGitHubツールのrepository読取りは成功しており、PR作成・全CI照会にはこの接続を使う。Gitのfetch/pushはCLIで行う。報告書生成の最初の一時Pythonコマンドはheredoc終端の衝突によるSyntaxErrorでexit2となった。終端を固有文字列に直してexit0で生成し、その後の機械照合もexit0。repositoryの担当外ファイルへの変更はない。

## 最終CIの扱いと未検証

本報告自身のSHAと、push/PR後に終了する同一最終SHAの全CI結果は、047依頼書の自己参照回避に従い最終応答で補う。未取得のCIを成功とは記録しない。draft PRを作成し、main直接書込み・マージ・強制pushを行わない。

今回は文書記録の検証であり、第2地方装備名・店24品・MAXのゲーム実装と動作、価格/数値調整、入手配置、手触り評価は未実施。既存ゲーム/装備基盤のCI成功を今回の未実装機能の成功と扱わない。通常新規開始・保存I/O・転職・戦闘・UIへの全接続は後続範囲。旧本編の手動workflowは今回起動していない。未決事項を今回解決する判断は不要。
