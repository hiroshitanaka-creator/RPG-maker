#!/usr/bin/env python3
"""083開始前の撮影補助の全castle_check呼出しを列挙し、式不変と世代/経路を対応付ける。"""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'docs/verification/task-083'
BASE='a4dc7c9d0d705f3181391fdccee4e4c825ddcaaf'
TARGET='tools/capture_task009_village_regression.gd'
def original(p):return subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT).decode()
def calls(s):
    result=[]
    for hit in re.finditer(r'\bcastle_check\s*\(',s):
        line=s.count('\n',0,hit.start())+1
        prefix=s[s.rfind('\n',0,hit.start())+1:hit.start()]
        if prefix.strip()=='func':continue
        depth=1;quote=None;escape=False;i=hit.end()
        while depth:
            c=s[i]
            if quote:
                if escape:escape=False
                elif c=='\\':escape=True
                elif c==quote:quote=None
            elif c in "\"'":quote=c
            elif c=='(':depth+=1
            elif c==')':depth-=1
            i+=1
        fn=list(re.finditer(r'^func (\w+)\(',s[:hit.start()],re.M))[-1].group(1)
        result.append({'line':line,'function':fn,'assertion':s[hit.start():i]})
    return result

def main():
    before=original(TARGET);after=(ROOT/TARGET).read_text();old=calls(before);new=calls(after)
    assert len(old)==len(new) and [x['assertion'] for x in old]==[x['assertion'] for x in new]
    # assertion以外も、コメント2行と撮影入力1値以外に変更がないことを証明。
    expected=before.replace('var front: Array=[[16,9],[12,5],[8,6],[8,6],[8,5]][index]','var front: Array=[[16,9],[12,5],[8,6],[8,6],[7,5]][index]')
    strip=lambda s:'\n'.join(l for l in s.splitlines() if not l.lstrip().startswith('#'))
    assert strip(expected)==strip(after)
    ci=json.loads((OUT/'github-corrected-final.json').read_text())
    modes={j['name']:j for j in ci['jobs'] if 'normal-input-and-rendering' in j['name']}
    rows=[]
    for i,(a,b) in enumerate(zip(old,new),1):
        fn=a['function'];scope='journey / details / restart-0〜4（共有部）'
        if fn in ['journey','coast_to_village']:scope='journey（通常キー・通常メニュー）'
        elif fn=='to_port':scope='journey / details / restart-0〜4の帰路'
        elif fn=='restart_route':scope='restart-0〜4'
        elif fn=='details':scope='details'
        special=fn=='picture' and 'matched' in a['assertion']
        rows.append({'id':f'CAP009-{i:03}','original_line':a['line'],'current_line':b['line'],'function':fn,'original_assertion':a['assertion'],'current_assertion_identical':True,'runtime_modes':scope,'fixed_generation':'006完成5f1c2ba231191b25b9b32a814b616a9f8d0a54ceの当時capture_region2_village_connections.gdを固定CI全7モードで実行。009完成ce07fdada0466138260ab678c10fd78e61c0c63dは別のscope/対応監査であり、この48呼出しの固定実描画SHAではない。','latest_generation':'611c598：同じassertionを最新CIの全7モードで実行。journeyの通常キー経路をcounter-back正例でも実行。','adopted_input_change':'room4 frontの[8,5]→[7,5]。全画素可視の前提を守るため。' if special or 'front' in a['assertion'] else 'なし（当該assertion/閾値/分岐/上限不変）','successor_coverage':'旧[8,5]での正常遮蔽はcapture_s10_static_displayのAPI入力player-behindと別の実方向キーnormal-keys-behindで個別に確認。通常キーcounter-backとAPI入力を同一とはみなさない。' if special else '元のassertionを維持。083の占有/保存/静止画像条件は新規集中検査で追加。'})
    inherited=[]
    for p in ['tools/capture_castle_town.gd','tools/smoke_first_region.gd','tools/check_region2_village_regression.py','tools/check_region2_village_regression.gd','tools/test_task009_lifecycle.py','docs/verification/task-009/assertion-map.md','docs/verification/task-016/assertion-correspondence.json']:
        data=(ROOT/p).read_bytes();assert data==original(p).encode()
        inherited.append({'path':p,'base_bytes_unchanged':True,'sha256':hashlib.sha256(data).hexdigest(),'note':'継承・既存世代対応・実行判定を083で変更していない。継承元の全関数がこのjourneyで実行されるとは主張しない。保護R-07も別CIで実行。'})
    result={'base':BASE,'current_helper_sha256':hashlib.sha256(after.encode()).hexdigest(),'all_assertion_calls_identical':True,'assertion_calls':len(rows),'changed_input_only':[{'room':4,'old':[8,5],'new':[7,5]}],'rows':rows,'inherited_and_existing_maps':inherited,'ci_modes':modes,'counter_back_command':'python tools/test_task009_lifecycle.py --fixed-path ../fixed --godot ../godot','counter_back_source_sha':'611c5986f3d960d3c306c48d971833de7f5a9523','positive_and_negative_result':'counter-back-negative-proof-611c598.json','raw_log':'ci-lifecycle-green-611c598.log','new_tests_ci_connected':False,'new_tests_note':'check_s10_static_display.py/.gdとcapture_s10_static_display.gdはCI未接続。083で明示ローカル実行した証拠だけを使用する。'}
    (OUT/'assertion-migration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    md=['# 083 撮影assertionの移行対応','',f'083基点 `{BASE}` の撮影補助の全 `{len(rows)}` castle_check呼出しを括弧・文字列を解釈して抽出。最新版と全式・順序が一致。コメントとroom4撮影入力1値以外のコードも一致する。実行時はループ展開によりjourneyが132条件となる。削除・省略・閾値/上限変更なし。','','| ID | 元行→最新行 | 関数 / 実行モード | 固定版 | 最新版・後続 |','|---|---|---|---|---|']
    for row in rows:
        md.append(f"| {row['id']} | {row['original_line']}→{row['current_line']} | {row['function']} / {row['runtime_modes']} | 006固定描画5f1c2ba／009完成ce07は別scope監査 | 式不変、611c598のCI。"+('旧[8,5]の遮蔽はAPI/実キーを別検査。' if '旧[8,5]' in row['successor_coverage'] else '元assertion維持。')+' |')
    md+=['','全式・元行・最新版行・CIジョブURLは assertion-migration.json。継承元・実行判定・既存の009/016世代対応表は083基点から全bytes不変。固定006の当時条件を最新の132件へ減らしたわけではなく、083基点の全呼出しを保持している。','','旧room4-frontの「全画素可視」は新人物配置により旧[8,5]では成立しないため、最新の可視検査点を隣[7,5]に移す。元位置は後続の人物遮蔽検査で正負を確認する。通常キーjourney/counter-back、API入力撮影、追加した実方向キー撮影の3経路は区別する。','','新規S10集中検査はCI未接続。毎回CI実行されるとの主張はしない。counter-back正例と故障注入の最新CIログ・終了値は ci-lifecycle-green-611c598.log / counter-back-negative-proof-611c598.json。各負例は実assertion FAIL・終了1・parse errorなし・timeoutなしを確認した。']
    (OUT/'assertion-migration.md').write_text('\n'.join(md)+'\n');print('ASSERTION_MIGRATION_PASS: calls='+str(len(rows)))
if __name__=='__main__':main()
