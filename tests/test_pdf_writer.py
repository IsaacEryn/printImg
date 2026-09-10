import re

from PIL import Image

from paginate import PAGE_H, PAGE_W, Plan
from pdf_writer import render_pages, write

RED = (255, 0, 0)
WHITE = (255, 255, 255)


def _plan(scale, x_offset, margin_px, slices):
    return Plan(
        scale=scale,
        x_offset=x_offset,
        margin_px=margin_px,
        usable_w=PAGE_W - 2 * margin_px,
        usable_h=PAGE_H - 2 * margin_px,
        slices=slices,
    )


def test_render_places_slices_top_left_inside_margin():
    im = Image.new("RGB", (71, 250), RED)
    pages = render_pages(im, _plan(1.0, 0, 118, [(0, 100), (100, 250)]))
    assert len(pages) == 2
    assert all(p.size == (PAGE_W, PAGE_H) and p.mode == "RGB" for p in pages)

    first, second = pages
    assert first.getpixel((118, 118)) == RED
    assert first.getpixel((117, 117)) == WHITE
    assert first.getpixel((118 + 70, 118 + 99)) == RED
    assert first.getpixel((118 + 71, 118)) == WHITE
    assert first.getpixel((118, 118 + 100)) == WHITE

    assert second.getpixel((118, 118 + 149)) == RED
    assert second.getpixel((118, 118 + 150)) == WHITE


def test_render_scales_slice_and_applies_x_offset():
    im = Image.new("RGB", (500, 10), RED)
    pages = render_pages(im, _plan(3.125, 341, 118, [(0, 10)]))
    page = pages[0]
    left = 118 + 341
    width = round(500 * 3.125)  # 1562
    assert page.getpixel((left, 118)) == RED
    assert page.getpixel((left - 1, 118)) == WHITE
    assert page.getpixel((left + width - 1, 118)) == RED
    assert page.getpixel((left + width, 118)) == WHITE
    assert page.getpixel((left, 118 + round(10 * 3.125) - 1)) == RED


def test_render_clamps_slice_height_to_usable_area():
    im = Image.new("RGB", (71, 3300), RED)
    plan = _plan(1.0, 0, 118, [(0, 3300)])  # 3300 > usable_h 3272
    page = render_pages(im, plan)[0]
    assert page.getpixel((118, 118 + 3271)) == RED
    assert page.getpixel((118, 118 + 3272)) == WHITE


def test_write_creates_multipage_a4_pdf(tmp_path):
    im = Image.new("RGB", (71, 250), RED)
    out = tmp_path / "out.pdf"
    count = write(im, _plan(1.0, 0, 118, [(0, 100), (100, 200), (200, 250)]), out)
    assert count == 3
    data = out.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(re.findall(rb"/Type\s*/Page\b(?!s)", data)) == 3
    assert re.search(rb"/MediaBox\s*\[\s*0\s+0\s+595\.2\s+841\.92\s*\]", data)
