
"""Punkt wejścia aplikacji GUI."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.gui.main_window import GlowneOkno


def main() -> int:
    katalog_projektu = Path(__file__).resolve().parent
    app = QApplication(sys.argv)
    app.setApplicationName("Symulator stacji ładowania EV")
    okno = GlowneOkno(katalog_projektu)
    okno.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
