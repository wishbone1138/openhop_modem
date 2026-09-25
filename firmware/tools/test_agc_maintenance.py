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

    web = (firmware_dir / "src" / "ota_manager.cpp").read_text()
    assert "<summary>Station AGC Recovery</summary>" in web
    assert "<form method='POST' action='/agc-reset'>" in web
    assert 'httpServer->on("/agc-reset", HTTP_POST, handleStationAgcSave);' in web
    handler = web.split("static void handleStationAgcSave() {", 1)[1].split("\n}\n", 1)[0]
    assert handler.index("if (!checkAuth()) return;") < handler.index("httpServer->hasArg(")
    assert "AgcMaintenance::parseIntervalSeconds(raw.c_str(), raw.length(), interval)" in handler
    assert "RFFrontEnd::setAgcResetIntervalSec(interval, true)" in handler
    assert "ESP.restart()" not in handler

    print("AGC maintenance contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
