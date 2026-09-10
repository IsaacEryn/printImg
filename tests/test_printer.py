from printer import page_box


def test_page_box_fills_physical_page_when_aspect_matches():
    # 600 DPI A4 프린터, 인쇄 불가 오프셋 (100, 100). 우리 페이지는 300 DPI A4.
    assert page_box(4960, 7016, 100, 100, 2480, 3508) == (-100, -100, 4860, 6916)


def test_page_box_keeps_aspect_and_centers_on_letter():
    # 600 DPI Letter (5100×6600): 높이에 맞추고 가로 가운데 정렬
    assert page_box(5100, 6600, 0, 0, 2480, 3508) == (217, 0, 4883, 6600)


def test_page_box_subtracts_printable_offset():
    assert page_box(5100, 6600, 50, 60, 2480, 3508) == (167, -60, 4833, 6540)


def test_page_box_fits_narrow_paper_by_width():
    # 용지가 페이지보다 세로로 길쭉하면 폭에 맞추고 세로 가운데 정렬
    assert page_box(2000, 4000, 0, 0, 2480, 3508) == (0, 586, 2000, 3415)
