import hashlib
import importlib.util
import io
from pathlib import Path

import pytest


@pytest.mark.parametrize("mode", ["short", "truncated", "over", "corrupt"])
def test_bounded_chunk_download(tmp_path, mode):
    path = (
        Path(__file__).resolve().parents[3] / "scripts/environment/fetch_fixed_debs.py"
    )
    spec = importlib.util.spec_from_file_location("rebuild_fetch_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = bytes(range(256)) * 32
    served = payload
    if mode == "truncated":
        served = payload[:-1]
    elif mode == "over":
        served = payload + b"x"
    elif mode == "corrupt":
        served = b"x" * len(payload)

    class Response(io.BytesIO):
        def read(self, size=-1):
            return super().read(min(size, 37))

    class Opener:
        calls = 0

        def open(self, uri, timeout):
            self.calls += 1
            return Response(served)

    opener = Opener()
    item = {
        "uri": "https://example.invalid/pkg",
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    output = tmp_path / "pkg.deb"
    if mode == "short":
        module.download_with_opener(item, output, opener)
        assert output.read_bytes() == payload
    else:
        with pytest.raises(
            ValueError, match="package_size_or_sha256_mismatch:received="
        ):
            module.download_with_opener(item, output, opener)
        assert not output.exists()
    assert opener.calls == 1
