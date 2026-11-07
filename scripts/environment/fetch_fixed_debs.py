"""Fetch the reviewed fixed-snapshot closure, only after the VM is stopped.

Usage: python scripts/environment/fetch_fixed_debs.py <window-dir>
The evidence root is fixed. Existing evidence and downloads are never replaced.
"""

import gzip
import hashlib
import io
import json
import multiprocessing
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PREFIX = "https://snapshot.ubuntu.com/ubuntu/20261021T000000Z/"
PER_ITEM_CAP = 64 * 1024 * 1024
MAX_ITEMS = 400
TOTAL_CAP = 1_500_000_000
SOLVE_CAP = 4 * 1024 * 1024
ROOT = Path(__file__).resolve().parents[2] / ".tmp/stage-1-1-resume-20261107"
# These exact InRelease bytes passed gpgv 2.5.24 in verify-01 on 2026-11-07.
# Pinning them reuses that verification; an unsigned receipt cannot replace them.
RELEASE_HASHES = {
    "noble": "cdb2f31d809f589719a53c6ad15f255b27569c4059542ada282aaa21b8e164b0",
    "noble-updates": "b88eac44c07e3606175cbca290f26508b7c5aa84aa8fecb4098f59a34c2ceab9",
    "noble-security": "13f077ea5f78804f0dfc864c880704d70e46f6cf7cad6b8f88964cb4ae2a0e7d",
}


def bounded_read(path, limit):
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("input_over_cap")
    return data


def package_index(root=ROOT):
    """Read only Packages payloads bound to the already verified signed releases."""
    index = {}
    for pocket, digest in RELEASE_HASHES.items():
        release = bounded_read(
            root / "snapshot-01" / f"dists_{pocket}_InRelease.part", 512 * 1024
        )
        if hashlib.sha256(release).hexdigest() != digest:
            raise ValueError(f"signed_release_drift:{pocket}")
        section = (
            release.decode("utf-8").split("\nSHA256:\n", 1)[1].split("\nSHA512:", 1)[0]
        )
        matches = re.findall(
            r"^ ([0-9a-f]{64})\s+(\d+) main/binary-amd64/Packages.gz$",
            section,
            re.MULTILINE,
        )
        if len(matches) != 1:
            raise ValueError(f"packages_binding_ambiguous:{pocket}")
        expected_hash, size = matches[0]
        compressed = bounded_read(
            root / "snapshot-01/packages" / f"{pocket}__Packages.gz", 8 * 1024 * 1024
        )
        if (
            len(compressed) != int(size)
            or hashlib.sha256(compressed).hexdigest() != expected_hash
        ):
            raise ValueError(f"packages_drift:{pocket}")
        # Bound decompression independently of the compressed-byte limit.
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
            payload = stream.read(64 * 1024 * 1024 + 1)
        if len(payload) > 64 * 1024 * 1024:
            raise ValueError("packages_expansion_over_cap")
        for paragraph in payload.decode("utf-8", errors="strict").split("\n\n"):
            fields = {}
            for line in paragraph.splitlines():
                if line and not line[0].isspace() and ": " in line:
                    key, value = line.split(": ", 1)
                    fields[key] = value
            if "Filename" not in fields:
                continue
            filename = fields["Filename"]
            entry = {
                "package": fields["Package"],
                "version": fields["Version"],
                "size": int(fields["Size"]),
                "sha256": fields["SHA256"],
            }
            if filename in index and index[filename] != entry:
                raise ValueError("ambiguous_filename")
            index[filename] = entry
    return index


def plan_downloads(text, index):
    """Validate the WHOLE list before any GET; zero URIs is never success."""
    uris = []
    for line in text.splitlines():
        if "://" not in line and not line.startswith("'"):
            continue
        match = re.fullmatch(r"'(https://[^']+)'\s+\S+\s+\d+\s+\S+\s*", line)
        if not match:
            raise ValueError("unparsed_uri_line")
        uris.append(match[1])
    if not 1 <= len(uris) <= MAX_ITEMS:
        raise ValueError("uri_count_out_of_bounds")
    result = []
    seen = set()
    total = 0
    for uri in uris:
        if not uri.startswith(PREFIX):
            raise ValueError("uri_out_of_scope")
        filename = urllib.parse.unquote(uri[len(PREFIX) :], errors="strict")
        if (
            not filename.startswith("pool/")
            or any(p in ("", ".", "..") for p in filename.split("/"))
            or re.search(r"[^A-Za-z0-9_./+~:\-]", filename)
        ):
            raise ValueError("unsafe_filename")
        meta = index.get(filename)
        if meta is None:
            raise ValueError("not_in_verified_packages")
        if not 0 < meta["size"] <= PER_ITEM_CAP or not re.fullmatch(
            r"[0-9a-f]{64}", meta["sha256"]
        ):
            raise ValueError("invalid_package_bounds")
        leaf = filename.rsplit("/", 1)[1]
        if leaf in seen:
            raise ValueError("duplicate_output_name")
        seen.add(leaf)
        total += meta["size"]
        if total > TOTAL_CAP:
            raise ValueError("total_over_cap")
        result.append({"uri": uri, "filename": filename, **meta})
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect_not_authorized")


def download_worker(item, destination):
    """One physical request, never retry; parent owns the wall-clock deadline."""
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
    )
    result = {"state": "failed_keep_partial", "error": None}
    try:
        download_with_opener(item, Path(destination), opener)
        result["state"] = "fetched_verified"
    except Exception as error:
        result["error"] = str(error)[:2048]
        raise
    finally:
        with Path(str(destination) + ".worker.json").open(
            "x", encoding="utf-8"
        ) as stream:
            json.dump(result, stream, indent=2)


def run_worker(target, args, deadline=120):
    worker = multiprocessing.get_context("spawn").Process(target=target, args=args)
    worker.start()
    try:
        worker.join(deadline)
        if worker.is_alive():
            raise TimeoutError("download_wall_clock_deadline")
        if worker.exitcode != 0:
            raise RuntimeError(f"download_worker_failed:{worker.exitcode}")
    finally:
        # Also fence interruption/cancellation, not only the ordinary deadline path.
        if worker.is_alive():
            worker.terminate()
            worker.join(5)
            if worker.is_alive():
                worker.kill()
                worker.join(5)
            if worker.is_alive():
                raise RuntimeError("download_worker_cleanup_unconfirmed")
        if not worker.is_alive():
            worker.close()


def download_with_opener(item, destination, opener):
    with opener.open(item["uri"], timeout=120) as response:
        data = response.read(item["size"] + 1)
    if len(data) != item["size"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise ValueError("package_size_or_sha256_mismatch")
    with destination.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def fetch(window, opener=None):
    text = bounded_read(window / "apt-solve-output.txt", SOLVE_CAP).decode(
        "utf-8", errors="strict"
    )
    plan = plan_downloads(text, package_index())
    out = window / "debs"
    out.mkdir(exist_ok=False)
    results = []
    try:
        for item in plan:
            receipt = {
                **item,
                "state": "failed_keep_partial",
                "bytes": 0,
                "error": None,
            }
            leaf = item["filename"].rsplit("/", 1)[1]
            try:
                destination = out / leaf
                if opener is None:
                    run_worker(download_worker, (item, str(destination)))
                else:
                    # In-memory fixtures only; the CLI never supplies an opener.
                    download_with_opener(item, destination, opener)
                data = bounded_read(destination, item["size"])
                receipt["bytes"] = len(data)
                if (
                    len(data) != item["size"]
                    or hashlib.sha256(data).hexdigest() != item["sha256"]
                ):
                    raise ValueError("persisted_package_mismatch")
                receipt["state"] = "fetched_verified"
            except Exception as error:
                receipt["error"] = str(error)
                raise
            finally:
                with (out / (leaf + ".receipt.json")).open(
                    "x", encoding="utf-8"
                ) as stream:
                    json.dump(receipt, stream, indent=2)
                results.append(receipt)
    finally:
        with (out / "fetch-summary.json").open("x", encoding="utf-8") as stream:
            json.dump(
                {
                    "planned": len(plan),
                    "results": results,
                    "complete": len(results) == len(plan)
                    and all(r["state"] == "fetched_verified" for r in results),
                },
                stream,
                indent=2,
            )
    print(f"FETCH_DONE verified={len(results)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    window = Path(sys.argv[1]).resolve(strict=True)
    if window != ROOT / "bootstrap/window-01":
        raise SystemExit("window_not_the_reviewed_one")
    fetch(window)
