"""Record reproducibility environment for research-method rule compliance."""
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = r"d:\Master Exers\Big Data\Recomendation_System"
OUT = os.path.join(ROOT, "logs", "hardware_manifest.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

def command_text(command):
    try:
        p = subprocess.run(command, capture_output=True, text=True, timeout=20)
        return (p.stdout or p.stderr).strip()
    except Exception as exc:
        return f"unavailable: {exc}"

try:
    import pyspark
    spark_version = pyspark.__version__
except Exception as exc:
    spark_version = f"unavailable: {exc}"

record = {
    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    "hostname": platform.node(),
    "os": platform.platform(),
    "python": sys.version,
    "python_executable": sys.executable,
    "cpu_logical": os.cpu_count(),
    "memory_total_bytes": None,
    "disk_free_bytes": shutil.disk_usage(ROOT).free,
    "spark_version": spark_version,
    "java_version": command_text(["java", "-version"]),
    "git_commit": command_text(["git", "rev-parse", "HEAD"]),
    "dataset_checksum_file": os.path.join(ROOT, "data", "raw", "CHECKSUMS.sha256"),
    "protocol": os.path.join(ROOT, "configs", "experiment_protocol_v1.json")
}
with open(OUT, "w", encoding="utf-8") as handle:
    json.dump(record, handle, ensure_ascii=False, indent=2)
print(json.dumps(record, ensure_ascii=False, indent=2))
