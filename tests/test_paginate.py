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


from paginate import Options, Plan, plan


def test_options_defaults():
    assert Options() == Options(keep_actual_size=False, margin_mm=10.0)


def test_plan_end_to_end_cuts_at_blank_row():
    # 폭 71, 여백 0 → scale = 2480/71, page_h = floor(3508*71/2480) = 100
    # 단색 줄은 전부 빈 줄로 판정되므로, 세로 줄무늬로 "내용 있는 줄"을 만든다.
    im = Image.new("RGB", (71, 250), "black")
    for y in range(250):
        for x in range(0, 71, 2):
            im.putpixel((x, y), (255, 255, 255))
    for x in range(71):
        im.putpixel((x, 90), (255, 255, 255))  # 90번 줄만 전부 흰색 = 빈 줄
    p = plan(im, Options(keep_actual_size=False, margin_mm=0))
    assert isinstance(p, Plan)
    assert p.margin_px == 0
    assert (p.usable_w, p.usable_h) == (2480, 3508)
    assert p.scale == pytest.approx(2480 / 71)
    assert p.x_offset == 0
    assert p.slices == [(0, 90), (90, 190), (190, 250)]


def test_plan_actual_size_centers_narrow_image():
    im = Image.new("RGB", (500, 10), "black")
    p = plan(im, Options(keep_actual_size=True, margin_mm=10))
    assert p.scale == pytest.approx(3.125)
    assert p.x_offset == 341
    assert p.slices == [(0, 10)]


from paginate import smart_cut_count


def _striped_with_blank_row(blank_y):
    im = Image.new("RGB", (71, 250), "black")
    for y in range(250):
        for x in range(0, 71, 2):
            im.putpixel((x, y), (255, 255, 255))
    for x in range(71):
        im.putpixel((x, blank_y), (255, 255, 255))
    return im


def test_options_smart_split_defaults_on():
    assert Options().smart_split is True


def test_plan_without_smart_split_uses_equal_split():
    im = _striped_with_blank_row(90)
    p = plan(im, Options(margin_mm=0, smart_split=False))
    assert p.slices == [(0, 100), (100, 200), (200, 250)]


def test_smart_cut_count_counts_cuts_on_blank_rows():
    im = _striped_with_blank_row(90)
    p = plan(im, Options(margin_mm=0))
    assert p.slices == [(0, 90), (90, 190), (190, 250)]
    assert smart_cut_count(im, p) == 1  # 90은 빈 줄, 190은 등분


def test_smart_cut_count_is_zero_for_single_page():
    im = Image.new("RGB", (71, 50), "black")
    assert smart_cut_count(im, plan(im, Options(margin_mm=0))) == 0
