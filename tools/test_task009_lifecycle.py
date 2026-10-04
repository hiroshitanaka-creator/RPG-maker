#!/usr/bin/env python3
"""009検査器の負例。固定SHA・誤接続・不正保存受理を作業コピーで拒否する。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from check_task009_scope import FIXED, ROOT, git
from check_task009_lifecycle import validate_fixed

OUT = ROOT / 'docs/verification/task-009/negative-cases'
NPC_CELL = [20, 25]
NPC_PROBE = '''extends "res://tools/check_region2_village_regression.gd"
func _initialize() -> void:
\tcontract=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://docs/verification/task-009/continuing-contract.json")))
\tmake_base()
\tvar present := "--npc-present" in OS.get_cmdline_user_args()
\tvar cell := Vector2i(20,25)
\tvar adjacent := Vector2i(20,26)
\tvar saved := placed(0,[4,15])
\tvar room_data := FirstRegion.room(saved["overworld"])
\tcheck(contract["maps"]["exterior"]["layout"][25][20]==".","NPC正例の固定006セルは床")
\tcheck(room_data["layout"][25][20]==".","配置前後とも本番地形は床")
\tcheck(occupied(saved,cell)==present,"正例NPCの配置有無を明示確認")
\tcheck(FirstRegion.walkable(saved,cell)==not present,"配置前通行可・配置後占有不可")
\tcheck(FirstRegion.walkable(saved,adjacent),"NPC隣接セルは通行可")
\tvar game := game_for(saved)
\tcheck(walk(game,adjacent),"入口からNPC隣接セルまで本番APIで通常歩行")
\tcheck(game.export_state()["overworld"]["cell"]==[20,26],"NPC隣接への到達を位置で確認")
\tvar before := game.export_state()
\tvar moved := game.move_first_region(cell)
\tcheck((moved.is_empty() and game.export_state()==before) if present else (moved.get("kind")=="moved" and game.export_state()["overworld"]["cell"]==[20,25]),"実移動も配置前成功・配置後占有拒否で全状態保持")
\troute_log.append({"npc_cell":[20,25],"adjacent_cell":[20,26],"npc_present":present,"terrain":room_data["layout"][25][20],"walkable":FirstRegion.walkable(saved,cell),"adjacent_reached":before["overworld"]["cell"]==[20,26],"move_kind":moved.get("kind",""),"state_unchanged":game.export_state()==before})
\tfinish()
'''


def invoke(copy: Path, exe: str, name: str, *, npc_present: bool | None = None) -> dict:
    env = os.environ.copy()
    env['RPG009_EXECUTION_SHA'] = git('rev-parse', 'HEAD').decode().strip()
    env['XDG_DATA_HOME'] = str(copy / 'qa-user')
    env['XDG_CONFIG_HOME'] = str(copy / 'qa-user')
    env['XDG_CACHE_HOME'] = str(copy / 'qa-cache')
    report_file = copy / 'docs/verification/task-009/latest/runtime-checks.json'
    report_file.unlink(missing_ok=True)
    start = time.monotonic()
    try:
        script = 'task009-copy-npc-probe.gd' if npc_present is not None else 'check_region2_village_regression.gd'
        command = [exe, '--headless', '--path', str(copy), '--script', 'res://tools/' + script]
        if npc_present:command.extend(['--', '--npc-present'])
        result = subprocess.run(command, env=env,
                                capture_output=True, timeout=180)
        code = result.returncode
        text = (result.stdout + result.stderr).decode('utf-8', errors='replace')
    except subprocess.TimeoutExpired as exc:
        code = 124
        text = ((exc.stdout or b'') + (exc.stderr or b'')).decode('utf-8', errors='replace') + '\nTIMEOUT\n'
    (OUT / (name + '.log')).write_text(text, encoding='utf-8')
    report_file = copy / 'docs/verification/task-009/latest/runtime-checks.json'
    report = json.loads(report_file.read_text()) if report_file.exists() else {}
    (OUT / (name + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'exit_code': code, 'checks': report.get('checks'), 'failures': report.get('failures', []),
            'runtime_status': report.get('status'), 'npc_probe': report.get('port_route') if npc_present is not None else None,
            'elapsed_seconds': round(time.monotonic() - start, 3),
            'timeout_seconds': 180, 'parser_errors': bool(re.search(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error', text))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--godot', default='godot')
    parser.add_argument('--fixed-path', type=Path, required=True)
    args = parser.parse_args()
    exe = shutil.which(args.godot) or str(Path(args.godot).resolve())
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    try:
        validate_fixed(args.fixed_path, '552261345f68a4916ddeefad959896b44da2fcbf')
        results['wrong-fixed-sha'] = {'status': 'FAIL', 'reason': '異常SHAを受理した'}
    except ValueError as exc:
        results['wrong-fixed-sha'] = {'status': 'PASS', 'exit_code': 1, 'failure': str(exc), 'fixed_sha': FIXED}
        (OUT / 'wrong-fixed-sha.log').write_text('TASK009_LIFECYCLE_FAIL: ' + str(exc) + '\n', encoding='utf-8')
    # キャッシュも含めて独立コピー。原画・本番ファイルへは書き込まない。
    before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ['world/region2_village.json', 'scripts/game/game_session.gd', 'scripts/world/first_region.gd']}
    with tempfile.TemporaryDirectory(prefix='task009-negative-') as directory:
        copy = Path(directory) / 'project'
        shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns('.git', '.tools', '__pycache__', 'latest'))
        old_outputs = copy / 'docs/verification/task-009/latest'
        old_outputs.mkdir(parents=True)
        # 正例は後続の依頼書追加とNPC占有を含める。007本番機能の完了とは扱わない。
        (copy / 'docs/tasks/010-copy-only.md').write_text('# 作業コピー限定の後続登録正例\n', encoding='utf-8')
        data_file = copy / 'world/region2_village.json'
        original_data = data_file.read_bytes()
        (copy / 'tools/task009-copy-npc-probe.gd').write_text(NPC_PROBE, encoding='utf-8')
        (OUT / 'npc-probe-source.gd.txt').write_text(NPC_PROBE, encoding='utf-8')
        observed = invoke(copy, exe, 'npc-floor-before', npc_present=False)
        ok = observed['exit_code'] == 0 and observed['runtime_status'] == 'PASS' and not observed['parser_errors']
        results['npc-floor-before'] = {'status': 'PASS' if ok else 'FAIL', **observed}
        data = json.loads(original_data)
        fixture = json.loads((copy / 'docs/verification/task-009/continuing-contract.json').read_text())
        if fixture['maps']['exterior']['layout'][NPC_CELL[1]][NPC_CELL[0]] != '.':
            raise ValueError('NPC正例の独立固定fixtureセルが床ではありません')
        data['site']['rooms'][0]['events'] = [{'id': 'task009_copy_probe', 'kind': 'npc', 'cell': NPC_CELL, 'text': ['検査コピー限定']}]
        data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        observed = invoke(copy, exe, 'npc-floor-after', npc_present=True)
        ok = observed['exit_code'] == 0 and observed['runtime_status'] == 'PASS' and not observed['parser_errors']
        results['npc-floor-after'] = {'status': 'PASS' if ok else 'FAIL', **observed}
        observed = invoke(copy, exe, 'registered-request-and-npc-occupancy')
        ok = observed['exit_code'] == 0 and observed['runtime_status'] == 'PASS' and not observed['parser_errors']
        results['registered-request-and-npc-occupancy'] = {'status': 'PASS' if ok else 'FAIL', **observed,
                                                          'scope': '一時コピーのみ。007サービスは未実装・未検証'}
        occupancy_source = copy / 'scripts/world/first_region.gd'
        original_occupancy = occupancy_source.read_text()
        guard = 'if event["kind"] in ["recruit","rest","shop","weapon_shop","npc","story"] and event_cell(saved,event) == cell:return false'
        if original_occupancy.count(guard) != 1:raise ValueError('占有負例の注入箇所が一意ではありません')
        occupancy_source.write_text(original_occupancy.replace(guard, 'if false:return false'), encoding='utf-8')
        observed = invoke(copy, exe, 'npc-occupancy-ignored', npc_present=True)
        ok = (observed['exit_code'] == 1 and observed['runtime_status'] == 'FAIL' and not observed['parser_errors']
              and '配置前通行可・配置後占有不可' in observed['failures']
              and '実移動も配置前成功・配置後占有拒否で全状態保持' in observed['failures'])
        results['npc-occupancy-ignored'] = {'status': 'PASS' if ok else 'FAIL', **observed,
                                          'mutation': '一時コピーだけNPC占有拒否を無効化'}
        occupancy_source.write_text(original_occupancy, encoding='utf-8')
        data_file.write_bytes(original_data)
        # fixtureと実行APIの両方が同時に間違った値を取り込む自己一致を防ぐ。
        data = json.loads(original_data)
        data['definition']['region2_village_doors'][0]['to']['room'] = 2
        data_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        observed = invoke(copy, exe, 'misconnected-door')
        ok = (observed['exit_code'] == 1 and observed['runtime_status'] == 'FAIL' and not observed['parser_errors']
              and any('8本の扉リンク' in f for f in observed['failures']))
        results['misconnected-door'] = {'status': 'PASS' if ok else 'FAIL', **observed, 'mutation': '扉0の接続室1を2へ変更'}
        data_file.write_bytes(original_data)
        source = copy / 'scripts/game/game_session.gd'
        original_source = source.read_text()
        marker = '\tvar decoded:=SavedDocument.decode(document.data)'
        insertion = '\tif path.ends_with("village009_boundary.json") and document.data.get("overworld",{}).get("room") is float and document.data["overworld"]["room"]==5:return true\n'
        if original_source.count(marker) != 1:raise ValueError('保存負例の注入箇所が一意ではありません')
        source.write_text(original_source.replace(marker, insertion + marker), encoding='utf-8')
        observed = invoke(copy, exe, 'invalid-save-accepted')
        ok = (observed['exit_code'] == 1 and observed['runtime_status'] == 'FAIL' and not observed['parser_errors']
              and any('不正保存拒否' in f and '5' in f for f in observed['failures']))
        results['invalid-save-accepted'] = {'status': 'PASS' if ok else 'FAIL', **observed, 'mutation': '不正room5のload_gameをtrueへ変更'}
        source.write_text(original_source, encoding='utf-8')
    unchanged = before == {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in before}
    report = {'status': 'PASS' if unchanged and all(r['status'] == 'PASS' for r in results.values()) else 'FAIL',
              'execution_sha': git('rev-parse', 'HEAD').decode().strip(), 'production_unchanged': unchanged,
              'results': results, 'method': '別コピーの正例と故障注入。負例は終了1・実assertion失敗を要求し、timeout/parse errorは成功扱いしない。'}
    (OUT / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
