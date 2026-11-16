"""Small run logger for Jupyter notebooks."""
from __future__ import annotations

import json
import os
import platform
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class NotebookRun:
    def __init__(self, project_root: str | Path, notebook_id: str, metadata: dict[str, Any] | None = None):
        self.project_root = Path(project_root).resolve()
        self.notebook_id = notebook_id
        self.run_id = f"{datetime.now():%Y%m%d_%H%M%S}_{notebook_id}_{uuid.uuid4().hex[:8]}"
        self.run_dir = self.project_root / "runs" / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=False)
        self.log_path = self.project_root / "logs" / "notebooks" / f"{self.run_id}.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        for folder in ("checkpoints", "outputs", "figures", "checks"):
            (self.run_dir / folder).mkdir()
        self.manifest_path = self.run_dir / "manifest.json"
        self.manifest = {
            "run_id": self.run_id, "notebook_id": notebook_id, "status": "RUNNING",
            "started_at_utc": utc_now(), "python_version": platform.python_version(),
            "python_executable": sys.executable, "metadata": metadata or {},
            "cells": [], "checkpoints": [], "current_cell": None,
        }
        self._save()
        self.log("RUN_START")

    def _save(self) -> None:
        temp = self.manifest_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        os.replace(temp, self.manifest_path)

    def log(self, event: str, **fields: Any) -> None:
        record = {"time_utc": utc_now(), "event": event, **fields}
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def attach_ipython(self, shell: Any) -> None:
        self._cell_counter = 0

        def before(info: Any) -> None:
            self._cell_counter += 1
            source = (getattr(info, "raw_cell", "") or "").strip().splitlines()
            title = source[0].lstrip("# " ).strip()[:160] if source else ""
            cell_id = f"CELL{self._cell_counter:03d}"
            self._active_cell = cell_id
            self._active_cell_started = time.perf_counter()
            self.manifest["current_cell"] = cell_id
            self.manifest["cells"].append({"cell_id": cell_id, "title": title, "status": "RUNNING", "started_at_utc": utc_now()})
            self._save()
            self.log("CELL_START", cell_id=cell_id, title=title)

        def after(result: Any) -> None:
            cell_id = getattr(self, "_active_cell", None)
            if not cell_id:
                return
            record = next(row for row in reversed(self.manifest["cells"]) if row["cell_id"] == cell_id)
            error = getattr(result, "error_in_exec", None) or getattr(result, "error_before_exec", None)
            record["finished_at_utc"] = utc_now()
            record["duration_seconds"] = round(time.perf_counter() - self._active_cell_started, 3)
            outputs = []
            for output in getattr(result, "outputs", []) or []:
                text = getattr(output, "data", {}).get("text/plain")
                if text:
                    outputs.append(str(text)[:2000])
            if outputs:
                record["outputs_preview"] = outputs
            if error is None:
                record["status"] = "COMPLETED"
                self.log("CELL_COMPLETED", cell_id=cell_id, duration_seconds=record["duration_seconds"], outputs_preview=outputs)
            else:
                record["status"] = "FAILED"
                record["error"] = f"{type(error).__name__}: {error}"
                self.manifest["status"] = "FAILED"
                self.log("CELL_FAILED", cell_id=cell_id, duration_seconds=record["duration_seconds"], error=record["error"])
            self.manifest["current_cell"] = None
            self._save()
            self._active_cell = None

        shell.events.register("pre_run_cell", before)
        shell.events.register("post_run_cell", after)
        self.log("CELL_LOGGER_ATTACHED")

    def checkpoint(self, step_id: str, status: str, checks: dict[str, Any] | None = None, note: str | None = None) -> Path:
        if status not in {"PASS", "FAIL", "INFO"}:
            raise ValueError("status must be PASS, FAIL, or INFO")
        record = {"step_id": step_id, "status": status, "time_utc": utc_now(), "checks": checks or {}, "note": note}
        path = self.run_dir / "checkpoints" / f"{step_id}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        self.manifest["checkpoints"].append(record)
        self._save()
        self.log("CHECKPOINT", step_id=step_id, status=status, checks=checks or {})
        return path

    def finish(self, status: str = "COMPLETED", summary: dict[str, Any] | None = None) -> None:
        if status not in {"COMPLETED", "FAILED", "INTERRUPTED"}:
            raise ValueError("invalid terminal status")
        self.manifest.update(status=status, finished_at_utc=utc_now(), current_cell=None, summary=summary or {})
        self._save()
        self.log("RUN_FINISH", status=status)
