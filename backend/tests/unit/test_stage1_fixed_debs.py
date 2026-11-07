"""Fixed-snapshot transport regressions; no WSL or external requests."""

import hashlib
import io
import json
import multiprocessing
import time
from pathlib import Path

import pytest

from scripts.environment import fetch_fixed_debs as subject


def blocked_worker_fixture():
    time.sleep(30)


def failed_worker_fixture():
    raise SystemExit(7)


def successful_worker_fixture(path):
    Path(path).write_bytes(b"verified local worker")


def maximum_package_worker_fixture(item, destination):
    with Path(destination).open("xb") as stream:
        stream.writelines(b"x" * 65536 for _ in range(item["size"] // 65536))


def package(data=b"verified deb"):
    return {
        "package": "fixture",
        "version": "1",
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def uri_line(filename="pool/main/f/fixture/fixture_1_amd64.deb"):
    return f"'{subject.PREFIX}{filename}' fixture_1_amd64.deb 12 MD5Sum:unused\n"


@pytest.mark.parametrize(
    "text", ["", "Inst fixture (1 Ubuntu)\n", "simulation succeeded\n"]
)
def test_simulation_without_uris_is_not_a_completed_download(text):
    with pytest.raises(ValueError, match="uri_count_out_of_bounds"):
        subject.plan_downloads(text, {})


@pytest.mark.parametrize(
    "text",
    [
        "'https://example.com/pool/fixture.deb' x 12 MD5Sum:x\n",
        uri_line("pool/../private.deb"),
        uri_line("pool/%2e%2e/private.deb"),
        uri_line("pool/main/f.deb?query=secret"),
        "'http://example.com/x' x 12 MD5Sum:x\n",
    ],
)
def test_untrusted_uri_list_cannot_escape_snapshot_pool(text):
    with pytest.raises(ValueError):
        subject.plan_downloads(text, {})


def test_whole_plan_validated_before_any_get(tmp_path, monkeypatch):
    filename = "pool/main/f/fixture/fixture_1_amd64.deb"
    monkeypatch.setattr(subject, "package_index", lambda: {filename: package()})
    (tmp_path / "apt-solve-output.txt").write_text(
        uri_line() + uri_line("pool/missing.deb"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="not_in_verified_packages"):
        subject.fetch(tmp_path, opener=object())
    assert not (tmp_path / "debs").exists()


def test_corrupt_body_stops_before_next_get_and_keeps_failure_receipt(
    tmp_path, monkeypatch
):
    first = "pool/main/f/fixture/fixture_1_amd64.deb"
    second = "pool/main/f/fixture/fixture2_1_amd64.deb"
    monkeypatch.setattr(
        subject, "package_index", lambda: {first: package(), second: package()}
    )
    (tmp_path / "apt-solve-output.txt").write_text(
        uri_line(first) + uri_line(second), encoding="utf-8"
    )

    class Opener:
        def __init__(self):
            self.calls = []

        def open(self, uri, timeout):
            self.calls.append(uri)
            return io.BytesIO(b"corrupt")

    opener = Opener()
    with pytest.raises(ValueError, match="size_or_sha256"):
        subject.fetch(tmp_path, opener)
    assert len(opener.calls) == 1
    summary = json.loads((tmp_path / "debs/fetch-summary.json").read_text())
    assert summary["complete"] is False
    assert summary["results"][0]["state"] == "failed_keep_partial"
    assert not (tmp_path / "debs/fixture_1_amd64.deb").exists()


def test_verified_body_is_exclusive_and_existing_downloads_are_preserved(
    tmp_path, monkeypatch
):
    filename = "pool/main/f/fixture/fixture_1_amd64.deb"
    data = b"verified deb"
    monkeypatch.setattr(subject, "package_index", lambda: {filename: package(data)})
    (tmp_path / "apt-solve-output.txt").write_text(uri_line(), encoding="utf-8")

    class Opener:
        def open(self, uri, timeout):
            return io.BytesIO(data)

    subject.fetch(tmp_path, Opener())
    assert (tmp_path / "debs/fixture_1_amd64.deb").read_bytes() == data
    with pytest.raises(FileExistsError):
        subject.fetch(tmp_path, Opener())
    assert (
        json.loads((tmp_path / "debs/fetch-summary.json").read_text())["complete"]
        is True
    )


@pytest.mark.parametrize(
    "field,value", [("size", subject.PER_ITEM_CAP + 1), ("size", 0), ("sha256", "bad")]
)
def test_authenticated_package_still_has_bounded_transport(field, value):
    meta = package()
    meta[field] = value
    with pytest.raises(ValueError, match="invalid_package_bounds"):
        subject.plan_downloads(
            uri_line(), {"pool/main/f/fixture/fixture_1_amd64.deb": meta}
        )


def test_duplicate_name_total_and_count_caps_are_hard_failures(monkeypatch):
    filename = "pool/main/f/fixture/fixture_1_amd64.deb"
    index = {filename: package()}
    with pytest.raises(ValueError, match="duplicate_output_name"):
        subject.plan_downloads(uri_line() * 2, index)
    monkeypatch.setattr(subject, "TOTAL_CAP", 1)
    with pytest.raises(ValueError, match="total_over_cap"):
        subject.plan_downloads(uri_line(), index)
    with pytest.raises(ValueError, match="uri_count_out_of_bounds"):
        subject.plan_downloads(uri_line() * (subject.MAX_ITEMS + 1), index)


def test_redirects_never_expand_disclosure():
    with pytest.raises(ValueError, match="redirect_not_authorized"):
        subject.NoRedirect().redirect_request(
            None, None, 302, "Found", {}, "https://other.test/"
        )


def test_wall_clock_deadline_terminates_a_real_blocked_worker():
    before = {child.pid for child in multiprocessing.active_children()}
    start = time.monotonic()
    with pytest.raises(TimeoutError, match="wall_clock_deadline"):
        subject.run_worker(blocked_worker_fixture, (), deadline=0.2)
    assert time.monotonic() - start < 8
    assert {child.pid for child in multiprocessing.active_children()} <= before


def test_failed_real_worker_cannot_be_reported_as_a_completed_download():
    with pytest.raises(RuntimeError, match="download_worker_failed:7"):
        subject.run_worker(failed_worker_fixture, (), deadline=5)


def test_successful_real_worker_is_joined_and_its_output_is_available(tmp_path):
    destination = tmp_path / "local-worker.txt"
    subject.run_worker(successful_worker_fixture, (str(destination),), deadline=5)
    assert destination.read_bytes() == b"verified local worker"


def test_maximum_legal_package_crosses_real_worker_file_and_parent_consumer(
    tmp_path, monkeypatch
):
    filename = "pool/main/f/fixture/fixture_1_amd64.deb"
    digest = hashlib.sha256()
    for _ in range(subject.PER_ITEM_CAP // 65536):
        digest.update(b"x" * 65536)
    meta = {**package(), "size": subject.PER_ITEM_CAP, "sha256": digest.hexdigest()}
    monkeypatch.setattr(subject, "package_index", lambda: {filename: meta})
    (tmp_path / "apt-solve-output.txt").write_text(uri_line(), encoding="utf-8")
    real_run_worker = subject.run_worker

    def local_producer_only(target, args):
        assert target is subject.download_worker
        real_run_worker(maximum_package_worker_fixture, args, deadline=10)

    monkeypatch.setattr(subject, "run_worker", local_producer_only)
    subject.fetch(tmp_path)
    summary = json.loads((tmp_path / "debs/fetch-summary.json").read_text())
    assert summary["complete"] is True
    assert summary["results"][0]["bytes"] == subject.PER_ITEM_CAP
