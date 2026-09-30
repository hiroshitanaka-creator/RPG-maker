"""メニューの変更前後で内容・配置・使用可否を照合し、実ノードの色と字体を確認する。"""
import copy,hashlib,json,re,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/menu-colors'
EXPECTED=[f'{i:02}' for i in range(1,24)]
BLUE='101c50ff';WHITE='ffffffff';MUTED='9aa6c4ff'
BODY_BASELINES={
    '12-mechanics':('main/1/1/0/0/0/1',[16,38,480,128]),
    '14-upgrade':('main/1/1/0/0/0/1',[16,38,480,128]),
    '22-journal-filled':('main/1/1/0/0/0/2',[16,62,480,128]),
    '23-journal-list':('main/1/1/0/0/0/2',[16,62,480,128]),
}

def expected_body_layout(screen_id,rows):
    """承認された本文高さだけを基準にし、既存VBoxの後続配置を導出する。"""
    expected=copy.deepcopy(rows)
    if screen_id not in BODY_BASELINES:return expected
    path,new_rect=BODY_BASELINES[screen_id]
    body=next(r for r in expected if r['path']==path)
    assert body['kind']=='RichTextLabel' and body['rect']==new_rect[:3]+[0], '変更前の本文領域が想定と異なる'
    delta=new_rect[3]-body['rect'][3]
    parent,index=path.rsplit('/',1)
    container=next(r for r in expected if r['path']==parent)
    assert container['kind']=='VBoxContainer', '既存の縦配置を維持'
    container['rect'][3]+=delta
    body['rect']=list(new_rect)
    # 高さ0の本文に出ていた内部バーは、本文が128pxに収まる場合だけ不要になる。
    bars=[r for r in expected if r['path']==path+'/0']
    assert len(bars)==1 and bars[0]['kind']=='VScrollBar', '変更前の本文内部バーを確認'
    scroll=bars[0]['range']
    assert scroll[0]==0 and 0<scroll[1]<=delta and scroll[2:]==[0,0], '本文全体が新しい高さに収まる'
    expected.remove(bars[0])
    for row in expected:
        if row['path'].startswith(parent+'/'):
            sibling=row['path'][len(parent)+1:].split('/')[0]
            if int(sibling)>int(index):row['rect'][1]+=delta
    return expected

def content(rows):
    result=copy.deepcopy(rows)
    for row in result:
        row.pop('styles',None);row.pop('colors',None);row.pop('font',None)
        if row.get('text','').startswith('経過 '):row['text']=re.sub(r'\d+\.\d+','<時間>',row['text'])
    return result

def palette_failures(document):
    errors=[];counts={'windows':0,'buttons':0,'popups':0,'scrollbars':0,'fonts':0,'disabled_buttons':0}
    for screen in document['screens']:
        for row in screen['controls']:
            prefix=screen['id']+':'+row['path']
            styles=row.get('styles',{});colors=row.get('colors',{})
            if 'font' in row:
                counts['fonts']+=1
                if 'Noto Sans JP' not in row['font']:errors.append(prefix+' 字体: '+row['font'])
                if colors.get('font')!=WHITE:errors.append(prefix+' 文字色: '+str(colors.get('font')))
            if 'panel' in styles:
                counts['windows']+=1
                if styles['panel'].get('background')!=BLUE or styles['panel'].get('border')!=WHITE or styles['panel'].get('widths')!=[1,1,1,1]:errors.append(prefix+' 窓の青地と白枠')
            if row['kind'] in ['Button','OptionButton']:
                counts['buttons']+=1
                if row.get('disabled'):counts['disabled_buttons']+=1
                if colors.get('disabled')!=MUTED or colors['disabled']==colors.get('font'):errors.append(prefix+' 無効項目の色')
                if styles.get('focus',{}).get('border')!=WHITE or styles.get('focus',{}).get('widths')!=[1,1,1,1]:errors.append(prefix+' 白い選択枠')
                if styles.get('normal',{}).get('background')!=BLUE:errors.append(prefix+' ボタンの青地')
            if row['kind']=='PopupMenu':
                counts['popups']+=1
                if colors.get('disabled')!=MUTED or styles.get('hover',{}).get('border')!=WHITE or styles.get('hover',{}).get('widths')!=[1,1,1,1]:errors.append(prefix+' 選択一覧の色と枠')
            if row['kind'] in ['VScrollBar','HScrollBar']:
                counts['scrollbars']+=1
                if styles['scroll'].get('background')!=BLUE or styles['grabber'].get('background')!='bdc7d3ff' or styles['grabber_highlight'].get('background')!=WHITE:errors.append(prefix+' スクロールバーの色')
        if screen['id'] in ['04-atlas','11-job-lore','17-title','18-review','20-review-input'] and screen['corner']!=BLUE:errors.append(screen['id']+' 全体の背景色')
    return errors,counts

def gallery(document,stage):
    width,height=512,288;header=30;columns=3
    sheet=Image.new('RGB',(columns*width,((len(document['screens'])+columns-1)//columns)*(height+header)+42),'#101c50')
    draw=ImageDraw.Draw(sheet);font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),16)
    draw.text((12,8),'メニュー全画面：'+('変更前' if stage=='before' else '変更後')+'　※条件付き画面は表示用状態',font=font,fill='white')
    for index,screen in enumerate(document['screens']):
        x=(index%columns)*width;y=(index//columns)*(height+header)+42
        draw.text((x+8,y+4),screen['id'][:2]+' '+screen['title'],font=font,fill='white')
        image=Image.open(OUT/stage/(screen['id']+'.png')).convert('RGB')
        assert image.size==(1024,576),'撮影寸法を維持'
        sheet.paste(image.resize((width,height),Image.Resampling.NEAREST),(x,y+header))
    sheet.save(OUT/(stage+'-all.png'))

def main():
    before=json.loads((OUT/'before/screens.json').read_text(encoding='utf8'))
    after=json.loads((OUT/'after/screens.json').read_text(encoding='utf8'))
    errors=[]
    if [s['id'][:2] for s in before['screens']]!=EXPECTED or [s['id'] for s in before['screens']]!=[s['id'] for s in after['screens']]:errors.append('対象23画面の不足または順序変更')
    if before['save_sha256']!=after['save_sha256']:errors.append('開始保存が異なる')
    if before['sources']!=after['sources']:errors.append('変更前後で共有する描画コードが異なる')
    for doc in [before,after]:
        if doc['errors'] or doc['elapsed_ms']>=180000 or doc['limit_ms']!=180000:errors.append('撮影エラーまたは180秒上限')
    original=subprocess.check_output(['git','show',before['baseline']+':scripts/ui/game_root.gd'],cwd=ROOT)
    if hashlib.sha256(original).hexdigest()!=before['root_source_sha256']:errors.append('変更前の画面コードが基点と不一致')
    if hashlib.sha256((ROOT/'scripts/ui/game_root.gd').read_bytes()).hexdigest()!=after['root_source_sha256']:errors.append('変更後の画面コードが現在と不一致')
    for path,digest in after['sources'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:errors.append('変更後の記録が古い: '+path)
    for a,b in zip(before['screens'],after['screens']):
        mode_by_id={'01':'REGION_COMMANDS','02':'REGION_COMMANDS','03':'REGION_ITEMS','04':'WORLD_ATLAS','05':'REGION_TRAVEL','06':'REGION_TRAVEL','07':'PARTY','08':'PARTY','09':'PARTY','10':'PARTY','11':'JOB_LORE','12':'MECHANICS','13':'PARTY','14':'RULE_UPGRADE','15':'JOURNAL','16':'DIALOGUE','17':'MENU','18':'REVIEW','19':'REVIEW','20':'REVIEW','21':'REGION_COMMANDS'}
        mode_by_id.update({'22':'JOURNAL','23':'JOURNAL'})
        if a['mode']!=mode_by_id[a['id'][:2]] or b['mode']!=a['mode']:errors.append(a['id']+' 対象画面の表示状態が不一致')
        ar,br=content(a['controls']),content(b['controls'])
        ar=expected_body_layout(a['id'],ar)
        if ar!=br:
            differences=[]
            for index,(x,y) in enumerate(zip(ar,br)):
                if x!=y:differences.append({'index':index,'before':x,'after':y})
            errors.append(a['id']+' 文言・順番・矩形・使用可否の不一致')
            (OUT/(a['id']+'-differences.json')).write_text(json.dumps({'before_count':len(ar),'after_count':len(br),'differences':differences},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    before_errors,_=palette_failures(before)
    for doc in [before,after]:
        journal=next(s for s in doc['screens'] if s['id']=='22-journal-filled')
        opened=next(s for s in doc['screens'] if s['id']=='23-journal-list')
        if not any(r['kind']=='OptionButton' and len(r.get('items',[]))==2 for r in journal['controls']):errors.append('手帳の記録選択欄が未観測')
        if not any(r['kind']=='RichTextLabel' and '物語の本文' in r.get('text','') for r in journal['controls']):errors.append('手帳の本文が未観測')
        if not any(r['kind']=='PopupMenu' and len(r.get('items',[]))==2 for r in opened['controls']):errors.append('手帳の開いた記録一覧が未観測')
    color_errors,counts=palette_failures(after);errors.extend(color_errors)
    if not before_errors:errors.append('変更前の色を不成立として検出できない')
    if not all(counts[k]>0 for k in counts):errors.append('窓・ボタン・リスト・無効項目・スクロール・字体の観測が不足')
    result={'status':'PASS' if not errors else 'FAIL','screens':len(after['screens']),'before_color_failures':len(before_errors),'observed':counts,'failures':errors,
            'body_height_baselines':{key:{'path':value[0],'rect':value[1]} for key,value in BODY_BASELINES.items()},
            'method':'同じ表示用状態の本番画面。文言・順序・使用可否は完全一致。承認済み3画面（手帳の一覧展開を含む4状態）の本文だけ高さ128px。親と後続要素はその高さ差から自動配置を導出し厳密照合。本文が収まる内部バーだけ消失を確認。他の矩形は完全一致。試遊の経過時間のみ文型で照合。'}
    (OUT/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    for stage,doc in [('before',before),('after',after)]:gallery(doc,stage)
    print(json.dumps(result,ensure_ascii=False))
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
