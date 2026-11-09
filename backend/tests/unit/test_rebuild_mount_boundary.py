"""Exercise the production mount check against observed WSL and unsafe mounts."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
BASH = shutil.which("bash")
if Path("D:/Git/Git/bin/bash.exe").is_file():
    BASH = "D:/Git/Git/bin/bash.exe"


@pytest.mark.skipif(BASH is None, reason="bash unavailable")
@pytest.mark.parametrize(
    ("mount", "allowed"),
    [
        (
            "drivers /usr/lib/wsl/drivers 9p ro,nosuid,nodev,aname=drivers;fmask=222;dmask=222 0 0",
            True,
        ),
        (
            "drivers /usr/lib/wsl/drivers 9p rw,nosuid,nodev,aname=drivers;fmask=222;dmask=222 0 0",
            False,
        ),
        (
            "drivers /usr/lib/wsl/drivers 9p ro,nodev,aname=drivers;fmask=222;dmask=222 0 0",
            False,
        ),
        (
            "drivers /usr/lib/wsl/drivers 9p ro,nosuid,nodev,aname=drivers;fmask=000;dmask=222 0 0",
            False,
        ),
        ("C: /mnt/c 9p ro,nosuid,nodev,aname=drvfs 0 0", False),
        ("C: /mnt/c drvfs ro,nosuid,nodev 0 0", False),
        (
            "drivers /mnt/user 9p ro,nosuid,nodev,aname=drivers;fmask=222;dmask=222 0 0",
            False,
        ),
    ],
)
def test_mount_boundary(tmp_path, mount, allowed):
    source = (REPO / "scripts/environment/rebuild/bootstrap.sh").read_text()
    match = re.search(r"^awk '([^']+)' /proc/mounts$", source, re.MULTILINE)
    assert match is not None
    fixture = tmp_path / "mounts"
    fixture.write_text(mount + "\n")
    result = subprocess.run(
        [BASH, "-c", 'exec awk "$1" "$2"', "fixture", match[1], fixture.as_posix()],
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == (0 if allowed else 1), result.stderr
