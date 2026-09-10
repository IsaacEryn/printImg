"""Windows 프린터로 페이지 이미지를 바로 보낸다. pywin32는 실제 인쇄 함수 안에서만 import한다."""

from __future__ import annotations

from PIL import Image

Box = tuple[int, int, int, int]


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


def list_printers() -> tuple[list[str], str | None]:
    """(설치된 프린터 이름 목록, 기본 프린터 이름 또는 None)."""
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


def print_pages(pages: list[Image.Image], printer_name: str, job_name: str) -> None:
    """페이지 이미지들을 한 인쇄 작업으로 보낸다. 실패하면 예외를 그대로 올린다."""
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

        dc.StartDoc(job_name)
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
