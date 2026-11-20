#!/usr/bin/env python3
import pathlib

for root, directories, files in pathlib.Path.cwd().walk():
    for file_in in [root / f for f in files if f.endswith(".png")]:
        file_out = (root / file_in.parent.stem).with_suffix(".png")
        print(f"Renaming: {file_in}\n"
              f"To:       {file_out}")
        file_in.replace(file_out)



