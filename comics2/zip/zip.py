#!/usr/bin/env python3
import sys, zipfile, pathlib
from zipfile import ZIP_STORED, ZIP_DEFLATED, ZIP_BZIP2
__all__ = ["ZIP_STORED", "ZIP_DEFLATED", "ZIP_BZIP2"]
if sys.version_info[0] >= 3 and sys.version_info[1] >= 3:
    from zipfile import ZIP_LZMA
    __all__.append("ZIP_LZMA")
if sys.version_info[0] >= 3 and sys.version_info[1] >= 14:
    from zipfile import ZIP_ZSTANDARD
    __all__.append("ZIP_ZSTANDARD")
# <<< --------------------------- ENG IMPORTS ---------------------------- >>>


# -----------------------------------------------------------------------------
# Magic Numbers
# -----------------------------------------------------------------------------
MAGICS = (
    (0, 4, b'PK\x03\x04', "zip"),
    (0, 4, b'PK\x05\x06', "zip"),
    (0, 4, b'PK\x07\x08', "zip"))
MAGIC = lambda f: any(True for off, n, magic in MAGICS if (
    pathlib.Path(f).read_bytes()[off:off+n] == magic))


def is_zipfile(path_in: str) -> bool:
    return bool(MAGIC(path_in))


# -----------------------------------------------------------------------------
# ZipInfo
# -----------------------------------------------------------------------------
# Define ZipInfo Class in this module.
ZipInfo = zipfile.ZipInfo


# -----------------------------------------------------------------------------
# ZipFile
# -----------------------------------------------------------------------------
# ZipFile = zipfile.ZipFile


class ZipFile(zipfile.ZipFile):

    def __init__(self, file, mode, compression=zipfile.ZIP_DEFLATED, **args_in):
        progress = args_in.pop("progress") if "progress" in args_in.keys() else None
        super().__init__(file, mode, compression, **args_in)

    @property
    def pages(self) -> list:
        return list((i.filename, PIL.Image.open(
            io.BytesIO(self.open(i).read()))) for i in self.infolist() if (
                pathlib.Path(i.filename).suffix in
                PIL.Image.registered_extensions()))
