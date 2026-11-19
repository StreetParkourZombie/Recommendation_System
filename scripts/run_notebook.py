"""Chạy một notebook bằng nbclient với kernel project, lưu .executed.ipynb.

Dùng để kiểm tra notebook chạy được end-to-end trước khi giao cho người dùng,
hoặc để sinh lại artifact khi chạy batch.

Usage:
    python scripts/run_notebook.py 04
    python scripts/run_notebook.py 04 05 06
    python scripts/run_notebook.py 11 --timeout 21600   # giay, cho cell chay lau (ItemKNN)
"""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks" / "jupyter"
KERNEL_NAME = "recsys-project-venv"


def resolve(prefix: str) -> Path:
    matches = sorted(NOTEBOOK_DIR.glob(f"{prefix}*.ipynb"))
    matches = [m for m in matches if not m.name.endswith(".executed.ipynb") and "_SMOKE" not in m.name]
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one notebook for prefix {prefix!r}, found {[m.name for m in matches]}")
    return matches[0]


def run(path: Path, timeout: int = 3600) -> None:
    print(f"=== {path.name} ===", flush=True)
    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=timeout,
        kernel_name=KERNEL_NAME,
        resources={"metadata": {"path": str(ROOT)}},
        allow_errors=False,
    )
    client.execute()
    out = path.with_suffix(".executed.ipynb")
    nbformat.write(notebook, out)
    print(f"OK -> {out}", flush=True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    timeout = 3600
    if "--timeout" in sys.argv:
        timeout = int(sys.argv[sys.argv.index("--timeout") + 1])
        args = [a for a in args if a != str(timeout)]
    if not args:
        raise SystemExit("Usage: python scripts/run_notebook.py <prefix> [<prefix> ...] [--timeout <seconds>]")
    for arg in args:
        run(resolve(arg), timeout=timeout)

