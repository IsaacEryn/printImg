"""이미지 파일을 열어 RGB로 통일한다."""

from __future__ import annotations

import os

from PIL import Image, ImageOps

SUPPORTED_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")


def flatten_to_rgb(im: Image.Image) -> Image.Image:
    """투명 영역은 흰 배경 위에 합성하고, 나머지는 RGB로 변환한다."""
    has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    if has_alpha:
        rgba = im.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return im.convert("RGB")


def load_image(path: str | os.PathLike) -> Image.Image:
    """파일을 열고 EXIF 회전을 적용한 뒤 RGB로 돌려준다. 예외는 호출자가 처리한다."""
    with Image.open(path) as im:
        im.load()  # 첫 프레임을 메모리에 올린다. 움직이는 GIF는 첫 프레임만 쓴다.
        upright = ImageOps.exif_transpose(im)
        return flatten_to_rgb(upright)
