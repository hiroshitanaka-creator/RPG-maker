"""受領済み静止PNGを検証し、元データを保持して決定論的に取り込む。"""
from pathlib import Path
import hashlib
from PIL import Image
from validate_assets import load_palette, frame_bottoms

ROOT = Path(__file__).resolve().parent.parent
INPUT = "assets/_incoming/parent-2026-10-03"
EXPECTED = {
    "human": (1590, "9ac1325542ae8240facda778e6fc1354ab8274687e707c9d0f2f59c3bcc14a7c"),
    "shell": (1854, "895f4a223dbac494f7cf20993364ec1f7b07eb0daa155289ce81e136f89d9cb0"),
}

def main():
    palette = load_palette(ROOT/"assets/palette/natural.gpl")
    for form, (size, digest) in EXPECTED.items():
        source = ROOT/INPUT/f"gado-{form}-event-standing-candidate.png"
        data = source.read_bytes()
        assert len(data) == size and hashlib.sha256(data).hexdigest() == digest, form
        original = Image.open(source)
        assert original.mode == "RGBA" and original.size == (32,48), form
        image = original.convert("RGBA")
        raw = image.tobytes()
        pixels = [tuple(raw[index:index+4]) for index in range(0,len(raw),4)]
        colors = {pixel[:3] for pixel in pixels if pixel[3]}
        assert {pixel[3] for pixel in pixels} <= {0,255}, form
        assert len(colors) <= 16 and colors <= palette, form
        assert frame_bottoms(image,[32,48],[1,1]) == [(0,0,47)], form
        destination = ROOT/f"assets/characters/gado/{form}_standing_front.png"
        destination.parent.mkdir(parents=True,exist_ok=True)
        # 規格適合済みのため色・寸法・画素を変えず、PNGを決定論的に再符号化する。
        image.save(destination,format="PNG",optimize=False,compress_level=9)
        assert Image.open(destination).convert("RGBA").tobytes() == image.tobytes(), form
        print(f"INTRO_ART_IMPORT_PASS: form={form} colors={len(colors)} bottom=47")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
