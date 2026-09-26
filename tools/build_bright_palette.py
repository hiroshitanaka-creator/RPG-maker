"""承認済みの新素材用64色と、旧色との比較画像を生成する。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
HEX_ROWS = [
    "101D36 1E3154 344F70 55718B 87A0AE BECED1 E7EFF0 FFFFFF",
    "103F78 19649C 228DC4 36B3E2 66D0F0 9BE6F5 C8F5FC EFFCFF",
    "153F32 22613A 32813E 48A449 6AC750 93DB65 BAE987 E0F4B0",
    "4A2B2B 704131 975638 B8784A D29A60 E8B77C F5D29A FFE6BC",
    "5F381E 8C511F BB7624 DF9F2B F3BE39 FFD957 FFED93 FFF6CA",
    "592544 81334D B13C55 D94C55 F36D62 FF9A82 FFC3AD FFE2D1",
    "332A57 504077 715B9A 967DBC BBA4D7 DCC5EF EEDEF8 F9EEFF",
    "143F4B 246773 3B8D94 62B3AC 91D0BB C5E5CF E1F1DD FAF8E8",
]

def read_colors(path):
    return [tuple(map(int,line.split()[:3])) for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and line.strip()[0].isdigit()]

def font(size):
    for name in ("C:/Windows/Fonts/meiryo.ttc", "C:/Windows/Fonts/arial.ttf"):
        if Path(name).exists():return ImageFont.truetype(name,size)
    return ImageFont.load_default(size=size)

def panel(colors, title):
    image = Image.new("RGB",(896,780),"#eef3f6")
    draw = ImageDraw.Draw(image)
    draw.text((22,14),title,fill="#17283e",font=font(25))
    for i,color in enumerate(colors):
        x,y = 24+(i%8)*108,70+(i//8)*86
        draw.rectangle((x,y,x+96,y+54),fill=color)
        draw.text((x,y+58),"#%02X%02X%02X"%color,fill="#17283e",font=font(14))
    return image

def main():
    colors = [tuple(bytes.fromhex(value)) for row in HEX_ROWS for value in row.split()]
    assert len(colors)==64 and len(set(colors))==64
    path = ROOT/"assets/palette/bright.gpl"
    path.write_text("GIMP Palette\nName: RPG-maker bright\nColumns: 8\n# Source: generated; tool: Codex palette authoring; date: 2026-09-26\n"+"".join("%3d %3d %3d\t#%02X%02X%02X\n"%(*c,*c) for c in colors),encoding="utf-8",newline="\n")
    out = ROOT/"docs/verification/asset-review"
    out.mkdir(parents=True,exist_ok=True)
    bright = panel(colors,"新素材用 bright.gpl / 64色")
    bright.save(out/"palette-bright.png")
    old = panel(read_colors(ROOT/"assets/palette/base.gpl"),"既存 base.gpl / 64色（変更なし）")
    comparison = Image.new("RGB",(1792,780))
    comparison.paste(old,(0,0));comparison.paste(bright,(896,0))
    comparison.save(out/"palette-compare.png")
    print("BRIGHT_PALETTE: colors=64 comparison=palette-compare.png")

if __name__ == "__main__":main()
