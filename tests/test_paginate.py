import pytest

from paginate import (
    PAGE_H,
    PAGE_W,
    Layout,
    compute_scale,
    layout_for,
    mm_to_px,
    page_height,
)


def test_mm_to_px_uses_300_dpi():
    assert mm_to_px(0) == 0
    assert mm_to_px(10) == 118
    assert mm_to_px(30) == 354
    assert mm_to_px(210) == 2480
    assert mm_to_px(297) == 3508


def test_page_canvas_is_a4_at_300_dpi():
    assert (PAGE_W, PAGE_H) == (2480, 3508)


@pytest.mark.parametrize(
    "margin_mm, expected",
    [
        (0, Layout(margin_px=0, usable_w=2480, usable_h=3508)),
        (10, Layout(margin_px=118, usable_w=2244, usable_h=3272)),
        (30, Layout(margin_px=354, usable_w=1772, usable_h=2800)),
    ],
)
def test_layout_for_margin(margin_mm, expected):
    assert layout_for(margin_mm) == expected


def test_fit_width_scale_fills_usable_width():
    scale, x_offset = compute_scale(1920, 2244, keep_actual_size=False)
    assert scale == pytest.approx(2244 / 1920)
    assert x_offset == 0


def test_fit_width_upscales_small_image():
    scale, x_offset = compute_scale(500, 2244, keep_actual_size=False)
    assert scale == pytest.approx(2244 / 500)
    assert x_offset == 0


def test_actual_size_uses_96_dpi_and_centers():
    scale, x_offset = compute_scale(500, 2244, keep_actual_size=True)
    assert scale == pytest.approx(3.125)
    # (2244 - 500 * 3.125) / 2 = 340.75 -> 341
    assert x_offset == 341


def test_actual_size_falls_back_to_fit_width_when_too_wide():
    scale, x_offset = compute_scale(1920, 2244, keep_actual_size=True)
    assert scale == pytest.approx(2244 / 1920)
    assert x_offset == 0


def test_page_height_floors_source_rows_per_page():
    assert page_height(1.0, 3508) == 3508
    assert page_height(2244 / 1920, 3272) == 2799
    assert page_height(3.125, 2800) == 896
