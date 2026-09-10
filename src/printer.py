"""페이지 이미지를 프린터로 바로 보낸다.

Windows는 pywin32(GDI), 맥·리눅스는 CUPS(lpstat/lpr)를 쓴다. 플랫폼 전용 모듈은 함수 안에서 import한다.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

from PIL import Image

Box = tuple[int, int, int, int]


# ----- 공통 순수 함수 -----


def page_box(phys_w: int, phys_h: int, off_x: int, off_y: int, page_w: int, page_h: int) -> Box:
    """페이지 이미지를 물리 용지에 비율 유지로 꽉 채워 가운데 놓았을 때의 상자.

    좌표는 GDI 원점(인쇄 가능 영역의 왼쪽 위) 기준이므로 물리 용지 왼쪽 위는 (−off_x, −off_y).
    우리 페이지에는 여백이 이미 들어 있어 인쇄 불가 영역을 무시하고 용지 전체에 맞춘다.
    """
    scale = min(phys_w / page_w, phys_h / page_h)
    w = round(page_w * scale)
    h = round(page_h * scale)
    x0 = round((phys_w - w) / 2) - off_x
    y0 = round((phys_h - h) / 2) - off_y
    return (x0, y0, x0 + w, y0 + h)


def parse_lpstat_printers(text: str) -> list[str]:
    """`lpstat -p` 출력에서 프린터 이름을 순서대로 뽑는다."""
    names = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "printer":
            names.append(parts[1])
    return names


def parse_lpstat_default(text: str) -> str | None:
    """`lpstat -d` 출력에서 기본 프린터 이름. 없으면 None."""
    prefix = "system default destination:"
    for line in text.splitlines():
        if line.startswith(prefix):
            name = line[len(prefix):].strip()
            return name or None
    return None


# ----- 플랫폼 진입점 -----


def list_printers() -> tuple[list[str], str | None]:
    """(설치된 프린터 이름 목록, 기본 프린터 이름 또는 None)."""
    if sys.platform.startswith("win"):
        return _win32_list_printers()
    return _cups_list_printers()


def print_pages(
    pages: list[Image.Image], printer_name: str, job_name: str, output_file: str | None = None
) -> None:
    """페이지 이미지들을 한 인쇄 작업으로 보낸다. 실패하면 예외를 그대로 올린다.

    output_file은 Windows 전용: 파일 출력 드라이버(예: Microsoft Print to PDF)가
    대화상자 없이 그 경로에 쓴다(검증용).
    """
    if sys.platform.startswith("win"):
        _win32_print_pages(pages, printer_name, job_name, output_file)
    else:
        _cups_print_pages(pages, printer_name, job_name)


# ----- Windows (pywin32) -----


def _win32_list_printers() -> tuple[list[str], str | None]:
    import win32print

    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    names = [p[2] for p in win32print.EnumPrinters(flags)]
    try:
        default = win32print.GetDefaultPrinter()
    except Exception:
        default = None
    if default and default not in names:
        names.insert(0, default)
    return names, default


def _win32_print_pages(
    pages: list[Image.Image], printer_name: str, job_name: str, output_file: str | None
) -> None:
    import win32con
    import win32ui
    from PIL import ImageWin

    dc = win32ui.CreateDC()
    dc.CreatePrinterDC(printer_name)
    try:
        phys_w = dc.GetDeviceCaps(win32con.PHYSICALWIDTH)
        phys_h = dc.GetDeviceCaps(win32con.PHYSICALHEIGHT)
        off_x = dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)
        off_y = dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)

        dc.StartDoc(job_name, output_file)
        try:
            for page in pages:
                dc.StartPage()
                box = page_box(phys_w, phys_h, off_x, off_y, page.width, page.height)
                ImageWin.Dib(page).draw(dc.GetHandleOutput(), box)
                dc.EndPage()
        finally:
            dc.EndDoc()
    finally:
        dc.DeleteDC()


# ----- macOS / Linux (CUPS) -----


def _run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout


def _cups_list_printers() -> tuple[list[str], str | None]:
    try:
        names = parse_lpstat_printers(_run(["lpstat", "-p"]))
        default = parse_lpstat_default(_run(["lpstat", "-d"]))
    except FileNotFoundError:
        return [], None
    if default and default not in names:
        names.insert(0, default)
    return names, default


def _cups_print_pages(pages: list[Image.Image], printer_name: str, job_name: str) -> None:
    """페이지를 임시 PDF로 저장해 lpr로 보낸다. PDF는 이미 A4라 용지만 A4로 지정한다."""
    from pdf_writer import save_pages

    fd, path = tempfile.mkstemp(prefix="printimg-", suffix=".pdf")
    os.close(fd)
    try:
        save_pages(pages, path)
        subprocess.run(
            ["lpr", "-P", printer_name, "-T", job_name, "-o", "media=A4", "-o", "fit-to-page", path],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
