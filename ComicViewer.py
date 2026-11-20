#!/usr/bin/env python3
import sys, pathlib, argparse, multiprocessing, os
sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent}")
#from comicutils.gui import viewer
from comicutils.gui2 import viewer


if __name__ == '__main__':
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser("Comic Utilities")
    parser.add_argument(
        "path",
        type=str,
        default=None,
        nargs='?',
        help="The Target Comic/Directory")
    args = parser.parse_args()

    args.path = None if args.path is None else pathlib.Path(args.path)
    viewer = viewer.ComicViewer(args.path)
