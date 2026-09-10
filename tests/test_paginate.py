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


from PIL import Image

from paginate import BLANK_THRESHOLD, SEARCH_RATIO, is_blank_row, split_rows


def _gray_rows(rows):
    """rows: 각 줄의 픽셀값 리스트. 같은 폭의 L 이미지를 만든다."""
    h = len(rows)
    w = len(rows[0])
    im = Image.new("L", (w, h))
    for y, row in enumerate(rows):
        for x, v in enumerate(row):
            im.putpixel((x, y), v)
    return im


def test_constants_match_spec():
    assert BLANK_THRESHOLD == 8
    assert SEARCH_RATIO == 0.3


def test_blank_row_detection():
    gray = _gray_rows(
        [
            [255, 255, 255, 255],  # 흰 줄
            [128, 128, 128, 128],  # 회색 단색 줄
            [0, 255, 0, 255],      # 흑백 혼합
            [100, 109, 100, 109],  # 차이 9: 임계값 바로 위
            [100, 108, 100, 108],  # 차이 8: 임계값
        ]
    )
    assert is_blank_row(gray, 0) is True
    assert is_blank_row(gray, 1) is True
    assert is_blank_row(gray, 2) is False
    assert is_blank_row(gray, 3) is False
    assert is_blank_row(gray, 4) is True


def never_blank(y):
    return False


def test_single_page_when_image_fits():
    assert split_rows(100, 100, never_blank) == [(0, 100)]
    assert split_rows(50, 100, never_blank) == [(0, 50)]


def test_equal_split_when_no_blank_rows():
    assert split_rows(250, 100, never_blank) == [(0, 100), (100, 200), (200, 250)]


def test_cuts_at_blank_row_above_ideal_boundary():
    blank = {90}
    slices = split_rows(250, 100, lambda y: y in blank)
    # 90에서 자르고, 다음 페이지는 90~190 (빈 줄 없음 → 등분), 나머지 190~250
    assert slices == [(0, 90), (90, 190), (190, 250)]


def test_prefers_blank_row_closest_to_ideal():
    blank = {85, 95}
    assert split_rows(250, 100, lambda y: y in blank)[0] == (0, 95)


def test_blank_row_exactly_at_ideal_is_used():
    blank = {100}
    assert split_rows(250, 100, lambda y: y in blank)[0] == (0, 100)


def test_ignores_blank_row_outside_search_window():
    # 탐색 범위는 page_h*0.3 = 30 → 71~100만 본다. 60은 무시.
    blank = {60}
    assert split_rows(250, 100, lambda y: y in blank) == [(0, 100), (100, 200), (200, 250)]


def test_slices_are_contiguous_and_cover_image():
    blank = {33, 77, 140, 141, 199, 260}
    img_h = 333
    slices = split_rows(img_h, 100, lambda y: y in blank)
    assert slices[0][0] == 0
    assert slices[-1][1] == img_h
    for (a0, a1), (b0, b1) in zip(slices, slices[1:]):
        assert a1 == b0
        assert a1 > a0
    assert all(y1 - y0 <= 100 for y0, y1 in slices)


def test_rejects_non_positive_page_height():
    with pytest.raises(ValueError):
        split_rows(100, 0, never_blank)
