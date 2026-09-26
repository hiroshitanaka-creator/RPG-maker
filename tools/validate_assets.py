#!/usr/bin/env python3
"""assets/registry.json に従って画像素材を検査する。

使い方:
    python tools/validate_assets.py            # 検査のみ
    python tools/validate_assets.py --strict   # 台帳外のファイルもエラーにする（CI 用）

検査内容:
    - 台帳に載っているファイルが存在するか（status=required のみ必須）
    - 画像サイズが台帳の値と一致するか
    - frame × grid がサイズと一致するか
    - アルファ値が 0 か 255 のみか（半透明・アンチエイリアスの縁を検出）
    - 使用色数が上限以内か
    - 不透明ピクセルの色がパレットに含まれるか
    - スプライトシート内の全コマで接地ライン（最下の不透明行）が揃っているか
    - assets/ 配下に台帳外の PNG が無いか（--strict のとき）

終了コード: 0 = 問題なし / 1 = エラーあり
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    print("Pillow が必要です: pip install pillow", file=sys.stderr)
    raise SystemExit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "assets" / "registry.json"
# 検査対象外のディレクトリ（外部素材の一時置き場など）
IGNORED_DIRS = {"_incoming"}


def load_palette(path: Path) -> set[tuple[int, int, int]] | None:
    """GIMP パレット (.gpl) を読み込む。無ければ None。"""
    if not path.exists():
        return None
    colors: set[tuple[int, int, int]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith(("gimp palette", "name:", "columns:")):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            colors.add((int(parts[0]), int(parts[1]), int(parts[2])))
        except ValueError:
            continue
    return colors or None


def frame_bottoms(img: Image.Image, frame: list[int], grid: list[int]) -> list[tuple[int, int, int | None]]:
    """各コマの接地ライン（最下の不透明行。コマ内の相対 y）を返す。"""
    fw, fh = frame
    cols, rows = grid
    result: list[tuple[int, int, int | None]] = []
    px = img.load()
    for row in range(rows):
        for col in range(cols):
            bottom: int | None = None
            for y in range(fh - 1, -1, -1):
                found = False
                for x in range(fw):
                    if px[col * fw + x, row * fh + y][3] != 0:
                        found = True
                        break
                if found:
                    bottom = y
                    break
            result.append((row, col, bottom))
    return result


def check_asset(entry: dict, palette: set[tuple[int, int, int]] | None) -> tuple[list[str], bool]:
    """1件を検査する。戻り値は (エラー一覧, ファイルが存在したか)。"""
    errors: list[str] = []
    rel = entry["path"]
    path = REPO_ROOT / rel
    status = entry.get("status", "required")

    if not path.exists():
        if status == "required":
            errors.append(f"{rel}: ファイルが存在しない (status=required)")
        return errors, False

    try:
        img = Image.open(path).convert("RGBA")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{rel}: 画像として読めない ({exc})")
        return errors, True

    size = entry.get("size")
    if size and list(img.size) != list(size):
        errors.append(f"{rel}: サイズが不一致 期待 {size[0]}x{size[1]} / 実際 {img.size[0]}x{img.size[1]}")

    frame, grid = entry.get("frame"), entry.get("grid")
    if frame and grid:
        expected = [frame[0] * grid[0], frame[1] * grid[1]]
        if list(img.size) != expected:
            errors.append(
                f"{rel}: frame×grid とサイズが不一致 期待 {expected[0]}x{expected[1]} / 実際 {img.size[0]}x{img.size[1]}"
            )

    raw = img.tobytes()  # RGBA が 1 ピクセル 4 バイトで並ぶ

    bad_alpha = set(raw[3::4]) - {0, 255}
    if bad_alpha:
        sample = sorted(bad_alpha)[:5]
        errors.append(
            f"{rel}: アルファに中間値がある {sample}{' ほか' if len(bad_alpha) > 5 else ''}"
            "（アンチエイリアスの縁。二値化すること）"
        )

    colors = {
        (raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 4) if raw[i + 3] != 0
    }
    max_colors = entry.get("max_colors")
    if max_colors and len(colors) > max_colors:
        errors.append(f"{rel}: 色数超過 {len(colors)} 色 / 上限 {max_colors} 色")

    if palette is not None:
        outside = colors - palette
        if outside:
            sample = ["#%02X%02X%02X" % c for c in sorted(outside)[:5]]
            errors.append(
                f"{rel}: パレット外の色が {len(outside)} 色ある 例: {', '.join(sample)}"
            )

    # コマ分割が成立する場合のみ実施（サイズ不一致のときは分割できない）
    if frame and grid and list(img.size) == [frame[0] * grid[0], frame[1] * grid[1]]:
        bottoms = frame_bottoms(img, frame, grid)
        values = {b for (_, _, b) in bottoms if b is not None}
        if len(values) > 1:
            detail = ", ".join(f"行{r}列{c}={b}" for (r, c, b) in bottoms if b is not None)
            errors.append(f"{rel}: 接地ラインが揃っていない ({detail})")
        empty = [f"行{r}列{c}" for (r, c, b) in bottoms if b is None]
        if empty:
            errors.append(f"{rel}: 中身が空のコマがある ({', '.join(empty)})")

    return errors, True


def collect_png_files() -> set[str]:
    assets_dir = REPO_ROOT / "assets"
    found: set[str] = set()
    if not assets_dir.exists():
        return found
    for path in assets_dir.rglob("*.png"):
        if IGNORED_DIRS & set(path.relative_to(assets_dir).parts):
            continue
        found.add(path.relative_to(REPO_ROOT).as_posix())
    return found


def check_autotile(entry: dict) -> list[str]:
    """新しい47形接続アトラスにだけ、形の欠落とセル数の検査を追加する。"""
    if 'autotile' not in entry:
        return []
    rel=entry['path'];data=entry['autotile'];errors=[]
    expected=[]
    for mask in range(256):
        valid=all(not(mask&(1<<d)) or (mask&(1<<a) and mask&(1<<b)) for d,a,b in [(4,0,1),(5,1,2),(6,2,3),(7,3,0)])
        if valid:expected.append(mask)
    if data.get('scheme')!='blob47' or data.get('masks')!=expected:
        errors.append(f'{rel}: 47種類の接続形が欠落・重複・順序不一致')
    phases=data.get('phase_cells',[]);grid=entry.get('grid',[])
    if len(phases)!=2 or not all(isinstance(v,int) and v>0 for v in phases):
        errors.append(f'{rel}: 模様位相の寸法が不正')
    elif len(grid)!=2 or grid[0]*grid[1]!=48*phases[0]*phases[1]:
        errors.append(f'{rel}: 接続形と模様位相の必要セル数が不一致')
    if entry.get('frame')!=[32,32] or data.get('stride')!=48 or data.get('background_index')!=47:
        errors.append(f'{rel}: タイル寸法または背景セル番号が不一致')
    return errors


def check_provenance(entry: dict) -> list[str]:
    """2026年9月26日以降の新項目の出典記録を検査する。"""
    rel = entry.get("path", "<pathなし>")
    if entry.get('source') == 'owner':
        fields=('author','provided_at','original_file','modified')
        errors=[f'{rel}: 依頼者原本の記録 {key} がない' for key in fields if not entry.get(key)]
        if entry.get('author') != '依頼者' or entry.get('license') != 'LicenseRef-Owner-Provided':
            errors.append(f'{rel}: 依頼者原本の作者またはライセンスが不一致')
        original=entry.get('original_file','')
        if not original.startswith('assets/_incoming/owner-2026-09-26/') or '..' in Path(original).parts or not (REPO_ROOT/original).is_file():
            errors.append(f'{rel}: 依頼者の原本ファイルが存在しない、または配置が不正')
        return errors
    if entry.get("source") == "generated":
        fields = ("tool", "generated_at", "prompt_record", "author", "license", "modified")
        errors = [f"{rel}: 生成記録 {key} がない" for key in fields if not entry.get(key)]
        if entry.get("license") != "LicenseRef-Generated-Project":
            errors.append(f"{rel}: 生成素材の識別用ライセンスが不一致")
    else:
        fields = ("source_url", "author", "license", "retrieved_at", "modified")
        errors = [f"{rel}: 出典記録 {key} がない" for key in fields if not entry.get(key)]
        allowed = {"CC0-1.0", "MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "Unlicense"}
        if entry.get("license") not in allowed:
            errors.append(f"{rel}: 許可されていない外部ライセンス")
    return errors


def check_audio(entry: dict) -> list[str]:
    """音を画像として開かず、所在・形式・出典を確かめる。"""
    errors = check_provenance(entry)
    rel = entry.get("path", "")
    path = REPO_ROOT / rel
    kind = entry.get("kind")
    allowed = {"bgm": {".ogg"}, "se": {".ogg", ".wav"}}
    if kind not in allowed or path.suffix.lower() not in allowed.get(kind, set()):
        errors.append(f"{rel}: 音の種別または拡張子が規約外")
    if not rel.startswith(f"assets/audio/{kind}/") or ".." in Path(rel).parts:
        errors.append(f"{rel}: 音の配置が規約外")
    if not path.is_file():
        return errors + [f"{rel}: 音声ファイルが存在しない"]
    try:
        if path.suffix.lower() == ".ogg":
            with path.open("rb") as stream:
                header = stream.read(128)
            if not header.startswith(b"OggS") or b"\x01vorbis" not in header:
                errors.append(f"{rel}: OGG Vorbisのヘッダーではない")
        elif path.suffix.lower() == ".wav":
            with wave.open(str(path), "rb") as stream:
                if stream.getnframes() <= 0:
                    errors.append(f"{rel}: WAVの音声フレームが空")
    except (OSError, EOFError, wave.Error) as exc:
        errors.append(f"{rel}: 音声を読めない ({exc})")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="素材台帳に従って画像を検査する")
    parser.add_argument("--strict", action="store_true", help="台帳外のファイルもエラーにする")
    args = parser.parse_args()

    if not REGISTRY_PATH.exists():
        print(f"素材台帳が見つからない: {REGISTRY_PATH}", file=sys.stderr)
        return 1

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    defaults = registry.get("defaults", {})
    entries = registry.get("assets", [])

    palette_rel = defaults.get("palette")
    palette = load_palette(REPO_ROOT / palette_rel) if palette_rel else None
    if palette_rel and palette is None:
        print(f"[注意] パレット未作成のため色の検査を省略: {palette_rel}")
        print("       作成: python tools/build_palette.py assets --max-colors 64 -o " + palette_rel)

    errors: list[str] = []
    missing: list[str] = []
    registered: set[str] = set()

    # 元の108項目はそのまま、追加項目だけに新しい出典条件を適用する。
    legacy_path = REPO_ROOT / "assets/source_records/legacy-images.json"
    legacy = set(json.loads(legacy_path.read_text(encoding="utf-8"))["paths"])
    palette_cache = {}
    palette_paths = {p.relative_to(REPO_ROOT).as_posix() for p in (REPO_ROOT / "assets/palette").glob("*.gpl")}
    palette_paths.update(e.get("palette", palette_rel) for e in entries)
    for rel in sorted(p for p in palette_paths if p):
        selected = load_palette(REPO_ROOT / rel)
        palette_cache[rel] = selected
        if selected is None:
            errors.append(f"{rel}: 指定パレットが存在しない、または色が空")
        elif len(selected) > 64:
            errors.append(f"{rel}: パレットの色数超過 {len(selected)} 色 / 上限64色")

    for entry in entries:
        entry.setdefault("max_colors", defaults.get("max_colors"))
        registered.add(entry["path"])
        entry_palette = palette_cache.get(entry.get("palette", palette_rel), palette)
        entry_errors, exists = check_asset(entry, entry_palette)
        errors.extend(entry_errors)
        errors.extend(check_autotile(entry))
        if entry["path"] not in legacy or entry.get('source') == 'owner':
            errors.extend(check_provenance(entry))
        if not exists and entry.get("status", "required") == "placeholder":
            missing.append(f"{entry['path']} ({entry.get('kind', '-')})")

    extra = sorted(collect_png_files() - registered)
    if extra:
        label = "エラー" if args.strict else "警告"
        for rel in extra:
            msg = f"{rel}: 素材台帳 (assets/registry.json) に登録されていない"
            if args.strict:
                errors.append(msg)
            else:
                print(f"[{label}] {msg}")

    print(f"検査対象: {len(entries)} 件")

    audio_entries = registry.get("audio", [])
    audio_registered = set()
    for entry in audio_entries:
        rel = entry.get("path", "")
        if rel in audio_registered:
            errors.append(f"{rel}: 音の台帳登録が重複")
        audio_registered.add(rel)
        errors.extend(check_audio(entry))
    for path in (REPO_ROOT / "assets").rglob("*"):
        if path.suffix.lower() not in {".ogg", ".wav"} or IGNORED_DIRS & set(path.parts):
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel not in audio_registered:
            errors.append(f"{rel}: 音の台帳に登録されていない")
    print(f"音の検査対象: {len(audio_entries)} 件 / パレット: {len(palette_cache)} 件")

    if missing:
        print(f"\n--- 不足素材 ({len(missing)} 件) ---")
        for item in missing:
            print(f"  未作成: {item}")

    if errors:
        print(f"\n--- エラー ({len(errors)} 件) ---", file=sys.stderr)
        for err in errors:
            print(f"  NG {err}", file=sys.stderr)
        return 1

    print("\n問題なし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
