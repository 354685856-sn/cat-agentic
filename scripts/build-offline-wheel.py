#!/usr/bin/env python3
"""Build the project wheel with the Python standard library only."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import sys
import tomllib
import zipfile
from pathlib import Path


def record_hash(data: bytes) -> str:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    return f"sha256={digest.decode('ascii')}"


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build-offline-wheel.py PROJECT_ROOT WHEEL_DIR")

    root = Path(sys.argv[1]).resolve()
    wheel_dir = Path(sys.argv[2]).resolve()
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    name = str(project["name"])
    version = str(project["version"])
    normalized = name.replace("-", "_")
    dist_info = f"{normalized}-{version}.dist-info"
    wheel_path = wheel_dir / f"{normalized}-{version}-py3-none-any.whl"
    package_root = root / "src" / "x_agentic_workflow"
    wheel_dir.mkdir(parents=True, exist_ok=True)

    metadata_lines = [
        "Metadata-Version: 2.4",
        f"Name: {name}",
        f"Version: {version}",
        f"Summary: {project['description']}",
        f"Requires-Python: {project['requires-python']}",
    ]
    metadata_lines.extend(f"Requires-Dist: {item}" for item in project.get("dependencies", []))
    metadata = ("\n".join(metadata_lines) + "\n").encode()
    wheel = (
        "Wheel-Version: 1.0\n"
        "Generator: cat-agentic-offline-builder\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    ).encode()
    entry_points = (
        "[console_scripts]\n"
        "cat-agentic = x_agentic_workflow.cli:app\n"
        "xaw = x_agentic_workflow.cli:app\n"
        "x-agentic-workflow = x_agentic_workflow.cli:app\n"
    ).encode()

    files: dict[str, bytes] = {}
    for path in sorted(package_root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        files[path.relative_to(root / "src").as_posix()] = path.read_bytes()
    files[f"{dist_info}/METADATA"] = metadata
    files[f"{dist_info}/WHEEL"] = wheel
    files[f"{dist_info}/entry_points.txt"] = entry_points

    rows = [[path, record_hash(data), str(len(data))] for path, data in files.items()]
    rows.append([f"{dist_info}/RECORD", "", ""])
    record_buffer = io.StringIO(newline="")
    csv.writer(record_buffer, lineterminator="\n").writerows(rows)
    files[f"{dist_info}/RECORD"] = record_buffer.getvalue().encode()

    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, data in files.items():
            archive.writestr(path, data)
    print(wheel_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
