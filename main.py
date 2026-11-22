#!/usr/bin/env python3
"""Deliver the finished poster for 21 November 2026 to the harness.

build_image.py already painted entry.png and left it beside this file;
the grading sandbox runs this script with no network and nothing
installed, so all it does is copy that one PNG into /output/entry.png.
It uses only the standard library, and copying the same bytes twice
gives the same file twice -- the run is deterministic by construction.

The picture: a code-drawn front page summing up Saturday 21 November
2026 in 44 sourced stories -- the COP31 overtime deadlock in Antalya
leads; Ukraine's Poland fallout and Druzhba reply, the Hormuz
tanker-attack peak, the Wall Street correction and the Houthi-Saudi
missile exchange fill four panels; a 39-item wire carries the rest of
the day, every item source-tagged and confidence-marked.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.realpath(__file__))


def main(argv=None):
    src = os.path.join(HERE, "entry.png")
    if not os.path.isfile(src):
        sys.stderr.write("entry.png is missing; run build_image.py first\n")
        return 1
    dest_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    dest = os.path.join(dest_dir, "entry.png")
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copyfile(src, dest)
    with open(dest, "rb") as fh:
        blob = fh.read()
    sys.stdout.write(f"wrote {dest}: {len(blob)} bytes\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
