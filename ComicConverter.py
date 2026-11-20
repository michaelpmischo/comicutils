#!/usr/bin/env python3
import sys, pathlib, argparse
sys.path.append(f"{pathlib.Path.cwd().resolve().parent}")
from comicutils.converter import converter
from comicutils.comics import comic


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Comic Converter")
    parser.add_argument(
        "-convert",
        choices=list(comic.Comic.TYPES.keys()) + ["auto"],
        default=None,
        help="The output file extension to convert to.")

    parser.add_argument(
        "-strip",
        action='store_true',
        help="Strip Retromag Bullshit From the Archive.")

    parser.add_argument(
        "-delete",
        action='store_true',
        help="Delete the file after conversion")

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="The Output File/Path.")

    parser.add_argument(
        "path",
        type=str,
        help="The Target path/Archive.")

    args = parser.parse_args()
    args.path = pathlib.Path(args.path).resolve()
    args.output = pathlib.Path(args.output) if args.output is not None else args.path
    if args.convert or args.strip:
        converter = converter.Converter(
            args.path, args.output, args.convert, args.strip, args.delete)
        converter.convert()
