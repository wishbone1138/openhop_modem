#!/usr/bin/env python3
"""Compile and run the host-side AGC maintenance contract."""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import tempfile


def main() -> int:
    firmware_dir = pathlib.Path(__file__).resolve().parents[1]
    compiler = shutil.which("g++")
    if compiler is None:
        raise SystemExit("g++ is required for the host-side AGC maintenance test")

    with tempfile.TemporaryDirectory(prefix="openhop-agc-maintenance-") as temp_dir:
        executable = pathlib.Path(temp_dir) / "agc_maintenance_test"
        command = [
            compiler,
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            f"-I{firmware_dir / 'include'}",
            str(firmware_dir / "tests" / "agc_maintenance_test.cpp"),
            "-o",
            str(executable),
        ]
        subprocess.run(command, check=True)
        subprocess.run([str(executable)], check=True)

    for board in ("station_g2", "station_g3"):
        board_config = (
            firmware_dir / "include" / "boards" / f"{board}.h"
        ).read_text()
        assert ".sx126x_agc_reset_interval_ms = 0," in board_config

    print("AGC maintenance contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
