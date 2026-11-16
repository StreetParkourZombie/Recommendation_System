"""Sinh artifact JSON/Parquet và tính checksum.

Mọi notebook ghi kết quả vào `runs/<run_id>/outputs/`, không ghi vào thư mục PoC
bên ngoài repo, để truy nguyên được theo run_id.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_HASH_BLOCK = 1024 * 1024


def sha256_file(path: str | Path) -> str:
    """SHA-256 của một file, đọc theo block 1 MB."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(_HASH_BLOCK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_dir(path: str | Path, pattern: str = "*.parquet") -> str:
    """SHA-256 gộp của thư mục Parquet.

    Xếp file theo tên rồi hash nối tiếp `name|sha256` từng file, nên thứ tự
    filesystem không ảnh hưởng kết quả. Không phải checksum chuẩn của Hadoop,
    chỉ để phát hiện thay đổi giữa các lần chạy.
    """
    root = Path(path)
    entries = []
    for file in sorted(root.rglob(pattern)):
        entries.append(f"{file.relative_to(root).as_posix()}|{sha256_file(file)}")
    digest = hashlib.sha256()
    for line in entries:
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def save_json(path: str | Path, obj: Any, indent: int = 2) -> Path:
    """Ghi JSON UTF-8, tạo thư mục cha nếu cần, trả đường dẫn đã ghi."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(obj, ensure_ascii=False, indent=indent, default=str),
        encoding="utf-8",
    )
    return target


def load_json(path: str | Path) -> Any:
    """Đọc JSON UTF-8."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def readback_ok(path: str | Path, expect_keys: list[str] | None = None) -> bool:
    """Đọc lại file JSON đã ghi và kiểm tra các key bắt buộc.

    Dùng trong checkpoint để chắc artifact tồn tại và đọc được, không chỉ vì
    cell không ném exception.
    """
    try:
        data = load_json(path)
    except Exception:
        return False
    if expect_keys is None:
        return True
    if not isinstance(data, dict):
        return False
    return all(key in data for key in expect_keys)


def dir_size_bytes(path: str | Path) -> int:
    """Tổng dung lượng file trong thư mục, đệ quy."""
    root = Path(path)
    if not root.exists():
        return 0
    return sum(file.stat().st_size for file in root.rglob("*") if file.is_file())

