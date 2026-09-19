#!/usr/bin/env python3
"""凍結時に記録した保護ファイルを読み取り専用で照合する。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    manifest_path = ROOT / '.scope-lock/frozen-files.json'
    if not manifest_path.exists():
        print('凍結ファイルの記録がありません。', file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    failures = []
    for entry in manifest['files']:
        path = (ROOT / entry['path']).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            failures.append(entry['path'] + ': ファイルがありません。')
        elif hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            failures.append(entry['path'] + ': 凍結時のSHA-256と一致しません。')
    for message in failures:
        print(message, file=sys.stderr)
    print('保護対象%d件、一致%d件。' % (len(manifest['files']), len(manifest['files'])-len(failures)))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
