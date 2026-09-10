"""PrintImg: 이미지를 A4 다중 페이지 PDF로 만드는 Tkinter 앱."""

from __future__ import annotations

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# `python src/main.py`로 실행해도 옆 모듈을 찾도록 한다. PyInstaller는 spec의 pathex로 처리.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, UnidentifiedImageError  # noqa: E402

from image_loader import SUPPORTED_EXTENSIONS, load_image  # noqa: E402
from paginate import Options, plan  # noqa: E402
from pdf_writer import write  # noqa: E402

APP_TITLE = "PrintImg"
MARGIN_MIN = 0
MARGIN_MAX = 30
MARGIN_DEFAULT = 10


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.resizable(False, False)
        self.image_path: Path | None = None
        self.keep_actual = tk.BooleanVar(value=False)
        self.margin = tk.StringVar(value=str(MARGIN_DEFAULT))
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.grid()

        ttk.Button(frame, text="이미지 선택…", command=self.choose_file).grid(
            row=0, column=0, sticky="w"
        )
        self.file_label = ttk.Label(frame, text="선택된 파일 없음", width=48)
        self.file_label.grid(row=0, column=1, padx=(8, 0), sticky="w")

        ttk.Checkbutton(frame, text="원본 크기 유지", variable=self.keep_actual).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )

        ttk.Label(frame, text="여백 (mm)").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Spinbox(
            frame, from_=MARGIN_MIN, to=MARGIN_MAX, textvariable=self.margin, width=5
        ).grid(row=2, column=1, sticky="w", pady=(8, 0))

        self.make_button = ttk.Button(
            frame, text="PDF 만들기", command=self.make_pdf, state="disabled"
        )
        self.make_button.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(16, 0))

        self.status = ttk.Label(frame, text="")
        self.status.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))

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
            with Image.open(path) as im:
                width, height = im.size
        except Image.DecompressionBombError:
            messagebox.showerror(APP_TITLE, "이미지가 너무 큽니다.")
            return
        except (UnidentifiedImageError, OSError):
            messagebox.showerror(APP_TITLE, f"이미지를 열 수 없습니다.\n{Path(path).name}")
            return

        self.image_path = Path(path)
        self.file_label.config(text=f"{self.image_path.name} · {width} × {height}")
        self.make_button.config(state="normal")
        self.status.config(text="")

    def make_pdf(self) -> None:
        if self.image_path is None:
            return
        margin_mm = self._read_margin()
        if margin_mm is None:
            return

        out_path = self.image_path.with_suffix(".pdf")
        if out_path.exists() and not messagebox.askyesno(
            APP_TITLE, f"{out_path.name} 파일이 이미 있습니다. 덮어쓸까요?"
        ):
            return

        self._set_busy(True)
        try:
            try:
                image = load_image(self.image_path)
            except Image.DecompressionBombError:
                messagebox.showerror(APP_TITLE, "이미지가 너무 큽니다.")
                return
            except (UnidentifiedImageError, OSError):
                messagebox.showerror(
                    APP_TITLE, f"이미지를 열 수 없습니다.\n{self.image_path.name}"
                )
                return

            options = Options(keep_actual_size=self.keep_actual.get(), margin_mm=margin_mm)
            try:
                page_count = write(image, plan(image, options), out_path)
            except PermissionError:
                messagebox.showerror(
                    APP_TITLE, f"{out_path.name} 파일이 열려 있습니다. 닫고 다시 시도하세요."
                )
                return
            except OSError as e:
                messagebox.showerror(
                    APP_TITLE, f"PDF를 저장할 수 없습니다.\n{out_path.name}\n{e}"
                )
                return
        finally:
            self._set_busy(False)

        self.status.config(text=f"{page_count}페이지 생성 → {out_path.name}")
        self._open_pdf(out_path)

    # ----- 내부 도우미 -----

    def _read_margin(self) -> float | None:
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
        return float(value)

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
