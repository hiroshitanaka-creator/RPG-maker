#!/usr/bin/env python3
"""060の4ファイルに限り、固定元bytesを確認して観測wrapperを生成する。"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re

BASE = '6695d7b802137e9d6b7e468a1414c04d658a5380'
HASHES = {
 'equipment_save_codec.gd':'57d1cd0ad63172c08fdb696ea7f0b009f12219ffd4f2aa9360c78d0ab15a0a49',
 'equipment_document_validation.gd':'e978c2eb2ccf2c207bb337673a364e10665d603f0b7ebb56f4be6294631e6ad4',
 'saved_document.gd':'7c97f0154ce5d518de94c5c1700fb9b43cc862e0e20c8f7d35a80c6a7bc7bcc9',
 'saved_value_types.gd':'63158c4fd9b747d614e2e792a7e3e27b12e180ddd3c446efa33cc7f40cfb00da'}
FUNCTIONS = {
 'equipment_save_codec.gd':['decode_source','encode_candidate','valid_utf8','unique_json_keys'],
 'equipment_document_validation.gd':['context_errors','metadata_errors','native_metadata_errors','auxiliary','schema','validate','audit_errors','prepare_candidate','compare_migration'],
 'saved_document.gd':['encode','decode'],
 'saved_value_types.gd':['describe','restore']}
# 置換対象は完全一致する式。元の条件式・短絡・returnと引数評価順を保持する。
EXPRESSIONS = {
 'equipment_save_codec.gd':[
 ('parser.parse(text)', '_Cost060.parse(parser,text,"codec.parse.outer")'),
 ('inner_parser.parse(inner_text)', '_Cost060.parse(inner_parser,inner_text,"codec.parse.inner")'),
 ('compressed.decompress(int(outer.decoded_bytes),FileAccess.COMPRESSION_GZIP)', '_Cost060.decompress(compressed,int(outer.decoded_bytes),FileAccess.COMPRESSION_GZIP,"codec.decompress")'),
 ('raw.duplicate(true)', '_Cost060.copy_dictionary(raw,true,"codec.copy.raw")'),
 ('document.duplicate(true)', '_Cost060.copy_dictionary(document,true,"codec.copy.document")')],
 'equipment_document_validation.gd':[
 ('document.duplicate(true)', '_Cost060.copy_dictionary(document,true,"validation.copy.document")'),
 ('candidate.duplicate(true)', '_Cost060.copy_dictionary(candidate,true,"validation.copy.candidate")')],
 'saved_document.gd':[
 ('parser.parse(text)', '_Cost060.parse(parser,text,"saved_document.parse")'),
 ('compressed.decompress(int(length),FileAccess.COMPRESSION_GZIP)', '_Cost060.decompress(compressed,int(length),FileAccess.COMPRESSION_GZIP,"saved_document.decompress")')],
 'saved_value_types.gd':[
 ('value.duplicate(true)', '_Cost060.copy_dictionary(value,true,"types.copy.value")'),
 ('metadata["arrays"].duplicate(true)', '_Cost060.copy_array(metadata["arrays"],true,"types.copy.metadata_arrays")')]}


def generate(name, raw):
    assert hashlib.sha256(raw).hexdigest() == HASHES[name], '固定元hash不一致:'+name
    source = raw.decode()
    changed = source
    counts = {}
    for before, after in EXPRESSIONS[name]:
        count = changed.count(before)
        assert count > 0, (name, before)
        counts[before] = count
        changed = changed.replace(before, after)
    wrappers = []
    for function in FUNCTIONS[name]:
        pattern = r'^static func '+function+r'\(([^\n]*)\)\s*->\s*(\w+):$'
        matches = list(re.finditer(pattern, changed, re.M))
        assert len(matches) == 1, (name, function)
        match = matches[0]
        parameters, result_type = match.groups()
        arguments = ','.join(p.strip().split(':')[0].strip() for p in parameters.split(','))
        original_header = match.group()
        changed = changed.replace(original_header, original_header.replace(function+'(', '_cost060_'+function+'(', 1), 1)
        wrappers.append(original_header+'\n\tvar tick := _Cost060.begin("'+name.removesuffix('.gd')+'.'+function+'")\n'
                        '\tvar result: '+result_type+' = _cost060_'+function+'('+arguments+')\n'
                        '\t_Cost060.finish(tick)\n\treturn result\n')
    prefix = 'const _Cost060 = preload("res://tools/check_equipment_save_codec_cost.gd")\n'
    changed = changed.replace('extends RefCounted\n', 'extends RefCounted\n'+prefix, 1)
    changed += '\n'+'\n'.join(wrappers)
    # 逆変換で元body全bytesへ戻ることを確認。計測以外の差分は拒否する。
    restored = changed[:changed.index('\n'+wrappers[0])]
    restored = restored.replace(prefix, '')
    for function in FUNCTIONS[name]:
        restored = restored.replace('static func _cost060_'+function+'(', 'static func '+function+'(', 1)
    for before, after in EXPRESSIONS[name]:
        restored = restored.replace(after, before)
    assert restored == source, '元body逆変換不一致:'+name
    return changed.encode(), counts


def instrument(checkout):
    checkout = Path(checkout).resolve()
    # 元checkoutへの誤挿入を禁止する。
    assert checkout != Path(__file__).resolve().parents[3], '本番作業ツリーへの挿入は禁止'
    rows = {}; patches = []
    for name in HASHES:
        path = checkout/'scripts/game'/name
        old = path.read_bytes(); new, counts = generate(name, old)
        rows['scripts/game/'+name] = dict(before=hashlib.sha256(old).hexdigest(), after=hashlib.sha256(new).hexdigest(), expressions=counts, functions=FUNCTIONS[name], original_body_restored=True)
        patches.extend(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True), fromfile='a/scripts/game/'+name, tofile='b/scripts/game/'+name))
        path.write_bytes(new)
    return rows, ''.join(patches)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--checkout', required=True)
    args = parser.parse_args()
    rows, patch = instrument(args.checkout)
    print(json.dumps(rows, ensure_ascii=False, indent=2)); print(patch)
