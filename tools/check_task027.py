"""027の通知・階段境界を実際の011検査器で検証する。fixtureは一時worktreeだけ。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BAD = re.compile(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error')
POSITIVE = '''\tif state["layer"] == "interior" and state["node"] == "region2_ruins":
\t\tvar result := Region2Ruins.move(state)
\t\tvar probe := "task027_notification_%d" % state["room"]
\t\tif state["entry_lock"] != "region2_ruins_stairs" and probe not in state["cleared"]:
\t\t\tstate["cleared"].append(probe)
\t\t\tsaved["inventory"]["potion"] += 1
\t\t\treturn {"kind":"battle","id":probe,"enemies":["slime"],"seed":1}
\t\treturn result'''
BRANCH = '\tif state["layer"] == "interior" and state["node"] == "region2_ruins":return Region2Ruins.move(state)'


def run(command, path, env, target, limit):
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=path, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=limit)
        code, raw = result.returncode, result.stdout
    except subprocess.TimeoutExpired as error:
        code, raw = 124, (error.stdout or b'') + b'\nTIMEOUT\n'
    target.write_bytes(raw)
    output = raw.decode('utf8', errors='replace')
    return dict(command=command, exit_code=code, timeout_seconds=limit,
                elapsed_seconds=round(time.monotonic()-started, 3),
                errors=[line for line in output.splitlines() if BAD.search(line)])


def verify(root, exe, sha, output):
    output.mkdir(parents=True, exist_ok=True)
    hashes = {name: hashlib.sha256((root/'tools'/name).read_bytes()).hexdigest()
              for name in ['check_task011_runtime.gd', 'capture_task011_ruins.gd', 'check_task027.py']}
    # 本番の固定・最新全検査とは別。新たな固定点・workflow・再帰呼出しは作らない。
    report = dict(execution_sha=sha, confirmation_state=True, checker_sha256=hashes, cases=[])
    with tempfile.TemporaryDirectory(prefix='task027-fixtures-') as directory:
        path = Path(directory)/'checkout'
        subprocess.run(['git', 'worktree', 'add', '--detach', str(path), sha], cwd=root,
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            # キャッシュは複製。fixtureのimportで本体・固定側のキャッシュを書き換えない。
            if (root/'.godot').is_dir():
                shutil.copytree(root/'.godot', path/'.godot')
            env = os.environ.copy()
            env['TASK011_EXECUTION_SHA'] = sha
            env['RPG_QA_SAVE_PREFIX'] = 'task011-task027-fixture'
            for key in ['XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME']:
                folder = Path(directory)/key
                folder.mkdir()
                env[key] = str(folder)
            imported = run([exe, '--headless', '--path', str(path), '--editor', '--import', '--quit'],
                           path, env, output/'import.log', 600)
            report['import'] = imported
            assert imported['exit_code'] == 0 and not imported['errors'], 'fixture import'
            originals = {name: (path/name).read_text() for name in
                         ['scripts/world/first_region.gd', 'scripts/world/region2_ruins.gd']}
            cases = [
                ('battle_notification', True, None),
                ('wrong_stair_destination', False, '階段の着地と向き'),
                ('stationary_retransition', False, '静止時に再遷移しない'),
                ('stair_inventory_damage', False, '階段直前直後は位置以外'),
                ('stair_progress_damage', False, '階段直前直後は位置以外'),
                ('stair_map_damage', False, '階段直前直後は位置以外'),
                ('invalid_notification', False, '道中の有効な通常移動・戦闘通知'),
                ('battle_at_stair', False, '階段接触の通常移動通知'),
            ]
            for name, positive, failure in cases:
                first = originals['scripts/world/first_region.gd']
                ruins = originals['scripts/world/region2_ruins.gd']
                assert first.count(BRANCH) == 1
                if positive:
                    first = first.replace(BRANCH, POSITIVE)
                elif name == 'wrong_stair_destination':
                    ruins = ruins.replace('state["cell"] = link["to_cell"].duplicate()',
                                          'state["cell"] = link["to_cell"].duplicate()\n\t\t\tif link["to_room"] == 1:state["cell"] = [22,5]')
                elif name == 'stationary_retransition':
                    first = first.replace('\tif absi(cell.x-before.x)',
                                          '\tif state["node"] == "region2_ruins" and cell == before:\n\t\tstate["room"] = (int(state["room"])+1)%4\n\t\treturn {"kind":"moved"}\n\tif absi(cell.x-before.x)')
                elif name in ['stair_inventory_damage', 'stair_progress_damage']:
                    mutation = ('saved["inventory"]["potion"] += 1' if name == 'stair_inventory_damage'
                                else 'saved["progress_flags"]["midgame_slots"] = not saved["progress_flags"].get("midgame_slots",false)')
                    first = first.replace(BRANCH, '\tif state["layer"] == "interior" and state["node"] == "region2_ruins":\n\t\tvar result := Region2Ruins.move(state)\n\t\tif state["entry_lock"] == "region2_ruins_stairs":'+mutation+'\n\t\treturn result')
                elif name == 'stair_map_damage':
                    ruins = ruins.replace('\t\t\tbreak', '\t\t\tstate["cleared"].append("task027_corrupted_progress")\n\t\t\tbreak')
                elif name == 'invalid_notification':
                    ruins = ruins.replace('\treturn {"kind":"moved"}', '\tif state["entry_lock"] != "region2_ruins_stairs":return {"kind":"task027_invalid"}\n\treturn {"kind":"moved"}')
                elif name == 'battle_at_stair':
                    ruins = ruins.replace('\treturn {"kind":"moved"}', '\tif state["entry_lock"] == "region2_ruins_stairs":return {"kind":"battle","id":"task027_wrong_stair_event","enemies":["slime"],"seed":1}\n\treturn {"kind":"moved"}')
                (path/'scripts/world/first_region.gd').write_text(first)
                (path/'scripts/world/region2_ruins.gd').write_text(ruins)
                diff = subprocess.check_output(['git', 'diff', '--', 'scripts/world'], cwd=path)
                assert diff, name
                (output/(name+'.patch')).write_bytes(diff)
                observed = run([exe, '--headless', '--path', str(path), '--script',
                                'res://tools/check_task011_runtime.gd'], path, env,
                               output/(name+'.log'), 120)
                runtime = json.loads((path/'docs/verification/task-011/latest/runtime.json').read_text())
                (output/(name+'.json')).write_text(json.dumps(runtime, ensure_ascii=False, indent=2)+'\n')
                assert not observed['errors'] and observed['exit_code'] in [0, 1], name
                assert runtime['execution_sha'] == sha and runtime['stage'] is False
                accepted = observed['exit_code'] == 0 and runtime['status'] == 'PASS' and not runtime['failures']
                assert accepted == positive, name
                if positive:
                    assert runtime['encounter_returns'] == 4, '4階で通知の開始・復帰を実行'
                else:
                    assert any(failure in line for line in runtime['failures']), name
                entry = dict(case=name, expected_accept=positive, accepted=accepted,
                             status='PASS', runtime=observed, failures=len(runtime['failures']))
                report['cases'].append(entry)
                print('TASK027_CASE_PASS: '+name, flush=True)
                if positive:
                    command = [exe, '--path', str(path), '--rendering-method', 'mobile',
                               '--rendering-driver', 'vulkan', '--audio-driver', 'Dummy',
                               '--script', 'res://tools/capture_task011_ruins.gd']
                    if not env.get('DISPLAY'):command = ['xvfb-run', '-a', *command]
                    captured = run(command, path, env, output/'battle-capture.log', 180)
                    record = json.loads((path/'docs/verification/task-011/latest/images/checks.json').read_text())
                    assert captured['exit_code'] == 0 and not captured['errors'], '通知あり撮影'
                    assert record['status'] == 'PASS' and not record['failures'] and record['execution_sha'] == sha
                    assert record['renderer'] == 'X11' and len(record['images']) == 25 and record['encounter_returns'] > 0
                    shutil.copytree(path/'docs/verification/task-011/latest/images', output/'battle-images', dirs_exist_ok=True)
                    entry['capture'] = captured
                    entry['capture_encounter_returns'] = record['encounter_returns']
                    # 最新側へ移した無遭遇条件も、stage指定では依然として拒否する。
                    stage = run([exe, '--headless', '--path', str(path), '--script',
                                 'res://tools/check_task011_runtime.gd', '--', '--stage'],
                                path, env, output/'battle-stage-rejection.log', 120)
                    state = json.loads((path/'docs/verification/task-011/latest/runtime.json').read_text())
                    assert stage['exit_code'] == 1 and not stage['errors'] and state['stage'] is True
                    assert any('無遭遇' in line for line in state['failures'])
                    entry['stage_rejection'] = stage
        finally:
            subprocess.run(['git', 'worktree', 'remove', '--force', str(path)], cwd=root,
                           check=True, stdout=subprocess.DEVNULL)
    report['status'] = 'PASS'
    (output/'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('TASK027_PASS: positive=1 negative=7 capture=25 stage_rejection=1', flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--godot', default='godot')
    args = parser.parse_args()
    exe = str(Path(shutil.which(args.godot) or args.godot).resolve())
    assert subprocess.check_output([exe, '--version'], text=True).strip() == '4.7.2.stable.official.ed1daf0bf'
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    for name in ['check_task011_runtime.gd', 'capture_task011_ruins.gd', 'check_task027.py']:
        assert (ROOT/'tools'/name).read_bytes() == subprocess.check_output(['git', 'show', sha+':tools/'+name], cwd=ROOT)
    verify(ROOT, exe, sha, ROOT/'docs/verification/task-027/fixtures')


if __name__ == '__main__':
    main()
