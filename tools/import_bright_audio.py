#!/usr/bin/env python3
"""確認済みのCC0音源をOGGへ変換し、新しいaudio一覧へ登録する。"""
from pathlib import Path
import sys
import json
import hashlib
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.tools/audio_python'))
import imageio_ffmpeg
import numpy as np
import soundfile as sf

INCOMING=ROOT/'assets/_incoming'
FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
RATE=44100
TRACKS=[
    ('village','TownTheme.mp3','town-theme-rpg','cynicmusic','ハープと笛を中心とした穏やかな村の曲。'),
    ('world','the_field_of_dreams.mp3','the-field-of-dreams','pauliuw','広い土地の探索に使う、旋律のある明るい曲。'),
    ('cave','cave%20themeb4.ogg','cave-theme','Brandon Morris (HaelDB / Brandon75689)','洞窟探索のための静かで神秘的な曲。'),
    ('battle','battleThemeA.mp3','battle-theme-a','cynicmusic','弦と管の勢いを使った通常戦闘の曲。'),
    ('boss','Juhani%20Junkala%20-%20Epic%20Boss%20Battle%20%5BSeamlessly%20Looping%5D.wav','boss-battle-music','Juhani Junkala / SubspaceAudio','強い打楽器と管弦楽によるボス戦の曲。'),
    ('victory','victory_0.wav','victory-4','Umplix','戦闘勝利を知らせる短いファンファーレ。'),
]
SOUNDS=[
    ('confirm','interface-sounds','confirmation_001.ogg','決定操作を知らせる短い電子音。'),
    ('cancel','interface-sounds','back_001.ogg','取り消し・前の窓へ戻る操作の短い音。'),
    ('chest','rpg-audio','handleCoins.ogg','宝箱の報酬を知らせる硬貨の音。'),
    ('door','rpg-audio','doorOpen_1.ogg','木製扉を開ける音。'),
    ('stairs','rpg-audio','footstep00.ogg','階段を上り下りする足音。'),
    ('attack','rpg-audio','knifeSlice.ogg','刃を振る通常攻撃の音。'),
    ('damage','impact-sounds','impactPunch_medium_000.ogg','打撃による被ダメージの音。'),
    ('heal','interface-sounds','maximize_001.ogg','回復を知らせる上向きの電子音。'),
]


def decode(path):
    result=subprocess.run([FFMPEG,'-v','error','-i',str(path),'-f','f32le','-ar',str(RATE),'-ac','2','pipe:1'],capture_output=True,check=True)
    return np.frombuffer(result.stdout,dtype='<f4').reshape(-1,2).copy()


def main():
    entries=[];results=[]
    for id_,filename,slug,author,description in TRACKS:
        path=INCOMING/('music_'+id_+Path(filename).suffix)
        samples=decode(path)
        # 曲の先頭・末尾を80msだけ重ね、循環境界のクリックを減らす。
        overlap=round(RATE*.08)
        weight=np.linspace(0,1,overlap,dtype=np.float32)[:,None]
        joint=samples[-overlap:]*(1-weight)+samples[:overlap]*weight
        out=np.concatenate([joint,samples[overlap:-overlap]])
        out*=float(10**(-3/20))/max(float(np.max(np.abs(out))),1e-8)
        # Vorbisの端で生じる段差も抑える。音のない区間は挿入しない。
        edge=round(RATE*.020)
        out[:edge]*=np.linspace(0,1,edge,dtype=np.float32)[:,None]
        out[-edge:]*=np.linspace(1,0,edge,dtype=np.float32)[:,None]
        dest=ROOT/f'assets/audio/bgm/{id_}.ogg';dest.parent.mkdir(parents=True,exist_ok=True)
        pcm=INCOMING/('loop_'+id_+'.wav');sf.write(str(pcm),out,RATE,subtype='PCM_16')
        subprocess.run([FFMPEG,'-v','error','-y','-i',str(pcm),'-c:a','libvorbis','-q:a','5',
                        '-metadata','LOOPSTART=0','-metadata',f'LOOPEND={len(out)}',str(dest)],check=True)
        decoded=decode(dest)
        assert len(decoded)>RATE and np.isfinite(decoded).all()
        seam=float(np.max(np.abs(decoded[0]-decoded[-1])))
        peak=float(np.max(np.abs(decoded)))
        assert peak<1.0, id_+' クリッピング'
        assert seam<.005, id_+' ループ境界の段差'
        entries.append({'path':dest.relative_to(ROOT).as_posix(),'kind':'bgm','status':'required',
                        'source':'imported','source_url':'https://opengameart.org/content/'+slug,
                        'download_url':'https://opengameart.org/sites/default/files/'+filename,
                        'author':author,'license':'CC0-1.0','retrieved_at':'2026-09-26',
                        'modified':'44100Hzステレオ、80ms循環クロスフェード、両端20msテーパー、ピーク-3dB、OGG Vorbis品質5、全体ループタグ',
                        'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'loop':True,'loop_start':0,'loop_end':len(out),'description':description})
        results.append({'id':id_,'kind':'bgm','frames':len(decoded),'seconds':round(len(decoded)/RATE,3),'peak':round(peak,6),'seam_delta':round(seam,6),'decoded':True})
    for id_,pack,filename,description in SOUNDS:
        with zipfile.ZipFile(INCOMING/(pack+'.zip')) as archive:
            raw=archive.read('Audio/'+filename)
        src=INCOMING/('se_'+id_+'.ogg');src.write_bytes(raw)
        samples=decode(src)
        # 階段は同じ足音を3回配置。その他は元音のまま音量だけ統一する。
        if id_=='stairs':
            silence=np.zeros((round(RATE*.12),2),dtype=np.float32)
            samples=np.concatenate([samples,silence,samples,silence,samples])
        samples*=float(10**(-6/20))/max(float(np.max(np.abs(samples))),1e-8)
        dest=ROOT/f'assets/audio/se/{id_}.wav';dest.parent.mkdir(parents=True,exist_ok=True)
        sf.write(str(dest),samples,RATE,subtype='PCM_16')
        entries.append({'path':dest.relative_to(ROOT).as_posix(),'kind':'se','status':'required',
                        'source':'imported','source_url':'https://kenney.nl/assets/'+pack,
                        'source_file':'Audio/'+filename,'author':'Kenney','license':'CC0-1.0','retrieved_at':'2026-09-26',
                        'modified':'44100HzステレオPCM16 WAV、ピーク-6dB'+('、足音3回を120ms間隔で合成' if id_=='stairs' else ''),
                        'source_sha256':hashlib.sha256(raw).hexdigest(),'description':description})
        result=decode(dest);assert len(result)>0 and np.isfinite(result).all()
        results.append({'id':id_,'kind':'se','seconds':round(len(result)/RATE,3),'peak':round(float(np.max(np.abs(result))),6),'decoded':True})
    registry_path=ROOT/'assets/registry.json';registry=json.loads(registry_path.read_text(encoding='utf-8'))
    paths={e['path'] for e in entries}
    registry['audio']=[e for e in registry.get('audio',[]) if e['path'] not in paths]+entries
    registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'docs/verification/asset-review/audio-checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    for r in results:print('AUDIO_DECODE_PASS:',json.dumps(r,ensure_ascii=False))


if __name__=='__main__':main()
