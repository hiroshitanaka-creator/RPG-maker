"""登録済み素材の由来・加工記録と出力ハッシュを集約する。権利を推測しない。"""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parent.parent

def main():
    assets=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))['assets']
    first_enemies={'slime','bat','shell_guard','ember_wisp','gate_beast'}
    records=[]
    for asset in assets:
        path=asset['path']
        receipts=['docs/art-import.md','docs/image-generation-prompts.json']
        origin='生成・提供参照の加工。詳細は取込記録を参照'
        if '/erosion_signs/' in path:
            origin='既存PNGを規定パレット内で決定論的に変換'
            receipts=['docs/verification/erosion-signs-import.json','tools/build_erosion_signs.py']
        elif '/forms/' in path:
            origin='依頼者の参照画像に基づくCodex内蔵画像生成と規格変換'
            receipts=['docs/monster-form-generation.json','docs/verification/monster-form-import.json']
        elif path.endswith('/portrait.png'):
            origin='提供された4人画像からの切り出し'
            receipts=['docs/asset-intake-20260919.md','tools/import_character_art.py']
        elif path.startswith('assets/monsters/') and path.split('/')[2] not in first_enemies:
            origin='依頼者が作成して提供したモンスター画像からの切り出し'
            receipts=['docs/user-monsters-20260919.md','docs/verification/user-monster-import.json']
        elif path.endswith('/walk.png'):
            origin='提供された歩行画像を正規化。一部の人物は不足コマの生成を含む'
        for receipt in receipts:
            assert (ROOT/receipt).is_file(),receipt
        records.append({'path':path,'status':asset['status'],'origin':origin,'receipts':receipts,'source':asset.get('source'),
                        'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()})
    output={'scope':'現在のリポジトリ内で使用する素材の来歴。公開・外部配布は対象外。',
            'use_basis':'依頼者からのRPG-maker制作・素材利用の指示。生成許可の個別範囲は履歴を参照。',
            'external_terms':'提供画像の外部サービス生成条件・他用途への許諾は、この記録だけでは断定しない。','assets':records}
    (ROOT/'docs/asset-provenance-v1.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'ASSET_PROVENANCE_PASS: {len(records)}点の由来参照と出力SHAを記録')

if __name__=='__main__':main()
