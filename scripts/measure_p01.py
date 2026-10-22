"""Measure the explicit fake Worker through the local Windows launcher.

This writes a new evidence file and a disposable test database. It never creates
a database, installs dependencies, calls a provider, or stops PostgreSQL/WSL.
The database must already be reachable and empty; cold-start and database-outage
checks need separate evidence. With --manual-database-outage the operator stops
and restores PostgreSQL when prompted; the harness never controls that service.
Run with the repository Python environment.
"""

import argparse
import asyncio
import hashlib
import json
import math
import os
import platform
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import psutil
from sqlalchemy import inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from adaptive_research.infrastructure.config import Settings
from adaptive_research.infrastructure.pg_models import PgEvent
from adaptive_research.infrastructure.pg_store import (
    TERMINAL,
    FenceLost,
    PgStore,
)

OWNER = "p01-local-owner"
FAKE_MODULE = "tests.p01_fake_worker"


class MeasurementFailure(RuntimeError):
    """A fixed measurement precondition or assertion failed."""


def now() -> str:
    return datetime.now(UTC).isoformat()


def json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (Decimal, Path)):
        return str(value)
    raise TypeError(type(value).__name__)


def assert_port_available(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as exc:
            raise MeasurementFailure("API measurement port is unavailable") from exc


def source_hashes() -> dict[str, str]:
    files = [
        ROOT / "scripts" / "start-p01.ps1",
        ROOT / "scripts" / "measure_p01.py",
        ROOT / "backend" / "tests" / "p01_fake_worker.py",
        ROOT / "backend" / "uv.lock",
        *sorted((ROOT / "backend" / "src" / "adaptive_research").rglob("*.py")),
        *sorted((ROOT / "backend" / "migrations").rglob("*.py")),
    ]
    return {
        file.relative_to(ROOT).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in files
    }


class Measurement:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.output = Path(args.output).resolve()
        self.output.relative_to((ROOT / "data" / "p01").resolve())
        if (
            self.output.exists()
            or self.output.with_suffix(self.output.suffix + ".sha256").exists()
        ):
            raise MeasurementFailure("Evidence output already exists")
        self.control = self.output.parent / f"{self.output.stem}-control"
        if self.control.exists():
            raise MeasurementFailure("Control directory already exists")
        self.launcher: subprocess.Popen[str] | None = None
        self.reader: threading.Thread | None = None
        self.resource_task: asyncio.Task | None = None
        self.background_tasks: list[asyncio.Task] = []
        self.engine = None
        self.store: PgStore | None = None
        self.client: httpx.AsyncClient | None = None
        self.secrets: tuple[str, ...] = ()
        self.launch_count = 0
        self.clock_offset_seconds = 0.0
        self.clock_uncertainty_seconds = 0.0
        self.evidence: dict[str, Any] = {
            "schema_version": 2,
            "started_at": now(),
            "mode": "controlled_fake_worker_no_provider_or_browser",
            "database_name": args.database_name,
            "api_port": args.port,
            "checks": {},
            "failures": [],
            "requests": [],
            "process_events": [],
            "launcher_output": [],
            "resource_samples": [],
            "scope_limits": {
                "database_outage_manual_restore": "UNVERIFIED",
                "real_browser_recovery": "UNVERIFIED",
                "wsl_cold_start": "SEPARATE_EVIDENCE_REQUIRED",
                "research_quality": "UNVERIFIED",
            },
            "product_release": "No-Go",
            "phase_status": "P01_INCOMPLETE",
            "manual_database_outage_requested": args.manual_database_outage,
            "actual_external_provider_calls": 0,
            "actual_external_provider_cost_cny": "0",
            "cost_note": "Synthetic local waits only; unpriced application ledger entries stay null.",
            "source_sha256": source_hashes(),
            "duration_clock": {
                "name": "time.perf_counter",
                "implementation": time.get_clock_info("perf_counter").implementation,
                "resolution_seconds": time.get_clock_info("perf_counter").resolution,
                "monotonic": time.get_clock_info("perf_counter").monotonic,
            },
            "sse_latency_method": {
                "name": "same_client_request_start_to_receive_upper_bound",
                "reasoning": (
                    "The matching cancel_requested event must commit after the cancellation "
                    "POST starts. The same-client perf_counter interval from immediately "
                    "before that POST to receipt of its SSE event therefore bounds "
                    "commit-to-receive latency from above."
                ),
                "remote_wall_clock_used_for_acceptance": False,
            },
        }

    def check(self, name: str, passed: bool, **details: Any) -> None:
        self.evidence["checks"][name] = {"passed": passed, **details}
        if not passed:
            self.evidence["failures"].append({"check": name, **details})

    def redact(self, value: str) -> str:
        for secret in self.secrets:
            value = value.replace(secret, "[REDACTED]")
        return value

    async def prepare(self) -> str:
        if os.name != "nt":
            raise MeasurementFailure(
                "This harness requires Windows and the WSL launcher"
            )
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,62}", self.args.database_name):
            raise MeasurementFailure("Invalid disposable database name")
        if "p01" not in self.args.database_name:
            raise MeasurementFailure("Disposable database name must contain p01")
        await asyncio.to_thread(assert_port_available, self.args.port)
        settings = Settings()
        original = make_url(settings.require_postgres_url())
        if original.host not in {"127.0.0.1", "localhost", "::1"}:
            raise MeasurementFailure("Only a loopback PostgreSQL service is supported")
        if self.args.database_name == original.database:
            raise MeasurementFailure("Refusing the configured application database")
        url = original.set(database=self.args.database_name).render_as_string(
            hide_password=False
        )
        self.secrets = tuple(
            value
            for value in (
                url,
                original.password,
                *(
                    secret.get_secret_value()
                    for secret in (settings.deepseek_api_key, settings.github_token)
                    if secret
                ),
            )
            if value
        )
        self.engine = create_async_engine(url, pool_pre_ping=True)
        async with self.engine.connect() as connection:
            tables = set(
                await connection.run_sync(lambda sync: inspect(sync).get_table_names())
            )
            if tables - {"alembic_version"}:
                raise MeasurementFailure("Disposable database contains existing tables")
            if "alembic_version" in tables and await connection.scalar(
                text("SELECT count(*) FROM alembic_version")
            ):
                raise MeasurementFailure("Disposable database has an applied migration")
            version = await connection.scalar(text("SELECT version()"))
            before = datetime.now(UTC).timestamp()
            database_time = await connection.scalar(text("SELECT clock_timestamp()"))
            after = datetime.now(UTC).timestamp()
            self.clock_offset_seconds = database_time.timestamp() - (before + after) / 2
            self.clock_uncertainty_seconds = (after - before) / 2
            self.evidence["database_clock"] = {
                "sampled_at": now(),
                "database_minus_client_seconds": self.clock_offset_seconds,
                "uncertainty_seconds": self.clock_uncertainty_seconds,
                "used_for_latency_acceptance": False,
            }
        self.store = PgStore(async_sessionmaker(self.engine, expire_on_commit=False))
        self.evidence["environment"] = {
            "platform": platform.platform(),
            "python": sys.version,
            "logical_cpu_count": psutil.cpu_count(),
            "physical_cpu_count": psutil.cpu_count(logical=False),
            "physical_memory_bytes": psutil.virtual_memory().total,
            "postgresql": version,
            "psutil": psutil.__version__,
            "lease_seconds": 30,
            "heartbeat_seconds": 5,
        }
        git = await asyncio.to_thread(
            subprocess.run,
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.evidence["git_head"] = git.stdout.strip() if git.returncode == 0 else None
        dirty = await asyncio.to_thread(
            subprocess.run,
            ["git", "status", "--short", "--ignore-submodules=all"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.evidence["working_tree_status"] = dirty.stdout.splitlines()
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.control.mkdir()
        return url

    def start(self, database_url: str) -> None:
        environment = os.environ.copy()
        environment.update(
            {
                "P01_DATABASE_URL": database_url,
                "P01_MEASURE_DATABASE_NAME": self.args.database_name,
                "P01_FAKE_CONTROL_DIR": str(self.control),
                "DEEPSEEK_API_KEY": "offline-p01-fake",
                "GITHUB_TOKEN": "",
            }
        )
        self.launcher = subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ROOT / "scripts" / "start-p01.ps1"),
                "-ApiPort",
                str(self.args.port),
                "-WslDistribution",
                self.args.wsl_distribution,
                "-ControlledTestWorker",
            ],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW
            | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        self.launch_count += 1
        launched = self.launcher
        self.evidence["process_events"].append(
            {
                "at": now(),
                "event": "launcher_started",
                "pid": launched.pid,
                "generation": self.launch_count,
            }
        )

        def read_output() -> None:
            assert launched.stdout is not None
            for line in launched.stdout:
                safe = self.redact(line.rstrip())
                self.evidence["launcher_output"].append({"at": now(), "line": safe})
                match = re.search(r"startup_seconds=([0-9.]+)", safe)
                if match:
                    self.evidence["launcher_startup_seconds"] = float(match.group(1))

        self.reader = threading.Thread(target=read_output, daemon=True)
        self.reader.start()
        if self.resource_task is None or self.resource_task.done():
            self.resource_task = asyncio.create_task(self.sample_resources())

    async def sample_resources(self) -> None:
        psutil.cpu_percent(interval=None)
        while True:
            memory = psutil.virtual_memory()
            descendants = []
            if self.launcher is not None:
                try:
                    descendants = psutil.Process(self.launcher.pid).children(
                        recursive=True
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            rss = 0
            for process in descendants:
                try:
                    rss += process.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            self.evidence["resource_samples"].append(
                {
                    "at": now(),
                    "host_cpu_percent": psutil.cpu_percent(interval=None),
                    "host_memory_used_bytes": memory.used,
                    "host_memory_percent": memory.percent,
                    "launcher_descendant_rss_sum_bytes": rss,
                    "launcher_descendant_count": len(descendants),
                }
            )
            await asyncio.sleep(0.25)

    def worker(self, excluding: int | None = None) -> psutil.Process | None:
        if self.launcher is None:
            return None
        try:
            children = psutil.Process(self.launcher.pid).children()
        except psutil.NoSuchProcess:
            return None
        for process in children:
            try:
                arguments = process.cmdline()
                if (
                    process.pid != excluding
                    and FAKE_MODULE in arguments
                    and "-m" in arguments
                ):
                    return process
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def owns_api_listener(self) -> bool:
        if self.launcher is None:
            return False
        try:
            descendants = psutil.Process(self.launcher.pid).children(recursive=True)
        except psutil.NoSuchProcess:
            return False
        for process in descendants:
            try:
                arguments = process.cmdline()
                if (
                    "uvicorn" not in arguments
                    or "adaptive_research.api.pg_main:app" not in arguments
                ):
                    continue
                for connection in process.net_connections(kind="tcp"):
                    if (
                        connection.status == psutil.CONN_LISTEN
                        and connection.laddr.port == self.args.port
                    ):
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    async def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        assert self.client is not None
        began = time.perf_counter()
        at = now()
        response = await self.client.request(method, path, **kwargs)
        self.evidence["requests"].append(
            {
                "at": at,
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "latency_seconds": time.perf_counter() - began,
            }
        )
        return response

    async def wait_until(self, predicate, seconds: float, description: str):
        deadline = time.perf_counter() + seconds
        while time.perf_counter() < deadline:
            if self.launcher is not None and self.launcher.poll() is not None:
                raise MeasurementFailure("Launcher exited during measurement")
            value = await predicate()
            if value:
                return value
            await asyncio.sleep(0.2)
        raise MeasurementFailure(f"Deadline exceeded: {description}")

    async def task(self, task_id: str):
        assert self.store is not None
        return await self.store.get_task(OWNER, task_id)

    async def wait_status(self, task_id: str, statuses: set[str], seconds: float = 15):
        async def predicate():
            task = await self.task(task_id)
            return task if task is not None and task.status in statuses else None

        return await self.wait_until(predicate, seconds, f"task {task_id} status")

    async def submit(self, label: str) -> str:
        response = await self.request(
            "POST", "/api/research", json={"goal": f"p01-fake:{label}"}
        )
        if response.status_code != 202:
            raise MeasurementFailure("Controlled task submission was not accepted")
        return response.json()["id"]

    async def listen_cancel(
        self, task_id: str, cursor: str, ready: asyncio.Event
    ) -> dict:
        assert self.client is not None
        async with self.client.stream(
            "GET",
            f"/api/research/{task_id}/events",
            headers={"Last-Event-ID": cursor},
            timeout=10,
        ) as response:
            if response.status_code != 200:
                raise MeasurementFailure("SSE subscription failed")
            ready.set()
            payload = None
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    payload = json.loads(line[6:])
                if not line and payload is not None:
                    if (
                        payload["event_type"] == "cancel_requested"
                        and payload["task_id"] == task_id
                    ):
                        received_counter = time.perf_counter()
                        received = datetime.now(UTC)
                        timestamp = datetime.fromisoformat(payload["timestamp"])
                        return {
                            "received_at": received.isoformat(),
                            "received_perf_counter_seconds": received_counter,
                            "event": payload,
                            "remote_wall_clock_diagnostic": {
                                "event_timestamp": timestamp.isoformat(),
                                "client_receive_minus_database_event_seconds": (
                                    received - timestamp
                                ).total_seconds(),
                                "used_for_latency_acceptance": False,
                            },
                        }
                    payload = None
        raise MeasurementFailure("SSE ended before the cancellation event")

    async def crash_and_recover(self, targets: list[str], generation: int) -> None:
        assert self.store is not None
        old_worker = self.worker()
        if old_worker is None:
            raise MeasurementFailure(
                "Could not identify the launcher-owned fake Worker"
            )
        old_records = {task_id: await self.task(task_id) for task_id in targets}
        if any(task.status != "running" for task in old_records.values()):
            raise MeasurementFailure("Crash targets are not both running")

        async def calls_started():
            for task_id, task in old_records.items():
                calls = await self.store.list_calls(OWNER, task_id)
                if not any(
                    call.fencing_token == task.fencing_token
                    and call.status == "started"
                    for call in calls
                ):
                    return False
            return True

        await self.wait_until(calls_started, 10, "controlled calls started before kill")
        old_pid = old_worker.pid
        old_children = old_worker.children(recursive=True)
        began = time.perf_counter()
        self.evidence["process_events"].append(
            {
                "at": now(),
                "event": "controlled_worker_kill",
                "pid": old_pid,
                "generation": generation,
            }
        )
        # Every terminated process is a captured descendant of this launcher's Worker.
        for process in reversed(old_children):
            try:
                process.kill()
            except psutil.NoSuchProcess:
                pass
        try:
            old_worker.kill()
        except psutil.NoSuchProcess:
            pass

        async def replacement():
            return self.worker(excluding=old_pid)

        new_worker = await self.wait_until(replacement, 60, "Worker restart")
        restart_seconds = time.perf_counter() - began
        self.check(
            f"worker_restart_{generation}",
            restart_seconds <= 60,
            seconds=restart_seconds,
            old_pid=old_pid,
            new_pid=new_worker.pid,
        )

        async def resolved():
            current = {task_id: await self.task(task_id) for task_id in targets}
            if generation == 1:
                done = all(
                    task.status in TERMINAL
                    or (
                        task.status == "running"
                        and task.fencing_token > old_records[task_id].fencing_token
                    )
                    for task_id, task in current.items()
                )
            else:
                done = all(task.status in TERMINAL for task in current.values())
            return current if done else None

        current = await self.wait_until(resolved, 120, "lease recovery or terminal")
        recovery_seconds = time.perf_counter() - began
        self.check(
            f"task_resolution_{generation}",
            recovery_seconds <= 120,
            seconds=recovery_seconds,
            before={key: asdict(value) for key, value in old_records.items()},
            after={key: asdict(value) for key, value in current.items()},
        )
        for task_id in targets:
            try:
                await self.store.append_event(
                    task_id, old_records[task_id].fencing_token, "step_evaluated"
                )
            except FenceLost:
                self.check(f"old_token_rejected_{generation}_{task_id}", True)
            else:
                self.check(f"old_token_rejected_{generation}_{task_id}", False)
            calls = await self.store.list_calls(OWNER, task_id)
            self.check(
                f"interrupted_call_unknown_{generation}_{task_id}",
                any(
                    call.fencing_token == old_records[task_id].fencing_token
                    and call.status == "unknown_outcome"
                    and call.known_cost_cny is None
                    for call in calls
                ),
            )
        if generation == 2:
            self.check(
                "second_failure_honest_terminal",
                all(
                    row.status == "failed"
                    and row.stop_reason == "second_worker_failure"
                    for row in current.values()
                ),
            )

    async def wait_runtime_ready(self) -> None:
        assert self.client is not None

        async def ready():
            try:
                response = await self.client.get("/openapi.json")
                return (
                    response.status_code == 200
                    and self.worker()
                    and self.owns_api_listener()
                )
            except (httpx.HTTPError, psutil.Error):
                return None

        await self.wait_until(ready, 60, "API and fake Worker startup")

    async def exercise(self) -> None:
        assert self.store is not None
        self.client = httpx.AsyncClient(
            base_url=f"http://127.0.0.1:{self.args.port}", timeout=3
        )
        await self.wait_runtime_ready()
        tasks = []
        for index in range(2):
            task_id = await self.submit(str(index))
            tasks.append(task_id)
            await self.wait_status(task_id, {"running"})
        for index in range(2, 10):
            tasks.append(await self.submit(str(index)))
        current = await self.store.list_tasks(OWNER)
        counts = {
            status: sum(row.status == status for row in current)
            for status in ("running", "queued")
        }
        self.check(
            "two_running_eight_queued",
            counts == {"running": 2, "queued": 8},
            counts=counts,
        )
        response = await self.request(
            "POST", "/api/research", json={"goal": "p01-fake:eleventh"}
        )
        after = await self.store.list_tasks(OWNER)
        self.check(
            "eleventh_429_without_insert",
            response.status_code == 429
            and len(after) == 10
            and all(row.goal != "p01-fake:eleventh" for row in after),
            status_code=response.status_code,
            retry_after=response.headers.get("Retry-After"),
            persisted_task_count=len(after),
        )

        sampled = []
        for index in range(self.args.samples):
            path = (
                "/api/research"
                if index % 2 == 0
                else f"/api/research/{tasks[index % 2]}"
            )
            response = await self.request("GET", path)
            sampled.append(self.evidence["requests"][-1]["latency_seconds"])
            if response.status_code != 200:
                self.check(
                    f"load_response_{index}", False, status_code=response.status_code
                )
        p95 = sorted(sampled)[math.ceil(0.95 * len(sampled)) - 1]
        self.check(
            "api_load_p95",
            p95 <= 1,
            seconds=p95,
            sample_count=len(sampled),
            samples_seconds=sampled,
        )

        queued_cancel = await self.request("POST", f"/api/research/{tasks[-1]}/cancel")
        replacement = await self.submit("replacement")
        self.check(
            "queued_cancel_releases_capacity",
            queued_cancel.status_code == 200
            and queued_cancel.json().get("cancelled") is True,
            response=queued_cancel.json(),
            replacement_task_id=replacement,
        )

        events = await self.store.list_events(OWNER, tasks[0])
        cursor = str(UUID(int=events[-1].id))
        sse_ready = asyncio.Event()
        listener = asyncio.create_task(self.listen_cancel(tasks[0], cursor, sse_ready))
        self.background_tasks.append(listener)
        await asyncio.wait_for(sse_ready.wait(), timeout=5)
        cancel_request_started_at = now()
        cancel_request_started_counter = time.perf_counter()
        cancelled = await self.request("POST", f"/api/research/{tasks[0]}/cancel")
        cancel_latency = self.evidence["requests"][-1]["latency_seconds"]
        self.check(
            "running_cancel_persisted_confirmation",
            cancelled.status_code == 200
            and cancelled.json().get("cancellation_requested") is True
            and cancel_latency <= 1,
            seconds=cancel_latency,
            response=cancelled.json(),
        )
        observed = await asyncio.wait_for(listener, timeout=10)
        latency = (
            observed["received_perf_counter_seconds"] - cancel_request_started_counter
        )
        self.check(
            "sse_committed_replay_upper_bound",
            0 <= latency <= 2,
            method="same_client_request_start_to_receive_upper_bound",
            request_started_at=cancel_request_started_at,
            request_started_perf_counter_seconds=cancel_request_started_counter,
            request_start_to_receive_upper_bound_seconds=latency,
            **observed,
        )
        await self.wait_status(tasks[0], {"cancelled"})
        await self.wait_status(tasks[2], {"running"})
        targets = [tasks[1], tasks[2]]
        await self.crash_and_recover(targets, 1)
        await self.crash_and_recover(targets, 2)

        for row in await self.store.list_tasks(OWNER):
            if row.status not in TERMINAL:
                (self.control / f"{row.id}.release").touch(exist_ok=False)

        async def all_terminal():
            rows = await self.store.list_tasks(OWNER)
            return rows if all(row.status in TERMINAL for row in rows) else None

        final = await self.wait_until(all_terminal, 60, "remaining controlled tasks")
        self.check(
            "no_lost_task",
            len(final) == 11 and all(row.status in TERMINAL for row in final),
            count=len(final),
        )
        snapshots = []
        for row in final:
            events = await self.store.list_events(OWNER, row.id)
            calls = await self.store.list_calls(OWNER, row.id)
            cost = await self.store.get_cost(OWNER, row.id)
            terminal_count = sum(
                event.event_type == "task_finished" for event in events
            )
            self.check(
                f"unique_terminal_{row.id}",
                terminal_count == 1,
                terminal_count=terminal_count,
            )
            snapshots.append(
                {
                    "task": asdict(row),
                    "events": [asdict(event) for event in events],
                    "calls": [asdict(call) for call in calls],
                    "cost": asdict(cost),
                }
            )
        self.evidence["task_timelines"] = snapshots
        async with self.engine.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        select(PgEvent.task_id)
                        .where(PgEvent.event_type == "task_started")
                        .order_by(PgEvent.id)
                    )
                )
                .scalars()
                .all()
            )
        first_claims = list(dict.fromkeys(rows))
        expected = [*tasks[:-1], replacement]
        self.check(
            "fifo_first_claims",
            first_claims == expected,
            actual=first_claims,
            expected=expected,
        )
        self.check(
            "no_external_call_kind",
            all(
                call["phase"] == "controlled_fake.wait" and call["kind"] == "tool"
                for snapshot in snapshots
                for call in snapshot["calls"]
            ),
        )
        async with self.engine.connect() as connection:
            before = datetime.now(UTC).timestamp()
            database_time = await connection.scalar(text("SELECT clock_timestamp()"))
            after = datetime.now(UTC).timestamp()
        final_offset = database_time.timestamp() - (before + after) / 2
        self.evidence["database_clock_drift_diagnostic"] = {
            "sampled_at": now(),
            "initial_offset_seconds": self.clock_offset_seconds,
            "final_offset_seconds": final_offset,
            "drift_seconds": final_offset - self.clock_offset_seconds,
            "final_uncertainty_seconds": (after - before) / 2,
            "used_for_latency_acceptance": False,
        }

    async def database_available(self) -> bool:
        async def probe() -> None:
            async with self.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))

        began = time.perf_counter()
        error_type = None
        try:
            await asyncio.wait_for(probe(), timeout=3)
            available = True
        except (SQLAlchemyError, OSError) as exc:
            available = False
            error_type = type(exc).__name__
        self.evidence["database_outage"]["probe_samples"].append(
            {
                "at": now(),
                "available": available,
                "error_type": error_type,
                "latency_seconds": time.perf_counter() - began,
            }
        )
        return available

    async def await_database(self, available: bool, seconds: float) -> None:
        deadline = time.perf_counter() + seconds
        while time.perf_counter() < deadline:
            if await self.database_available() is available:
                return
            await asyncio.sleep(0.2)
        raise MeasurementFailure("Manual database stop/restore deadline exceeded")

    async def task_snapshots(self, task_ids: list[str]) -> list[dict[str, Any]]:
        assert self.store is not None
        snapshots = []
        for task_id in task_ids:
            row = await self.task(task_id)
            events = await self.store.list_events(OWNER, task_id)
            calls = await self.store.list_calls(OWNER, task_id)
            cost = await self.store.get_cost(OWNER, task_id)
            snapshots.append(
                {
                    "task": asdict(row),
                    "events": [asdict(event) for event in events],
                    "calls": [asdict(call) for call in calls],
                    "cost": asdict(cost),
                }
            )
        return snapshots

    async def exercise_database_outage(self, database_url: str) -> None:
        assert self.store is not None
        outage: dict[str, Any] = {"manual_service_control": True, "probe_samples": []}
        self.evidence["database_outage"] = outage
        initial_count = len(await self.store.list_tasks(OWNER))
        targets = []
        for index in range(2):
            task_id = await self.submit(f"outage-{index}")
            targets.append(task_id)
            await self.wait_status(task_id, {"running"})
        outage["task_ids"] = targets
        before = {task_id: await self.task(task_id) for task_id in targets}

        async def started_calls():
            for task_id, task in before.items():
                calls = await self.store.list_calls(OWNER, task_id)
                if not any(
                    call.fencing_token == task.fencing_token
                    and call.status == "started"
                    for call in calls
                ):
                    return False
            return True

        await self.wait_until(started_calls, 10, "outage controlled calls started")
        outage["before"] = {key: asdict(value) for key, value in before.items()}
        outage["stop_wait_started_at"] = now()
        stop_wait_started = time.perf_counter()
        print("WAITING_FOR_DATABASE_STOP", flush=True)
        await self.await_database(False, 90)
        outage["loss_detected_at"] = now()
        outage["stop_detection_seconds"] = time.perf_counter() - stop_wait_started

        async def worker_paused():
            return self.worker() is None

        try:
            await self.wait_until(
                worker_paused, 15, "Worker paused during database outage"
            )
            self.check("outage_worker_paused", True)
        except MeasurementFailure:
            self.check("outage_worker_paused", False)
        self.check(
            "outage_launcher_keeps_api_process",
            self.launcher is not None and self.launcher.poll() is None,
        )
        for name, path, body in (
            ("submit", "/api/research", {"goal": "p01-fake:outage-rejected"}),
            ("cancel", f"/api/research/{targets[0]}/cancel", None),
        ):
            try:
                response = await self.request(
                    "POST", path, **({"json": body} if body else {})
                )
            except httpx.HTTPError as exc:
                self.check(f"outage_{name}_503", False, error_type=type(exc).__name__)
            else:
                self.check(
                    f"outage_{name}_503",
                    response.status_code == 503,
                    status_code=response.status_code,
                )
        outage["restore_wait_started_at"] = now()
        restore_wait_started = time.perf_counter()
        print("WAITING_FOR_DATABASE_RESTORE", flush=True)
        await self.await_database(True, 120)
        outage["restore_detected_at"] = now()
        outage["restore_detection_seconds"] = time.perf_counter() - restore_wait_started

        rows = await self.store.list_tasks(OWNER)
        restored = {task_id: await self.task(task_id) for task_id in targets}
        self.check(
            "outage_rejected_writes_not_committed",
            len(rows) == initial_count + 2
            and all(row.goal != "p01-fake:outage-rejected" for row in rows)
            and all(not row.cancellation_requested for row in restored.values()),
            persisted_task_count=len(rows),
            expected_task_count=initial_count + 2,
            cancellation_requested={
                key: row.cancellation_requested for key, row in restored.items()
            },
        )
        outage["after_restore_before_launcher_restart"] = {
            key: asdict(row) for key, row in restored.items()
        }
        self.check("outage_worker_stays_paused_after_restore", self.worker() is None)
        if not await self.stop_launcher("outage_launcher_owned_process_cleanup"):
            raise MeasurementFailure(
                "Owned launcher descendants survived outage cleanup"
            )
        await asyncio.to_thread(assert_port_available, self.args.port)
        restart_started = time.perf_counter()
        outage["launcher_restart_started_at"] = now()
        # The initial empty-database guard is deliberately not repeated. Only
        # this same launcher is restarted; Alembic upgrade is idempotent.
        self.start(database_url)
        await self.wait_runtime_ready()

        async def resolved():
            current = {task_id: await self.task(task_id) for task_id in targets}
            return (
                current
                if all(
                    row.status in TERMINAL
                    or (
                        row.status == "running"
                        and row.fencing_token > before[task_id].fencing_token
                    )
                    for task_id, row in current.items()
                )
                else None
            )

        remaining = 120 - (time.perf_counter() - restart_started)
        if remaining <= 0:
            raise MeasurementFailure(
                "Outage recovery exceeded the task resolution deadline"
            )
        recovered = await self.wait_until(
            resolved, remaining, "outage task recovery or honest terminal"
        )
        resolution_seconds = time.perf_counter() - restart_started
        self.check(
            "outage_task_resolution_after_launcher_restart",
            resolution_seconds <= 120,
            seconds=resolution_seconds,
            after={key: asdict(row) for key, row in recovered.items()},
        )
        for task_id in targets:
            try:
                await self.store.append_event(
                    task_id, before[task_id].fencing_token, "step_evaluated"
                )
            except FenceLost:
                self.check(f"outage_old_token_rejected_{task_id}", True)
            else:
                self.check(f"outage_old_token_rejected_{task_id}", False)
            calls = await self.store.list_calls(OWNER, task_id)
            self.check(
                f"outage_interrupted_call_unknown_{task_id}",
                any(
                    call.fencing_token == before[task_id].fencing_token
                    and call.status == "unknown_outcome"
                    and call.known_cost_cny is None
                    for call in calls
                ),
            )
            if recovered[task_id].status not in TERMINAL:
                (self.control / f"{task_id}.release").touch(exist_ok=False)
        for task_id in targets:
            await self.wait_status(task_id, set(TERMINAL), seconds=30)
        snapshots = await self.task_snapshots(targets)
        outage["task_timelines"] = snapshots
        for snapshot in snapshots:
            task_id = snapshot["task"]["id"]
            terminal_count = sum(
                event["event_type"] == "task_finished" for event in snapshot["events"]
            )
            self.check(
                f"outage_unique_terminal_{task_id}",
                terminal_count == 1,
                terminal_count=terminal_count,
            )
        checks = [
            value
            for name, value in self.evidence["checks"].items()
            if name.startswith("outage_")
        ]
        passed = all(check["passed"] for check in checks)
        outage["outage_scope"] = "verified_fake_only" if passed else "failed_fake_only"
        self.evidence["outage_scope"] = outage["outage_scope"]
        self.evidence["scope_limits"]["database_outage_manual_restore"] = (
            "VERIFIED_CONTROLLED_FAKE_ONLY" if passed else "FAILED_CONTROLLED_FAKE_ONLY"
        )

    async def stop_launcher(self, check_name: str) -> bool:
        owned = []
        launcher = self.launcher
        if launcher is not None:
            try:
                owned = psutil.Process(launcher.pid).children(recursive=True)
            except psutil.NoSuchProcess:
                pass
            try:
                launcher.send_signal(signal.CTRL_BREAK_EVENT)
                await asyncio.to_thread(launcher.wait, timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                pass
            if launcher.poll() is None:
                try:
                    launcher_process = psutil.Process(launcher.pid)
                    launcher_process.suspend()
                    latest = launcher_process.children(recursive=True)
                    owned = list(
                        {process.pid: process for process in (*owned, *latest)}.values()
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                launcher.terminate()
            for process in reversed(owned):
                try:
                    process.terminate()
                except psutil.NoSuchProcess:
                    pass
            try:
                await asyncio.to_thread(launcher.wait, timeout=5)
            except subprocess.TimeoutExpired:
                launcher.kill()
                await asyncio.to_thread(launcher.wait, timeout=5)
            _, alive = await asyncio.to_thread(psutil.wait_procs, owned, timeout=3)
            for process in alive:
                try:
                    process.kill()
                except psutil.NoSuchProcess:
                    pass
            _, survivors = await asyncio.to_thread(psutil.wait_procs, alive, timeout=3)
            self.check(
                check_name,
                not survivors,
                remaining_pids=[process.pid for process in survivors],
            )
            if self.reader is not None:
                await asyncio.to_thread(self.reader.join, timeout=2)
            self.evidence["process_events"].append(
                {
                    "at": now(),
                    "event": "launcher_stopped",
                    "pid": launcher.pid,
                    "generation": self.launch_count,
                }
            )
            self.launcher = None
            self.reader = None
            return not survivors
        return True

    async def cleanup(self) -> None:
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        if self.client is not None:
            await self.client.aclose()
        if self.resource_task is not None:
            self.resource_task.cancel()
            await asyncio.gather(self.resource_task, return_exceptions=True)
        await self.stop_launcher("launcher_owned_process_cleanup")
        if self.store is not None and "task_timelines" not in self.evidence:
            try:
                partial = []
                for row in await self.store.list_tasks(OWNER):
                    events = await self.store.list_events(OWNER, row.id)
                    calls = await self.store.list_calls(OWNER, row.id)
                    cost = await self.store.get_cost(OWNER, row.id)
                    partial.append(
                        {
                            "task": asdict(row),
                            "events": [asdict(event) for event in events],
                            "calls": [asdict(call) for call in calls],
                            "cost": asdict(cost),
                        }
                    )
                self.evidence["partial_task_timelines"] = partial
            except Exception as exc:  # noqa: BLE001 - best-effort evidence without exception messages
                self.evidence["partial_snapshot_error_type"] = type(exc).__name__
        outage = self.evidence.get("database_outage")
        if outage and "task_ids" in outage and "task_timelines" not in outage:
            try:
                outage["partial_task_timelines"] = await self.task_snapshots(
                    outage["task_ids"]
                )
            except Exception as exc:  # noqa: BLE001 - best-effort evidence without exception messages
                outage["partial_snapshot_error_type"] = type(exc).__name__
        if self.engine is not None:
            await self.engine.dispose()
        samples = self.evidence["resource_samples"]
        self.evidence["resource_peaks"] = {
            key: max((sample[key] for sample in samples), default=None)
            for key in (
                "host_cpu_percent",
                "host_memory_used_bytes",
                "host_memory_percent",
                "launcher_descendant_rss_sum_bytes",
            )
        }
        self.evidence["finished_at"] = now()
        self.evidence["local_checks_passed"] = (
            bool(self.evidence["checks"])
            and all(check["passed"] for check in self.evidence["checks"].values())
            and not self.evidence["failures"]
        )
        self.output.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(
            self.evidence, ensure_ascii=False, indent=2, default=json_default
        ).encode("utf-8")
        with self.output.open("xb") as stream:
            stream.write(encoded)
        with self.output.with_suffix(self.output.suffix + ".sha256").open(
            "x", encoding="ascii"
        ) as stream:
            stream.write(hashlib.sha256(encoded).hexdigest() + "\n")

    async def run(self) -> int:
        try:
            database_url = await self.prepare()
            self.start(database_url)
            await self.exercise()
            if self.args.manual_database_outage:
                await self.exercise_database_outage(database_url)
        except Exception as exc:  # noqa: BLE001 - record exception type only, never credential-bearing messages
            failure = {"type": type(exc).__name__}
            if isinstance(exc, MeasurementFailure):
                failure["message"] = str(exc)
            self.evidence["failures"].append(failure)
        finally:
            await self.cleanup()
        print(
            json.dumps(
                {
                    "evidence": str(self.output),
                    "local_checks_passed": self.evidence["local_checks_passed"],
                    "phase_status": "P01_INCOMPLETE",
                }
            )
        )
        return 0 if self.evidence["local_checks_passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-name", required=True)
    parser.add_argument(
        "--output", required=True, help="New JSON file under repository data/p01"
    )
    parser.add_argument("--port", type=int, default=8014)
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--wsl-distribution", default="Ubuntu")
    parser.add_argument(
        "--manual-database-outage",
        action="store_true",
        help="After normal checks, prompt the operator to stop/restore PostgreSQL; never control the service automatically",
    )
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535 or args.samples < 20:
        parser.error("Use a port from 1024 to 65535 and at least 20 latency samples")
    return asyncio.run(Measurement(args).run())


if __name__ == "__main__":
    raise SystemExit(main())
