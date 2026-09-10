import pytest
from PIL import Image

from background import (
    BG_BORDER_MIN,
    BG_FADE_KEEP,
    BG_FADE_MIN,
    BG_TOLERANCE,
    BG_WHITE_MAX,
    apply_background,
    detect_background,
    faded_color,
    is_white,
)

GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)


def test_constants_match_web_version():
    assert BG_TOLERANCE == 16
    assert BG_WHITE_MAX == 3
    assert BG_FADE_KEEP == 0.15
    assert BG_FADE_MIN == 10
    assert BG_BORDER_MIN == 0.3


def test_is_white_within_three_levels():
    assert is_white((255, 255, 255)) is True
    assert is_white((252, 252, 252)) is True
    assert is_white((251, 255, 255)) is False


def test_faded_color_keeps_minimum_trace_for_light_backgrounds():
    # (233,233,236): 흰색과의 차이 (22,22,19), 최대 22 → 15%는 3.3이지만 최소 10을 유지
    assert faded_color((233, 233, 236)) == (245, 245, 246)


def test_faded_color_keeps_fifteen_percent_for_dark_backgrounds():
    # 검정: 차이 255 → 15% = 38.25 → 255 − 38 = 217
    assert faded_color((0, 0, 0)) == (217, 217, 217)


def _image(size, fill):
    return Image.new("RGB", size, fill)


def test_detect_prefers_border_color_over_center_content():
    im = _image((200, 100), GRAY)
    im.paste(RED, (40, 20, 160, 80))
    assert detect_background(im) == GRAY


def test_detect_falls_back_to_global_dominant_when_border_is_mixed():
    im = _image((200, 200), GREEN)
    colors = [(0, 0, 0), (64, 0, 0), (128, 0, 0), (192, 0, 0),
              (0, 64, 0), (0, 128, 0), (0, 192, 0), (0, 0, 64)]
    band = 4  # 2% of 200
    for y in range(200):
        for x in range(200):
            if x < band or x >= 200 - band or y < band or y >= 200 - band:
                im.putpixel((x, y), colors[((x + y) // 25) % 8])
    assert detect_background(im) == GREEN


def test_detect_returns_white_for_white_background_with_content():
    im = _image((200, 100), WHITE)
    im.paste((0, 0, 0), (20, 40, 180, 44))
    assert detect_background(im) == WHITE


def test_detect_resizes_wide_images_before_sampling():
    im = _image((1920, 300), GRAY)
    im.paste(RED, (300, 50, 1600, 250))
    assert detect_background(im) == GRAY


def _row(pixels):
    im = Image.new("RGB", (len(pixels), 1))
    for x, p in enumerate(pixels):
        im.putpixel((x, 0), p)
    return im


def _pixels(im):
    return [im.getpixel((x, 0)) for x in range(im.width)]


def test_remove_turns_background_pixels_white_within_tolerance():
    im = _row([GRAY, (210, 200, 200), (230, 200, 200), WHITE])
    out = apply_background(im, GRAY, "remove")
    assert _pixels(out) == [WHITE, WHITE, (230, 200, 200), WHITE]


def test_fade_paints_background_pixels_with_faded_color():
    im = _row([GRAY, (210, 200, 200), (230, 200, 200)])
    out = apply_background(im, GRAY, "fade")
    assert _pixels(out) == [(245, 245, 245), (245, 245, 245), (230, 200, 200)]


def test_apply_does_not_mutate_input():
    im = _row([GRAY, RED])
    apply_background(im, GRAY, "remove")
    assert _pixels(im) == [GRAY, RED]


def test_apply_is_noop_when_background_is_already_white():
    im = _row([(250, 250, 250), RED])
    out = apply_background(im, WHITE, "remove")
    assert _pixels(out) == [(250, 250, 250), RED]


def test_apply_rejects_unknown_mode():
    with pytest.raises(ValueError):
        apply_background(_row([GRAY]), GRAY, "blur")
