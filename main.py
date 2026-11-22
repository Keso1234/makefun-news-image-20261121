"""Entry for news-image-20261121: copy the pre-rendered poster to /output.

Standard library only, fully self-contained: no local imports, so it runs
under the grader's `python3 -P -s main.py` exactly as it runs here.
"""

import os
import shutil
from pathlib import Path

def main():
    here = Path(__file__).resolve().parent
    out = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(here / "entry.png", out / "entry.png")


if __name__ == "__main__":
    main()
