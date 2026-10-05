"""028：完全SHA固定の変更前と最新の表示・画素・素材・変更範囲を検査する。"""
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

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = 'a5f3f65dcb63e8fa86a8c68e702ebf931115cd85'
BOSS = 'ruins_sandstone_colossus'
BAD = re.compile(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|_FAIL:')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def run(command, cwd, env, target, limit):
    started = time.monotonic()
    result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=limit)
    target.write_bytes(result.stdout)
    text = result.stdout.decode('utf8', errors='replace')
    assert result.returncode == 0 and not BAD.search(text), text[-5000:]
    return dict(command=command, exit_code=result.returncode,
                elapsed_seconds=round(time.monotonic()-started, 3), timeout_seconds=limit)


def capture(path, exe, sha, phase, output, env):
    output.mkdir(parents=True, exist_ok=True)
    local = env.copy()
    local.update(TASK028_OUTPUT=str(output), TASK028_PHASE=phase,
                 TASK028_EXECUTION_SHA=sha, RPG_QA_SAVE_PREFIX='task028-'+phase)
    command = [exe, '--path', str(path), '--rendering-method', 'mobile',
               '--rendering-driver', 'vulkan', '--audio-driver', 'Dummy',
               '--script', 'res://tools/check_task028_capture.gd']
    if not local.get('DISPLAY'):
        command = ['xvfb-run', '-a', *command]
    executed = run(command, path, local, output/'capture.log', 180)
    assert b'TASK028_CAPTURE_PASS:' in (output/'capture.log').read_bytes()
    result = json.loads((output/'checks.json').read_text())
    assert result['status'] == 'PASS' and not result['failures']
    assert result['execution_sha'] == sha and result['phase'] == phase
    return executed, result


def verify_pair(before, after, output):
    for name in ['battle-1.png', 'battle-2.png']:
        assert (output/'before'/name).read_bytes() == (output/'after'/name).read_bytes(), '他敵6体の画面全バイト不変'
    assert before['layouts'].keys() == after['layouts'].keys()
    for identifier in before['layouts']:
        if identifier != BOSS:
            assert before['layouts'][identifier] == after['layouts'][identifier], '他敵の領域・配置不変: '+identifier
    old = before['images'][2]['rendered'][0]
    new = after['images'][2]['rendered'][0]
    assert old['rect'] == [124.25, 82, 91.5, 114]
    assert new['rect'] == [101.375, 25, 137.25, 171]
    assert old['region'] == new['region'] == [35, 6, 122, 152]
    ratios = [new['rect'][i]/old['rect'][i] for i in [2, 3]]
    assert ratios == [1.5, 1.5]
    assert old['rect'][1]+old['rect'][3] == new['rect'][1]+new['rect'][3] == 196
    a = Image.open(output/'before/battle-3.png').convert('RGBA')
    b = Image.open(output/'after/battle-3.png').convert('RGBA')
    # 巨像の新しい領域以外は背景・味方・UIも全画素不変。
    changed = 0
    bbox = [a.width, a.height, 0, 0]
    for y in range(a.height):
        for x in range(a.width):
            if a.getpixel((x, y)) == b.getpixel((x, y)):
                continue
            assert 202 <= x < 478 and 50 <= y < 392, '対象外の実画面画素が変化'
            changed += 1
            bbox = [min(bbox[0], x), min(bbox[1], y), max(bbox[2], x+1), max(bbox[3], y+1)]
    assert changed > 1000
    return dict(before_rect=old['rect'], after_rect=new['rect'], width_height_ratio=ratios,
                feet=[170, 196], changed_pixels=changed, changed_pixel_bbox=bbox,
                unchanged_other_enemy_layouts=len(before['layouts'])-1,
                unchanged_other_enemy_pages=2, pixels_outside_boss_unchanged=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--godot', default='godot')
    args = parser.parse_args()
    exe = str(Path(shutil.which(args.godot) or args.godot).resolve())
    head = git('rev-parse', 'HEAD').decode().strip()
    assert not git('diff', '--name-only', 'HEAD', '--', 'scripts', 'tools', 'assets', 'world', 'test', '.scope-lock', '.github', 'project.godot').strip(), '実行SHAと本番・検査器が一致'
    assert not [p for p in git('ls-files', '--others', '--exclude-standard').decode().splitlines() if p.startswith(('tools/', 'scripts/', 'assets/', 'world/'))], '未登録の本番・検査器'
    changes = git('diff', '--name-only', BASE, head).decode().splitlines()
    allowed = {'scripts/ui/rpg_battle_view.gd', 'tools/capture_task011_ruins.gd',
               'tools/check_task028.py', 'tools/check_task028_capture.gd', 'tools/check_task028_capture.gd.uid',
               'docs/decision-log.md', 'docs/tasks/028-enlarge-ruins-boss.md',
               'docs/tasks/reports/028-enlarge-ruins-boss.md'}
    assert all(p in allowed or p.startswith('docs/verification/task-028/') for p in changes), '028の変更範囲'
    tracked_assets = git('ls-tree', '-r', '--name-only', BASE, '--', 'assets').decode().splitlines()
    for name in tracked_assets:
        assert (ROOT/name).read_bytes() == git('show', BASE+':'+name), '原画・全素材不変: '+name
    old_capture = git('show', BASE+':tools/capture_task011_ruins.gd').decode()
    expected = old_capture.replace('/0.75\n', '/(rect.size/region.size)\n')
    assert (ROOT/'tools/capture_task011_ruins.gd').read_text() == expected, '011撮影の画素参照倍率のみ変更、assertionは全て保持'
    output = ROOT/'docs/verification/task-028'
    output.mkdir(parents=True, exist_ok=True)
    report = dict(base_sha=BASE, execution_sha=head, changes=changes,
                  unchanged_asset_files=len(tracked_assets), protected_and_workflow_unchanged=True)
    with tempfile.TemporaryDirectory(prefix='task028-') as directory:
        env = os.environ.copy()
        for key in ['XDG_CACHE_HOME', 'XDG_DATA_HOME', 'XDG_CONFIG_HOME']:
            folder = Path(directory)/key
            folder.mkdir()
            env[key] = str(folder)
        version = subprocess.check_output([exe, '--version'], env=env, text=True).strip()
        assert version == '4.7.2.stable.official.ed1daf0bf'
        report['engine_version'] = version
        path = Path(directory)/'before'
        subprocess.run(['git', 'worktree', 'add', '--detach', str(path), BASE], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        try:
            shutil.copy2(ROOT/'tools/check_task028_capture.gd', path/'tools/check_task028_capture.gd')
            if (ROOT/'.godot').is_dir():
                shutil.copytree(ROOT/'.godot', path/'.godot')
                for descriptor in ROOT.rglob('*.import'):
                    relative = descriptor.relative_to(ROOT)
                    if relative.parts[0] in ['assets', 'addons', 'docs'] and (path/relative).with_suffix('').is_file():
                        shutil.copy2(descriptor, path/relative)
            report['before_import'] = run([exe, '--headless', '--path', str(path), '--editor', '--import', '--quit'], path, env, output/'before-import.log', 600)
            report['before_capture'], before = capture(path, exe, BASE, 'before', output/'before', env)
        finally:
            subprocess.run(['git', 'worktree', 'remove', '--force', str(path)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        report['after_capture'], after = capture(ROOT, exe, head, 'after', output/'after', env)
    report['comparison'] = verify_pair(before, after, output)
    canvas = Image.new('RGB', (2048, 576))
    canvas.paste(Image.open(output/'before/battle-3.png'), (0, 0))
    canvas.paste(Image.open(output/'after/battle-3.png'), (1024, 0))
    canvas.save(output/'before-after.png')
    report['status'] = 'PASS'
    (output/'checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('TASK028_PASS: width=1.5 height=1.5 originals=unchanged other_enemies=unchanged')


if __name__ == '__main__':
    main()
