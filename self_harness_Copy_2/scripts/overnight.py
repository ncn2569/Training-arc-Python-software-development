"""Run overnight in this terminal, mirroring stdout/stderr into a timestamped log."""

from __future__ import annotations

import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from typing import TextIO

from ..cli import main
from ..config import ARTIFACTS_DIR


class Tee:
    def __init__(self, terminal: TextIO, log: TextIO):
        self.terminal, self.log = terminal, log

    def write(self, text: str) -> int:
        self.terminal.write(text)
        self.log.write(text)
        self.flush()
        return len(text)

    def flush(self) -> None:
        self.terminal.flush()
        self.log.flush()


def run() -> int:
    if "--dry-run" in sys.argv[1:]:
        return main(["overnight", *sys.argv[1:]])
    log_dir = ARTIFACTS_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"overnight-{datetime.now():%Y%m%d-%H%M%S-%f}.log"
    print(f"Overnight log: {path}")
    with path.open("w", encoding="utf-8") as log:
        with redirect_stdout(Tee(sys.stdout, log)), redirect_stderr(Tee(sys.stderr, log)):
            try:
                result = main(["overnight", *sys.argv[1:]])
                print(f"Overnight exit code: {result}")
                return result
            except KeyboardInterrupt:
                print("Interrupted. Completed benches and round checkpoints are retained; there is no automatic resume.")
                return 130


if __name__ == "__main__":
    raise SystemExit(run())
