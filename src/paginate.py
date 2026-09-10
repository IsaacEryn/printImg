"""A4 페이지 레이아웃, 배율, 분할 위치 계산. Tkinter와 파일 I/O를 모른다."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from PIL import Image

A4_W_MM = 210.0
A4_H_MM = 297.0
OUTPUT_DPI = 300
SOURCE_DPI = 96


def mm_to_px(mm: float) -> int:
    """mm를 출력 해상도(300 DPI) 픽셀로 반올림."""
    return round(mm / 25.4 * OUTPUT_DPI)


PAGE_W = mm_to_px(A4_W_MM)
PAGE_H = mm_to_px(A4_H_MM)


@dataclass(frozen=True)
class Layout:
    """여백을 뺀 인쇄 가능 영역. 단위는 출력 픽셀."""

    margin_px: int
    usable_w: int
    usable_h: int


def layout_for(margin_mm: float) -> Layout:
    margin_px = mm_to_px(margin_mm)
    return Layout(
        margin_px=margin_px,
        usable_w=PAGE_W - 2 * margin_px,
        usable_h=PAGE_H - 2 * margin_px,
    )


def compute_scale(img_w: int, usable_w: int, keep_actual_size: bool) -> tuple[float, int]:
    """원본 1 px가 출력 몇 px가 되는지와, 인쇄 영역 안의 가로 오프셋을 돌려준다.

    폭 맞춤: 항상 usable_w를 꽉 채운다.
    원본 크기: 96 DPI 기준 실제 크기. 폭이 넘치면 폭 맞춤으로 전환.
    """
    if keep_actual_size:
        scale = OUTPUT_DPI / SOURCE_DPI
        scaled_w = img_w * scale
        if scaled_w <= usable_w:
            return scale, round((usable_w - scaled_w) / 2)
    return usable_w / img_w, 0


def page_height(scale: float, usable_h: int) -> int:
    """한 페이지에 들어가는 원본 픽셀 높이."""
    return math.floor(usable_h / scale)


BLANK_THRESHOLD = 8
SEARCH_RATIO = 0.3


def is_blank_row(gray: Image.Image, y: int) -> bool:
    """L 모드 이미지의 y번째 가로줄이 단색(빈 줄)인지."""
    lo, hi = gray.crop((0, y, gray.width, y + 1)).getextrema()
    return hi - lo <= BLANK_THRESHOLD


def split_rows(img_h: int, page_h: int, is_blank: Callable[[int], bool]) -> list[tuple[int, int]]:
    """이미지를 원본 픽셀 기준 (y_start, y_end) 구간으로 나눈다.

    이상적인 경계에서 위로 page_h*SEARCH_RATIO 안에 빈 줄이 있으면 거기서,
    없으면 이상적인 경계에서 자른다.
    """
    if page_h < 1:
        raise ValueError("page_h must be >= 1")
    search = int(page_h * SEARCH_RATIO)
    slices: list[tuple[int, int]] = []
    y0 = 0
    while img_h - y0 > page_h:
        y_ideal = y0 + page_h
        cut = y_ideal
        for y in range(y_ideal, y_ideal - search, -1):
            if is_blank(y):
                cut = y
                break
        slices.append((y0, cut))
        y0 = cut
    slices.append((y0, img_h))
    return slices


@dataclass(frozen=True)
class Options:
    keep_actual_size: bool = False
    margin_mm: float = 10.0


@dataclass(frozen=True)
class Plan:
    scale: float
    x_offset: int
    margin_px: int
    usable_w: int
    usable_h: int
    slices: list[tuple[int, int]]


def plan(image: Image.Image, options: Options) -> Plan:
    """RGB 이미지와 옵션으로부터 배율·오프셋·분할 구간을 계산한다."""
    img_w, img_h = image.size
    layout = layout_for(options.margin_mm)
    scale, x_offset = compute_scale(img_w, layout.usable_w, options.keep_actual_size)
    page_h = page_height(scale, layout.usable_h)
    gray = image.convert("L")
    slices = split_rows(img_h, page_h, lambda y: is_blank_row(gray, y))
    return Plan(
        scale=scale,
        x_offset=x_offset,
        margin_px=layout.margin_px,
        usable_w=layout.usable_w,
        usable_h=layout.usable_h,
        slices=slices,
    )
