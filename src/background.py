"""배경색 감지와 제거·흐리게 처리. Pillow만 사용한다."""

from __future__ import annotations

from PIL import Image, ImageChops, ImageStat

RGB = tuple[int, int, int]

BG_TOLERANCE = 16      # 배경색과 채널당 이 차이 이하면 배경 픽셀
BG_WHITE_MAX = 3       # 배경색이 흰색과 채널당 이 차이 이하면 처리할 것 없음
BG_FADE_KEEP = 0.15    # 흐리게: 흰색과의 차이를 이 비율만큼만 남김
BG_FADE_MIN = 10       # 흐리게: 그래도 최소 이만큼은 흰색과 다르게 (흔적 유지)
BG_BORDER_RATIO = 0.02 # 테두리 띠 두께 (가로·세로 각각 이 비율)
BG_BORDER_MIN = 0.3    # 테두리 최빈색 비중이 이보다 낮으면 전체 최빈색으로 폴백
DETECT_WIDTH = 200     # 감지용 축소 폭
BIN_MASK = 0xF8        # 채널당 8단계(5비트)로 묶는 마스크

MODES = ("remove", "fade")


def is_white(bg: RGB) -> bool:
    return all(255 - v <= BG_WHITE_MAX for v in bg)


def faded_color(bg: RGB) -> RGB:
    """흰색과의 차이를 BG_FADE_KEEP만큼만 남기되 최소 BG_FADE_MIN은 유지한 색."""
    diff = [255 - v for v in bg]
    s = max(diff)
    if s == 0:
        return bg
    t = max(BG_FADE_MIN, s * BG_FADE_KEEP) / s
    return tuple(round(255 - d * t) for d in diff)  # type: ignore[return-value]


def _dominant(small: Image.Image, regions: list[tuple[int, int, int, int]]) -> tuple[RGB, float] | None:
    """regions(크롭 박스들) 안 픽셀의 최빈 색 묶음 → (묶음의 평균색, 비중)."""
    binned = small.point(lambda v: v & BIN_MASK)
    counts: dict[RGB, int] = {}
    total = 0
    for box in regions:
        strip = binned.crop(box)
        for n, color in strip.getcolors(strip.width * strip.height) or []:
            counts[color] = counts.get(color, 0) + n
            total += n
    if not counts:
        return None
    key = max(counts, key=counts.get)  # type: ignore[arg-type]

    in_bin = ImageChops.difference(binned, Image.new("RGB", small.size, key)).convert("L")
    in_bin = in_bin.point(lambda v: 255 if v == 0 else 0)
    in_region = Image.new("L", small.size, 0)
    for box in regions:
        in_region.paste(255, box)
    mean = ImageStat.Stat(small, ImageChops.multiply(in_bin, in_region)).mean
    return tuple(round(v) for v in mean), counts[key] / total  # type: ignore[return-value]


def detect_background(image: Image.Image) -> RGB | None:
    """배경색 추정. 가장자리 띠의 최빈색을 우선하고, 뒤섞여 있으면 전체 최빈색으로 폴백."""
    w = DETECT_WIDTH
    h = max(1, round(image.height * w / image.width))
    small = image.convert("RGB").resize((w, h), Image.Resampling.BOX)

    bw = max(1, round(w * BG_BORDER_RATIO))
    bh = max(1, round(h * BG_BORDER_RATIO))
    whole = [(0, 0, w, h)]
    if w > 2 * bw and h > 2 * bh:
        border = [
            (0, 0, w, bh),            # 위
            (0, h - bh, w, h),        # 아래
            (0, bh, bw, h - bh),      # 왼쪽 (위·아래 띠 제외)
            (w - bw, bh, w, h - bh),  # 오른쪽
        ]
    else:
        border = whole

    result = _dominant(small, border)
    if result and result[1] >= BG_BORDER_MIN:
        return result[0]
    result = _dominant(small, whole)
    return result[0] if result else None


def apply_background(image: Image.Image, bg: RGB, mode: str) -> Image.Image:
    """배경색과 채널당 BG_TOLERANCE 이하로 가까운 픽셀을 흰색(remove) 또는 연한 색(fade)으로 바꾼 새 이미지."""
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode}")
    if is_white(bg):
        return image.copy()
    diff = ImageChops.difference(image, Image.new("RGB", image.size, bg))
    r, g, b = diff.split()
    max_diff = ImageChops.lighter(ImageChops.lighter(r, g), b)
    mask = max_diff.point(lambda v: 255 if v <= BG_TOLERANCE else 0)
    fill = (255, 255, 255) if mode == "remove" else faded_color(bg)
    out = image.copy()
    out.paste(fill, mask=mask)
    return out
