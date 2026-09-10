from desktop import open_command
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
