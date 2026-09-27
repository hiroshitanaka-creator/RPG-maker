"""以前の平原見本と本番描画を、同じ512×288の大きさで並べる。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / "docs/verification/battle-layout"


def main():
    before = Image.open(ROOT / "docs/verification/owner-monsters/battle-mock-plains.png").convert("RGB")
    after = Image.open(DESTINATION / "01-party-four.png").convert("RGB")
    assert before.size == (512, 288)
    assert after.size == (1024, 576)
    after = after.resize((512, 288), Image.Resampling.NEAREST)
    board = Image.new("RGB", (1056, 344), "#17232b")
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 16)
    draw.text((8, 10), "以前の平原見本（静止画）", font=font, fill="white")
    draw.text((536, 10), "今回の本番描画（原寸背景・下端の窓・縦隊）", font=font, fill="white")
    board.paste(before, (8, 42))
    board.paste(after, (536, 42))
    board.save(DESTINATION / "plains-comparison.png")
    print("BATTLE_COMPARISON_PASS: 原画を変更せず、512×288同士で比較画像を作成")


if __name__ == "__main__":
    main()
