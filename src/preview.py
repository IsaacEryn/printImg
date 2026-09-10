"""인쇄 전 미리보기 창: 페이지 썸네일 목록 + 프린터 선택 + 인쇄 버튼."""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from PIL import Image, ImageTk

THUMB_WIDTH = 420      # 썸네일 폭 (px)
VISIBLE_HEIGHT = 640   # 스크롤 영역 높이 (px)
GAP = 16


def wheel_steps(delta: int, platform: str = sys.platform) -> int:
    """<MouseWheel> delta를 yview_scroll 단위 수로 바꾼다.

    Windows는 한 칸에 ±120, 맥은 ±1(트랙패드 가속 시 더 큼)이라 맥에서 120으로 나누면 항상 0이 된다.
    """
    if platform == "darwin":
        return -delta
    return -int(delta / 120)


class PreviewWindow(tk.Toplevel):
    """pages를 보여주고, 사용자가 [인쇄]를 누르면 on_print(printer_name)를 부른다."""

    def __init__(
        self,
        parent: tk.Misc,
        pages: list[Image.Image],
        printers: list[str],
        default_printer: str | None,
        on_print: Callable[[str], None],
    ) -> None:
        super().__init__(parent)
        self.title(f"인쇄 미리보기 · {len(pages)}페이지")
        self.transient(parent)
        self.on_print = on_print
        self.photos: list[ImageTk.PhotoImage] = []  # Tk가 참조를 잃지 않도록 보관
        self._build(pages, printers, default_printer)
        self.grab_set()

    def _build(self, pages: list[Image.Image], printers: list[str], default: str | None) -> None:
        outer = ttk.Frame(self, padding=12)
        outer.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        canvas = tk.Canvas(
            outer, width=THUMB_WIDTH + 2 * GAP, height=VISIBLE_HEIGHT,
            background="#d9d9de", highlightthickness=0,
        )
        bar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=bar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        bar.grid(row=0, column=1, sticky="ns")
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        y = GAP
        for i, page in enumerate(pages, start=1):
            thumb_h = round(page.height * THUMB_WIDTH / page.width)
            thumb = page.resize((THUMB_WIDTH, thumb_h), Image.Resampling.BOX)
            photo = ImageTk.PhotoImage(thumb)
            self.photos.append(photo)
            canvas.create_image(GAP, y, image=photo, anchor="nw")
            canvas.create_text(
                GAP + THUMB_WIDTH / 2, y + thumb_h + 4, text=f"{i} / {len(pages)}", anchor="n",
            )
            y += thumb_h + 24 + GAP
        canvas.configure(scrollregion=(0, 0, THUMB_WIDTH + 2 * GAP, y))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(wheel_steps(e.delta), "units"))
        # X11(리눅스)은 휠이 버튼 4/5로 온다.
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        bottom = ttk.Frame(outer)
        bottom.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Label(bottom, text="프린터").pack(side="left")
        self.printer = tk.StringVar(value=default or (printers[0] if printers else ""))
        ttk.Combobox(
            bottom, textvariable=self.printer, values=printers, state="readonly", width=36,
        ).pack(side="left", padx=(6, 12))
        ttk.Button(bottom, text="닫기", command=self.destroy).pack(side="right")
        self.print_button = ttk.Button(bottom, text="인쇄", command=self._print)
        self.print_button.pack(side="right", padx=(0, 8))
        if not printers:
            self.print_button.config(state="disabled")

    def _print(self) -> None:
        name = self.printer.get()
        if not name:
            return
        self.print_button.config(state="disabled")
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            self.on_print(name)
        finally:
            self.destroy()
