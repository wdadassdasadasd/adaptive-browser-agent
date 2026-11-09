"""Fetch only the approved rebuilt instance's signed dependency closure; never install."""

import hashlib
import json
import shutil
import subprocess
import winreg
from pathlib import Path

import fetch_fixed_debs as fixed
from fetch_fixed_debs import ROOT as LEGACY_ROOT
from fetch_fixed_debs import bounded_read, fetch

_ORIGINAL_DOWNLOAD_WORKER = fixed.download_worker


def resume_download_worker(item, destination):
    if item["filename"] == "pool/main/p/perl/perl-base_5.38.2-3.2ubuntu0.6_amd64.deb":
        source = (
            LEGACY_ROOT.parent / "stage1-rebuild-20261108/first-package-diagnostic.deb"
        )
        data = bounded_read(source, item["size"])
        if (
            len(data) != item["size"]
            or hashlib.sha256(data).hexdigest() != item["sha256"]
        ):
            raise ValueError("diagnostic_package_drift")
        with Path(destination).open("xb") as stream:
            stream.write(data)
        return
    _ORIGINAL_DOWNLOAD_WORKER(item, destination)


def main():
    root = LEGACY_ROOT.parent / "stage1-rebuild-20261108"
    phase = root / "bootstrap-03"
    receipt = json.loads(bounded_read(phase / "receipt.json", 65536))
    if receipt.get("phase") != "Bootstrap" or receipt.get("success") is not True:
        raise ValueError("bootstrap_not_verified_and_closed")

    candidate_path = root / "candidate.json"
    candidate_bytes = bounded_read(candidate_path, 65536)
    if (
        hashlib.sha256(bounded_read(phase / "receipt.json", 65536)).hexdigest()
        != "664f8f2e174d148044ae975cfcab8c351f49beada1235f65b0105875bf4fb206"
    ):
        raise ValueError("bootstrap_receipt_drift")
    prior = bounded_read(root / "candidate-v12.json", 65536)
    if (
        hashlib.sha256(prior).hexdigest() != receipt["candidate_sha256"]
        or receipt["candidate_sha256"]
        != "fd277bbf3ae0523b9ecee50255c14dc347994be3319719c899d1b795ca4263a3"
    ):
        raise ValueError("bootstrap_candidate_drift")
    repo = Path(__file__).resolve().parents[2]
    for entry in json.loads(prior)["files"]:
        if (
            hashlib.sha256(
                (root / "candidate-originals-r12" / entry["path"]).read_bytes()
            ).hexdigest()
            != entry["sha256"]
        ):
            raise ValueError("bootstrap_original_drift")
    candidate = json.loads(candidate_bytes)
    repo = Path(__file__).resolve().parents[2]
    for entry in candidate["files"]:
        file = repo / entry["path"]
        if not file.resolve().is_relative_to(repo.resolve()):
            raise ValueError("candidate_path_escape")
        if hashlib.sha256(file.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("candidate_source_drift")
    for entry in receipt["files"]:
        name = entry["name"]
        if Path(name).name != name:
            raise ValueError("receipt_filename_escape")
        if hashlib.sha256((phase / name).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("bootstrap_evidence_drift")
    for service in ("WslService", "vmcompute"):
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, rf"SYSTEM\CurrentControlSet\Services\{service}"
        ) as key:
            if winreg.QueryValueEx(key, "Start")[0] != 4:
                raise ValueError("wsl_service_not_disabled")
        result = subprocess.run(
            [r"C:\Windows\System32\sc.exe", "query", service],
            capture_output=True,
            timeout=10,
            check=True,
        )
        if b"STOPPED" not in result.stdout:
            raise ValueError("wsl_service_not_stopped")
    output = root / "fetch-02"
    output.mkdir(exist_ok=False)
    shutil.copyfile(phase / "apt-solve-output.txt", output / "apt-solve-output.txt")
    fixed.download_worker = resume_download_worker
    fetch(output)


if __name__ == "__main__":
    main()
