"""
Настройка логирования: консоль + файл bot.log в каталоге проекта.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Final

LOG_FORMAT: Final[str] = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"


def setup_logging(project_dir: Path | None = None, level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)

    # Удаляем дублирующиеся при повторном вызове
    for h in root.handlers[:]:
        root.removeHandler(h)

    fmt = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.addHandler(sh)

    base = project_dir or Path(__file__).resolve().parent
    log_path = base / "bot.log"
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # Шум от httpx/aiogram при необходимости
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)
