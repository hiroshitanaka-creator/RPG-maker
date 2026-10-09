from pathlib import Path
import hashlib,json,tarfile
root=Path(__file__).resolve().parents[1]
count=0
for row in json.loads((root/'archives.json').read_bytes()):
    path=root/row['archive']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'], path
    assert path.stat().st_size==row['bytes'],path
    index={r['path']:r for r in json.loads((root/row['member_index']).read_bytes())}
    seen=set()
    with tarfile.open(path,'r:gz') as tar:
        for member in tar:
            assert member.isfile() or member.islnk(),member.name
            assert member.name in index,member.name
            raw=tar.extractfile(member).read();expected=index[member.name]
            assert len(raw)==expected['size'] and hashlib.sha256(raw).hexdigest()==expected['sha256'],member.name
            seen.add(member.name)
    assert seen==set(index) and len(seen)==row['members'],path
    count+=len(seen)
print('ARCHIVE057_PASS:',len(json.loads((root/'archives.json').read_bytes())),'archives',count,'members')
