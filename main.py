"""Entry point for the GTA VI launch-day Twitch CCU forecaster.

Reads every case file the sandbox puts in the input directory, asks model.py for
the 23 hourly quantile rows, and writes one <id>.out per case. Standard library
only, deterministic, no network.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from model import forecast  # noqa: E402

INPUT = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))


def run() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for src in sorted(INPUT.glob("*.in")):
        with open(src, encoding="utf-8") as fh:
            case = json.load(fh)
        name = str(case.get("id", src.stem)) + ".out"
        with open(OUTPUT / name, "w", encoding="utf-8") as fh:
            json.dump(forecast(case), fh, separators=(",", ":"))


if __name__ == "__main__":
    run()
