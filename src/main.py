"""PrintImg: 이미지를 A4 다중 페이지 PDF로 만드는 Tkinter 앱."""

from __future__ import annotations

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

# `python src/main.py`로 실행해도 옆 모듈을 찾도록 한다. PyInstaller는 spec의 pathex로 처리.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, UnidentifiedImageError  # noqa: E402

from background import apply_background, detect_background, is_white  # noqa: E402
from image_loader import SUPPORTED_EXTENSIONS, load_image  # noqa: E402
from paginate import Options, Plan, plan, smart_cut_count  # noqa: E402
from pdf_writer import write  # noqa: E402

APP_TITLE = "PrintImg"
MARGIN_MIN = 0
MARGIN_MAX = 30
MARGIN_DEFAULT = 10
MAX_PAGES = 50
BG_MODES = {"제거": "remove", "흐리게": "fade"}

RGB = tuple[int, int, int]


class UserError(Exception):
    """사용자에게 그대로 보여줄 오류 메시지."""


def to_hex(rgb: RGB) -> str:
    return "#" + "".join(f"{v:02x}" for v in rgb)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.resizable(False, False)
        self.image_path: Path | None = None
        self.image: Image.Image | None = None  # 선택 시 로드해 둔 RGB 원본
        self.bg_color: RGB | None = None       # 감지되거나 직접 고른 배경색
        self.keep_actual = tk.BooleanVar(value=False)
        self.smart_split = tk.BooleanVar(value=True)
        self.bg_on = tk.BooleanVar(value=False)
        self.bg_mode = tk.StringVar(value="제거")
        self.margin = tk.StringVar(value=str(MARGIN_DEFAULT))
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.grid()

        ttk.Button(frame, text="이미지 선택…", command=self.choose_file).grid(
            row=0, column=0, sticky="w"
        )
        self.file_label = ttk.Label(frame, text="선택된 파일 없음", wraplength=360)
        self.file_label.grid(row=0, column=1, padx=(8, 0), sticky="w")

        ttk.Checkbutton(frame, text="원본 크기 유지", variable=self.keep_actual).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        ttk.Checkbutton(frame, text="빈 줄에 맞춰 자르기", variable=self.smart_split).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )

        bg_row = ttk.Frame(frame)
        bg_row.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Checkbutton(
            bg_row, text="배경색", variable=self.bg_on, command=self._sync_bg_widgets
        ).pack(side="left")
        self.bg_mode_box = ttk.Combobox(
            bg_row, textvariable=self.bg_mode, values=list(BG_MODES), width=6, state="readonly"
        )
        self.bg_mode_box.pack(side="left", padx=(6, 0))
        self.bg_button = tk.Button(
            bg_row, text="#ffffff", width=8, relief="groove", command=self.pick_bg_color
        )
        self.bg_button.pack(side="left", padx=(6, 0))
        self._sync_bg_widgets()

        ttk.Label(frame, text="여백 (mm)").grid(row=4, column=0, sticky="w", pady=(8, 0))
        ttk.Spinbox(
            frame, from_=MARGIN_MIN, to=MARGIN_MAX, textvariable=self.margin, width=5
        ).grid(row=4, column=1, sticky="w", pady=(8, 0))

        self.make_button = ttk.Button(
            frame, text="PDF 만들기", command=self.make_pdf, state="disabled"
        )
        self.make_button.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(16, 0))

        self.status = ttk.Label(frame, text="", wraplength=360)
        self.status.grid(row=6, column=0, columnspan=2, sticky="w", pady=(12, 0))

    # ----- 사용자 조작 -----

    def choose_file(self) -> None:
        patterns = " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)
        path = filedialog.askopenfilename(
            title="이미지 선택",
            filetypes=[("이미지 파일", patterns), ("모든 파일", "*.*")],
        )
        if not path:
            return
        try:
            image = load_image(path)
        except Image.DecompressionBombError:
            messagebox.showerror(APP_TITLE, "이미지가 너무 큽니다.")
            return
        except (UnidentifiedImageError, OSError):
            messagebox.showerror(APP_TITLE, f"이미지를 열 수 없습니다.\n{Path(path).name}")
            return

        self.image_path = Path(path)
        self.image = image
        self.bg_color = detect_background(image)
        self._show_bg_color()
        self.file_label.config(text=f"{self.image_path.name} · {image.width} × {image.height}")
        self.make_button.config(state="normal")
        self.status.config(text="")

    def pick_bg_color(self) -> None:
        initial = to_hex(self.bg_color) if self.bg_color else "#ffffff"
        rgb, _ = colorchooser.askcolor(color=initial, title="배경색 선택", parent=self)
        if rgb is None:
            return
        self.bg_color = tuple(round(v) for v in rgb)  # type: ignore[assignment]
        self._show_bg_color()

    def make_pdf(self) -> None:
        if self.image_path is None or self.image is None:
            return
        options = self._read_options()
        if options is None:
            return

        out_path = self.image_path.with_suffix(".pdf")
        if out_path.exists() and not messagebox.askyesno(
            APP_TITLE, f"{out_path.name} 파일이 이미 있습니다. 덮어쓸까요?"
        ):
            return

        self._set_busy(True)
        try:
            image, p, notes = self._prepare(options)
            try:
                page_count = write(image, p, out_path)
            except PermissionError:
                raise UserError(f"{out_path.name} 파일이 열려 있습니다. 닫고 다시 시도하세요.")
            except OSError as e:
                raise UserError(f"PDF를 저장할 수 없습니다.\n{out_path.name}\n{e}")
            summary = f"{page_count}페이지 생성" + (f" ({', '.join(notes)})" if notes else "")
        except UserError as e:
            self._set_busy(False)
            messagebox.showerror(APP_TITLE, str(e))
            return
        except Exception as e:
            # console=False 빌드에서는 이 오류가 아무 곳에도 안 보이므로 반드시 메시지로 표시한다.
            self._set_busy(False)
            messagebox.showerror(APP_TITLE, f"PDF를 만들 수 없습니다.\n{type(e).__name__}: {e}")
            return
        self._set_busy(False)

        self.status.config(text=f"{summary} → {out_path.name}")
        self._open_pdf(out_path)

    # ----- 파이프라인 -----

    def _prepare(self, options: Options) -> tuple[Image.Image, Plan, list[str]]:
        """배경 처리 → 분할 계획. (처리된 이미지, 계획, 상태줄 메모)를 돌려준다."""
        assert self.image is not None
        image = self.image
        notes: list[str] = []

        if self.bg_on.get() and self.bg_color is not None:
            if is_white(self.bg_color):
                notes.append(f"배경 {to_hex(self.bg_color)}은 이미 흰색")
            else:
                mode_label = self.bg_mode.get()
                image = apply_background(image, self.bg_color, BG_MODES[mode_label])
                notes.append(f"배경 {to_hex(self.bg_color)} {mode_label}")

        p = plan(image, options)
        if len(p.slices) > MAX_PAGES:
            raise UserError(f"페이지가 너무 많습니다 ({len(p.slices)}페이지, 최대 {MAX_PAGES}페이지).")
        if options.smart_split and len(p.slices) > 1:
            notes.append(f"빈 줄 컷 {smart_cut_count(image, p)}/{len(p.slices) - 1}")
        return image, p, notes

    # ----- 내부 도우미 -----

    def _read_options(self) -> Options | None:
        raw = self.margin.get().strip()
        try:
            value = int(raw)
        except ValueError:
            value = -1
        if not MARGIN_MIN <= value <= MARGIN_MAX:
            messagebox.showerror(
                APP_TITLE, f"여백은 {MARGIN_MIN}~{MARGIN_MAX} 사이의 정수여야 합니다."
            )
            return None
        return Options(
            keep_actual_size=self.keep_actual.get(),
            margin_mm=float(value),
            smart_split=self.smart_split.get(),
        )

    def _sync_bg_widgets(self) -> None:
        state = "readonly" if self.bg_on.get() else "disabled"
        self.bg_mode_box.config(state=state)
        self.bg_button.config(state="normal" if self.bg_on.get() else "disabled")

    def _show_bg_color(self) -> None:
        if self.bg_color is None:
            self.bg_button.config(text="감지 실패", bg="SystemButtonFace", fg="black")
            return
        r, g, b = self.bg_color
        luma = 0.299 * r + 0.587 * g + 0.114 * b
        self.bg_button.config(
            text=to_hex(self.bg_color),
            bg=to_hex(self.bg_color),
            fg="black" if luma > 128 else "white",
        )

    def _set_busy(self, busy: bool) -> None:
        self.make_button.config(state="disabled" if busy else "normal")
        self.config(cursor="watch" if busy else "")
        # 성공 시에는 호출자가 이 뒤에 결과 문구를 덮어쓴다. 오류 시 "처리 중…"이 남지 않게 비운다.
        self.status.config(text="처리 중…" if busy else "")
        self.update_idletasks()

    def _open_pdf(self, out_path: Path) -> None:
        try:
            os.startfile(out_path)  # type: ignore[attr-defined]  # Windows 전용
        except OSError:
            messagebox.showinfo(APP_TITLE, f"PDF를 저장했습니다.\n{out_path}")


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
