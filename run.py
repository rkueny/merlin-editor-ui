"""PyInstaller entry point — wraps merlin_gui.app.main as a top-level script."""

import sys

from merlin_gui.app import main


if __name__ == "__main__":
    sys.exit(main())
