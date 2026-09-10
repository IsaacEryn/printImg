"""운영체제 기본 앱으로 파일 열기. Windows는 os.startfile, 맥은 open, 리눅스는 xdg-open."""

from __future__ import annotations

import os
import subprocess
import sys


def open_command(path: str | os.PathLike, platform: str = sys.platform) -> list[str] | None:
    """플랫폼별 열기 명령. Windows는 명령 대신 os.startfile을 써야 하므로 None."""
    if platform.startswith("win"):
        return None
    if platform == "darwin":
        return ["open", str(path)]
    return ["xdg-open", str(path)]


def open_file(path: str | os.PathLike) -> None:
    """실패하면 OSError를 올린다."""
    cmd = open_command(path)
    if cmd is None:
        os.startfile(path)  # type: ignore[attr-defined]
        return
    try:
        subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise OSError(str(e)) from e
