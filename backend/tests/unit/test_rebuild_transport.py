"""Qualify the actual Windows binary transport and its legacy refusal."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows transport qualification")
@pytest.mark.parametrize(
    "legacy", [False, True], ids=["ps7-bytes-and-bounds", "ps5-refusal"]
)
def test_windows_binary_transport(tmp_path, legacy):
    executable = shutil.which("powershell" if legacy else "pwsh")
    if executable is None:
        pytest.skip("required PowerShell runtime unavailable")
    repo = Path(__file__).resolve().parents[3]
    command = [
        executable,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(repo / "scripts/environment/Test-RebuildTransport.ps1"),
        "-FixtureDir",
        str(tmp_path / "transport"),
        "-Python",
        sys.executable,
    ]
    if legacy:
        command.append("-LegacyRefusal")
    result = subprocess.run(command, capture_output=True, timeout=120, check=False)
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    marker = "LEGACY_BINARY_STDIN_REFUSED" if legacy else "STDIN_PRIMITIVE_RESULT=OK"
    assert result.returncode == 0 and marker in output, output[-4000:]
