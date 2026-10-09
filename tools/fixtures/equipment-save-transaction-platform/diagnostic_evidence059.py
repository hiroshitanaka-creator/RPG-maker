#!/usr/bin/env python3
"""全原証拠を保持したまま、059診断だけを独立保存して失敗内訳を注記する。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def collect(area, destination, source_sha, code_sha):
    area = Path(area).resolve()
    destination = Path(destination).resolve()
    if destination == area or area in destination.parents:
        raise ValueError('独立証拠の保存先は元診断directoryの外')
    destination.mkdir(parents=True, exist_ok=False)
    errors = []

    def read(relative):
        try:
            return json.loads((area / relative).read_bytes())
        except (OSError, ValueError) as exc:
            errors.append(relative + ': ' + type(exc).__name__ + ': ' + str(exc))
            return {}

    execution = read('execution.json')
    if execution.get('source_sha') != source_sha or execution.get('code_sha') != code_sha:
        errors.append('executionのsource/code完全SHA不一致または欠落')
    if execution.get('status') != 'PASS':
        errors.append('execution status=' + str(execution.get('status')))
    errors.extend(str(value) for value in execution.get('failures', []))
    commands = []
    setup = []
    for row in execution.get('setup', []) + execution.get('commands', []):
        value = {key: row.get(key) for key in ['label', 'exit_code', 'seconds', 'budget_seconds', 'exception', 'timed_out', 'record_error']}
        value['stopped'] = row.get('supervision', {}).get('stopped')
        (setup if row in execution.get('setup', []) else commands).append(value)
        if value['exit_code'] != 0 or value['stopped'] is not True:
            errors.append(str(value['label']) + ': ' + json.dumps(value, ensure_ascii=False))
    if [row['label'] for row in commands] != ['capture-tests', 'scope059', 'capture059', 'baseline058', 'measurements']:
        errors.append('元5診断の実行記録が揃っていない')
    if execution.get('schema') == 2 and [row['label'] for row in setup] != ['baseline-checkout']:
        errors.append('058 checkout準備の実行記録が揃っていない')
    tests = {}
    for label in ['capture-tests', 'capture059']:
        value = read(label + '/tests.json')
        failed = [row for row in value.get('cases', []) if row.get('status') != 'PASS']
        tests[label] = dict(status=value.get('status'), count=len(value.get('cases', [])), failures=failed)
        if value.get('status') != 'PASS' or failed:
            errors.append(label + ': ' + json.dumps(tests[label], ensure_ascii=False))
    measurements = read('measurements/diagnostics.json')
    if measurements.get('status') != 'PASS':
        errors.append('measurements: ' + json.dumps(measurements.get('failures', []), ensure_ascii=False))
    summary = dict(source_sha=source_sha, code_sha=code_sha,
                   status='FAIL' if errors else 'PASS', errors=errors, setup=setup, commands=commands, tests=tests,
                   measurements=dict(status=measurements.get('status'), samples=len(measurements.get('samples', [])), failures=measurements.get('failures')),
                   scope='059診断だけ。全取引受入・元取得不能jobの原因特定とは別。既存全artifactは保持。')
    members = []
    links = []
    directories = []
    archive = destination / 'diagnostic-originals.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in sorted(area.rglob('*')):
            relative = path.relative_to(area).as_posix()
            if path.is_symlink():
                # 専用fixtureのリンク先をたどらず、元のtarget bytesを記録する。
                raw = os.fsencode(os.readlink(path))
                links.append(dict(path=relative, target_hex=raw.hex(), sha256=digest(raw)))
            elif path.is_dir():
                directories.append(relative)
            elif path.is_file():
                raw = path.read_bytes()
                members.append(dict(path=relative, bytes=len(raw), sha256=digest(raw)))
                output.writestr('task059/' + relative, raw)
        index = dict(files=members, symbolic_links=links, directories=directories, omitted_regular_files=[])
        output.writestr('original-index.json', json.dumps(index, ensure_ascii=False, indent=2) + '\n')
    raw = archive.read_bytes()
    summary['archive'] = dict(file=archive.name, bytes=len(raw), sha256=digest(raw), members=len(members), uncompressed_bytes=sum(row['bytes'] for row in members))
    (destination / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (destination / 'original-index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return summary


def annotation(text):
    # GitHub annotationの制御文字をescapeし、原ログは独立archiveへ保持する。
    return str(text).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')


def main(args):
    summary = collect(Path(args.output) / 'task059', args.destination, args.source_sha, args.code_sha)
    print('DIAGNOSTIC059_SUMMARY ' + json.dumps(summary, ensure_ascii=False), flush=True)
    for error in summary['errors']:
        print('::error title=059診断内訳::' + annotation(error), flush=True)
    return 1 if summary['errors'] else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--code-sha', required=True)
    sys.exit(main(parser.parse_args()))
