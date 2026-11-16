"""Generate beginner-friendly notebook 00 for project preflight."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "jupyter" / "00_environment_check.ipynb"
OUT.parent.mkdir(parents=True, exist_ok=True)
CELL_IDS = iter(range(1, 100))


def md(text):
    return {"cell_type": "markdown", "id": f"cell-{next(CELL_IDS):03d}", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "id": f"cell-{next(CELL_IDS):03d}", "execution_count": None, "metadata": {}, "outputs": [], "source": text.strip("\n").splitlines(keepends=True)}


cells = [
    md("""# 00 — Kiểm tra môi trường và tài nguyên

**Mục tiêu:** xác nhận Jupyter kernel, Python, Java, PySpark và Spark local hoạt động trước khi xử lý dữ liệu. Notebook này không tải dataset và không chạy job nặng.

**Checkpoint:** manifest trong `runs/` và log UTF-8 theo cell trong `logs/notebooks/`."""),
    md("""## Lý thuyết — Vì sao kiểm tra môi trường trước?

Notebook chạy bằng Python kernel đã chọn, không nhất thiết cùng Python với terminal. Spark local cần JVM. Kiểm tra trước giúp tách lỗi môi trường khỏi lỗi dữ liệu. `local[2]` ở đây chỉ là phép thử nhỏ; cấu hình production sẽ theo protocol đã chốt."""),
    code("""from pathlib import Path
import sys

PROJECT_ROOT = Path.cwd().resolve()
while PROJECT_ROOT != PROJECT_ROOT.parent and not (PROJECT_ROOT / "src").is_dir():
    PROJECT_ROOT = PROJECT_ROOT.parent
assert (PROJECT_ROOT / "src").is_dir(), "Cannot find project root containing src/"
sys.path.insert(0, str(PROJECT_ROOT))
print("Project root:", PROJECT_ROOT)
print("Kernel Python:", sys.executable)
print("Python version:", sys.version.split()[0])"""),
    md("""## 1. Bắt đầu run và nạp helper log

Mỗi lần chạy tạo `run_id` mới. Không ghi đè run cũ."""),
    code("""from src.recsys.notebook_logging import NotebookRun

run = NotebookRun(PROJECT_ROOT, "00_environment_check", metadata={"purpose": "environment preflight"})
from IPython import get_ipython
run.attach_ipython(get_ipython())
print("Run ID:", run.run_id)
assert PROJECT_ROOT.is_dir() and sys.executable"""),
    md("""## 2. Kiểm tra Python packages

Chỉ đọc version; notebook không tự cài hoặc nâng cấp package."""),
    code("""import importlib.metadata as md

packages = {}
for name in ["pyspark", "jupyterlab", "notebook", "ipykernel", "nbformat", "numpy", "pandas", "scipy"]:
    try:
        packages[name] = md.version(name)
    except md.PackageNotFoundError:
        packages[name] = None
print(packages)
assert packages["pyspark"] is not None, "PySpark missing in this kernel"
assert packages["ipykernel"] is not None, "ipykernel missing in this kernel"
run.log("PACKAGE_VERSIONS", versions=packages)
run.checkpoint("packages", "PASS", checks={"versions": packages})"""),
    md("""## 3. Kiểm tra Java và Spark local

Tạo session nhỏ, chạy phép đếm 10 phần tử rồi đóng session. Windows có thể báo thiếu `winutils.exe`; phép thử đạt nếu Spark action hoàn tất."""),
    code("""import os
import time
os.environ["PYSPARK_PYTHON"] = sys.executable
from pyspark.sql import SparkSession

started = time.perf_counter()
spark = (SparkSession.builder.appName("RecSysNotebook00Preflight")
         .master("local[2]")
         .config("spark.driver.memory", "2g")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
probe_count = spark.range(10).count()
spark_info = {"spark_version": spark.version, "master": spark.sparkContext.master,
              "default_parallelism": spark.sparkContext.defaultParallelism,
              "probe_count": probe_count, "elapsed_seconds": round(time.perf_counter() - started, 2)}
print(spark_info)
spark.stop()
assert probe_count == 10
run.log("SPARK_PREFLIGHT", **spark_info)
run.checkpoint("spark_local", "PASS", checks=spark_info)"""),
    md("""## 4. Kiểm tra thư mục dữ liệu và dung lượng

Chỉ kiểm tra, không tạo hoặc xóa dataset. Hiện data có thể nằm ngoài repo tại `D:/recsys_data/raw/ml-25m/`; cell này giúp tránh tải trùng."""),
    code("""from shutil import disk_usage

DATA_DIR = Path("D:/recsys_data/raw/ml-25m")
data_files = {p.name: p.stat().st_size for p in DATA_DIR.iterdir() if p.is_file()} if DATA_DIR.exists() else {}
free_bytes = disk_usage("D:/").free
print("Dataset directory exists:", DATA_DIR.exists())
print("Files:", data_files)
print("D drive free GB:", round(free_bytes / 1024**3, 2))
run.log("DATA_PATH_PREFLIGHT", directory=str(DATA_DIR), files=data_files, free_bytes=free_bytes)
run.checkpoint("data_path", "INFO", checks={"directory_exists": DATA_DIR.exists(), "files": data_files, "free_bytes": free_bytes}, note="Dataset verification happens in notebook 01.")"""),
    md("""## Kết luận và checkpoint

Cell cuối đóng run thành `COMPLETED`. Nếu cell lỗi, manifest ghi `FAILED`; sau khi sửa, chạy lại để tạo `run_id` mới."""),
    code("""summary = {"python": sys.version.split()[0], "packages": packages, "spark": spark_info,
           "data_directory_exists": DATA_DIR.exists(), "data_files": data_files}
run.finish("COMPLETED", summary=summary)
print("PREFLIGHT PASS. Inspect the run manifest and UTF-8 log under runs/ and logs/notebooks/.")"""),
]

notebook = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3.14 (BigData RecSys .venv)", "language": "python", "name": "recsys-project-venv"}, "language_info": {"name": "python"}},
    "nbformat": 4,
    "nbformat_minor": 5,
}
for index, cell in enumerate(cells):
    cell["id"] = f"cell-{index + 1:03d}"
OUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Created {OUT} with {len(cells)} cells")


