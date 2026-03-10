import subprocess
import sys

from fastcs_bacnet import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "fastcs_bacnet", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
