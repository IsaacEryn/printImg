"""분할 계획대로 A4 캔버스에 렌더링하고 다중 페이지 PDF로 저장한다."""

from __future__ import annotations

import os
import tempfile

from PIL import Image

from paginate import OUTPUT_DPI, PAGE_H, PAGE_W, Plan

JPEG_QUALITY = 95  # 기본값 75는 300 DPI 텍스트에 링잉 아티팩트를 남긴다.


def render_pages(image: Image.Image, plan: Plan) -> list[Image.Image]:
    """구간마다 조각을 잘라 리사이즈하고 흰 A4 캔버스의 여백 안쪽 상단에 붙인다."""
    img_w = image.width
    target_w = round(img_w * plan.scale)
    pages: list[Image.Image] = []
    for y0, y1 in plan.slices:
        piece = image.crop((0, y0, img_w, y1))
        target_h = min(round((y1 - y0) * plan.scale), plan.usable_h)
        piece = piece.resize((max(target_w, 1), max(target_h, 1)), Image.LANCZOS)
        page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        page.paste(piece, (plan.margin_px + plan.x_offset, plan.margin_px))
        pages.append(page)
    return pages


def save_pages(pages: list[Image.Image], out_path: str | os.PathLike) -> int:
    """렌더링된 페이지들을 다중 페이지 PDF로 저장하고 페이지 수를 돌려준다.

    같은 폴더의 임시 파일에 쓴 뒤 os.replace로 바꿔치기해, 저장 도중 실패해도 기존 파일이 반쯤 잘린
    상태로 남지 않는다. 권한 오류는 mkstemp나 replace에서 PermissionError로 올라온다.
    """
    out_path = os.fspath(out_path)
    out_dir = os.path.dirname(os.path.abspath(out_path))
    fd, tmp = tempfile.mkstemp(prefix=".printimg-", suffix=".pdf", dir=out_dir)
    os.close(fd)
    try:
        pages[0].save(
            tmp,
            "PDF",
            resolution=float(OUTPUT_DPI),
            save_all=True,
            append_images=pages[1:],
            quality=JPEG_QUALITY,
        )
        # mkstemp는 0600으로 만든다. 일반 파일처럼 umask를 적용한 권한으로 맞춘다.
        umask = os.umask(0)
        os.umask(umask)
        os.chmod(tmp, 0o666 & ~umask)
        os.replace(tmp, out_path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return len(pages)


def write(image: Image.Image, plan: Plan, out_path: str | os.PathLike) -> int:
    """PDF를 저장하고 페이지 수를 돌려준다. 파일 오류는 호출자가 처리한다."""
    return save_pages(render_pages(image, plan), out_path)
