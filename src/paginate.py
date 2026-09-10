"""A4 페이지 레이아웃, 배율, 분할 위치 계산. Tkinter와 파일 I/O를 모른다."""

from __future__ import annotations

import math
from dataclasses import dataclass

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
