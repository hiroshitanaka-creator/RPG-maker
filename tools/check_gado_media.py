"""受領バイト列・規格・小物差分・修理音を検査する。原画画素の検証とは区別する。"""
from pathlib import Path
import hashlib,json,math,struct,wave
from PIL import Image
from validate_assets import load_palette

ROOT=Path(__file__).resolve().parent.parent
INPUT=ROOT/"assets/_incoming/parent-2026-10-03"
EXPECTED={
"gado_tool_broken.png":(482,"e3640897e199c9594161aa256350fec396cf1378780e38e55901310f85805ba4"),
"gado_tool_repaired.png":(506,"c98982f4ded016b48d4c854bdd00f2ff480ce00870d4c4d9de94a9485937bf3d"),
"prop-source-record.json":(12215,"963943d55c68b52779d0e086072fdcf18249f7c621130107458c9226402089c5"),
"character-source-record.json":(19555,"4ae9a36a503197e20a51799e2a37b04d87f336ce65dd8ccc4990ff44e80ea8b9"),
"repair-tap.provenance.json":(2553,"cb6dd28553337984570bc53d037f8636c0d54cb996294326b509b5cc032fa5f2"),
"synthesize-repair-tap.py":(6083,"fcba6cc29038f9f4f83f9d0f8468e0dd7fcebd6e1455253fff4759ead59e4b12"),
"repair-tap.wav":(42380,"6e36c4de5352a0fd39baa26110fac6069e8ee2d917821b901e5815a0c83739ee"),
}

def main():
    for name,(size,digest) in EXPECTED.items():
        raw=(INPUT/name).read_bytes()
        assert len(raw)==size and hashlib.sha256(raw).hexdigest()==digest,name
    for source,target in [("character-source-record.json","gado-character-generation.json"),("prop-source-record.json","gado-prop-generation.json"),("repair-tap.provenance.json","gado-repair-provenance.json")]:
        assert (INPUT/source).read_bytes()==(ROOT/"assets/source_records"/target).read_bytes()
    character=json.loads((INPUT/"character-source-record.json").read_text(encoding="utf8"))
    for entry in character["records"]:
        candidate=INPUT/f"gado-{entry['form']}-event-standing-candidate.png"
        assert hashlib.sha256(candidate.read_bytes()).hexdigest()==entry["conversion"]["output_sha256"]
        assert entry["original_library"]["library_file_id"] and entry["original_sha256"]
    palette=load_palette(ROOT/"assets/palette/natural.gpl")
    images=[]
    color_counts=[]
    for form in ["broken","repaired"]:
        original=INPUT/f"gado_tool_{form}.png"
        target=ROOT/f"assets/objects/gado_tool_{form}.png"
        assert original.read_bytes()==target.read_bytes()
        image=Image.open(target)
        assert image.mode=="RGBA" and image.size==(32,32)
        raw=image.tobytes()
        pixels=[tuple(raw[index:index+4]) for index in range(0,len(raw),4)]
        colors={pixel[:3] for pixel in pixels if pixel[3]}
        assert {pixel[3] for pixel in pixels}<={0,255} and len(colors)<=16 and colors<=palette
        color_counts.append(len(colors))
        images.append(image)
    assert images[0].crop((0,0,32,16)).tobytes()==images[1].crop((0,0,32,16)).tobytes()
    assert images[0].getbbox()==images[1].getbbox()==(8,2,24,30)
    for y in range(32):
        for x in range(32):
            if not (13<=x<20 and 16<=y<22):assert images[0].getpixel((x,y))==images[1].getpixel((x,y))
    assert all(images[0].getpixel((x,19))[3]==0 for x in range(32))
    assert any(images[1].getpixel((x,19))[3]==255 for x in range(32))
    wav=ROOT/"assets/audio/se/gado_repair.wav"
    assert wav.read_bytes()==(INPUT/"repair-tap.wav").read_bytes()
    with wave.open(str(wav),"rb") as handle:
        assert (handle.getnchannels(),handle.getsampwidth(),handle.getframerate(),handle.getnframes(),handle.getcomptype())==(1,2,44100,21168,"NONE")
        samples=struct.unpack("<21168h",handle.readframes(21168))
    peak=max(map(abs,samples))
    clips=sum(value in (-32768,32767) for value in samples)
    assert peak==5827 and clips==0 and samples[0]==samples[-1]==0
    provenance=json.loads((INPUT/"repair-tap.provenance.json").read_text(encoding="utf8"))
    assert provenance["original_sha256"]==EXPECTED["repair-tap.wav"][1]
    assert provenance["generation_code_sha256"]==EXPECTED["synthesize-repair-tap.py"][1]
    assert not provenance["loop"] and not provenance["speech"] and not provenance["external_samples_used"]
    result={"status":"PASS","received_files_sha256":6,"reproduced_wav_sha256":"MATCH","prop_colors":color_counts,"duration_seconds":21168/44100,"peak_dbfs":20*math.log10(peak/32768),"clipped_samples":clips,"generation_records_received":True,"large_originals_received":False,"large_original_pixels_verified":False,"listened":False,"scope":"受領規格と原音バイト一致。大きい生成原画はLibrary所在だけを追跡。実際の聴感は未確認。"}
    (ROOT/"docs/verification/first-region-intro/media-checks.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("INTRO_MEDIA_PASS: received=6 original_wav_match=1 props=2")
    return 0

if __name__=="__main__":raise SystemExit(main())
