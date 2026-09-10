from desktop import open_command
from preview import wheel_steps
from printer import parse_lpstat_default, parse_lpstat_printers

LPSTAT_P = """printer HP_LaserJet_Pro is idle.  enabled since Mon 01 Jan 2024 10:00:00 AM KST
printer Brother_MFC_L2750DW disabled since Tue 02 Jan 2024 09:00:00 AM KST
\tReason: Paused
printer Canon_iR_ADV is idle.  enabled since Wed 03 Jan 2024 08:00:00 AM KST
"""


def test_parse_lpstat_printers_returns_names_in_order():
    assert parse_lpstat_printers(LPSTAT_P) == [
        "HP_LaserJet_Pro",
        "Brother_MFC_L2750DW",
        "Canon_iR_ADV",
    ]


def test_parse_lpstat_printers_handles_no_printers():
    assert parse_lpstat_printers("lpstat: No destinations added.\n") == []


def test_parse_lpstat_default_reads_system_default():
    assert parse_lpstat_default("system default destination: Canon_iR_ADV\n") == "Canon_iR_ADV"


def test_parse_lpstat_default_is_none_when_unset():
    assert parse_lpstat_default("no system default destination\n") is None


def test_open_command_per_platform():
    assert open_command("/tmp/a.pdf", "darwin") == ["open", "/tmp/a.pdf"]
    assert open_command("/tmp/a.pdf", "linux") == ["xdg-open", "/tmp/a.pdf"]
    assert open_command("C:\\a.pdf", "win32") is None  # os.startfile 사용


def test_wheel_steps_per_platform():
    # Windows: 한 칸 = 120. 맥: 한 칸 = 1 (가속되면 더 큼). 위로 굴리면(양수) 위로 스크롤(음수).
    assert wheel_steps(120, "win32") == -1
    assert wheel_steps(-240, "win32") == 2
    assert wheel_steps(1, "darwin") == -1
    assert wheel_steps(-3, "darwin") == 3
    assert wheel_steps(0, "darwin") == 0
