#!/usr/bin/env python3
"""Executable entry point that copies entry.png into MAKEFUN_OUTPUT_DIR."""

import os
import shutil


def main() -> None:
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(output_dir, exist_ok=True)

    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    dst = os.path.join(output_dir, "entry.png")
    if not os.path.exists(src): raise FileNotFoundError(src)
    shutil.copy2(src, dst)
    print(dst)


if __name__ == "__main__":
    main()
