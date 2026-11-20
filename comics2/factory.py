#/usr/bin/env python3
import pathlib, typing
if __name__ == '__main__':
    import sys
    sys.path.append(f"{pathlib.Path(__file__).parent.parent.parent}")
    from comicutils.comics2 import epub, pdf, rar, sevenzip, tar, zip
else:
    from . import epub, pdf, rar, sevenzip, tar, zip

# <<< --------------------------- ENG IMPORTS ---------------------------- >>>


# -----------------------------------------------------------------------------
# Protected Module Types
# -----------------------------------------------------------------------------
_archT = typing.Union[epub.EPubFile, pdf.PdfFile, rar.RarFile, tar.TarFile, sevenzip.SevenZipFile, zip.ZipFile]
_modes = ['r', 'rb', 'w', 'a']
_modeT = typing.Literal['r', 'rb', 'w', 'a']



# -----------------------------------------------------------------------------
# Private Magic Number Based Constructor List
# -----------------------------------------------------------------------------
__CONSTRUCTORS = (
    # --------------------------------- EPubs ---------------------------------
    (0, 4, b'PK\x03\x04', lambda f: pathlib.Path(f).suffix == ".epub",
     lambda f, m, p: epub.EPubFile(f, mode=m, progress=p)),
    (0, 4, b'PK\x05\x06', lambda f: pathlib.Path(f).suffix == ".epub",
     lambda f, m, p: epub.EPubFile(f, mode=m, progress=p)),
    (0, 4, b'PK\x07\x08', lambda f: pathlib.Path(f).suffix == ".epub",
     lambda f, m, p: epub.EPubFile(f, mode=m, progress=p)),
    # --------------------------------- PDFs ----------------------------------
    (0, 4, b'%PDF', lambda f: True,
     lambda f, m, p: pdf.PdfFile(f, mode=m, progress=p)), # pdf
    # --------------------------------- RARs ----------------------------------
    (0, 7, b'Rar!\x1A\x07\x00', lambda f: True,
     lambda f, m, p: rar.RarFile(f, mode=m, progress=p)), # RAR[1-4]
    (0, 8, b'Rar!\x1A\x07\x01\x00', lambda f: True,
     lambda f, m, p: rar.RarFile(f, mode=m, progress=p)), # RAR5+
    # --------------------------------- 7zip ----------------------------------
    (0, 6, b'7z\xBC\xAF\x27\x1C', lambda f: True,
     lambda f, m, p: sevenzip.SevenZipFile(f, mode=m, progress=p)),
    # ------------------------------- Tarballs --------------------------------
    (257, 8, b'ustar\x00\x30\x30', lambda f: True,
     lambda f, m, p: tar.TarFile(f, mode=m, progress=p)), # Uncompressed
    (257, 8, b'ustar\x20\x20\x00', lambda f: True,
     lambda f, m, p: tar.TarFile(f, mode=m, progress=p)), # Uncompressed
    (0, 6, b'\xFD\x37\x7A\x58\x5A\x00',
     lambda f: pathlib.Path(f).suffix == ".cbt",
     lambda f, m, p: tar.TarFile(f, mode=f"{m}:xz", progress=p)), # xz (lzma) compressed
    (0, 2, b'\x1F\x8B', lambda f: pathlib.Path(f).suffix == ".cbt",
     lambda f, m, p: tar.TarFile(f, mode=f"{m}:gz", progress=p)), # gz, (GZip) compressed
    (0, 3, b'BZh', lambda f: pathlib.Path(f).suffix == ".cbt",
     lambda f, m, p: tar.TarFile(f, mode=f"{m}:bz2", progress=p)), # Bzip2 compressed
    # --------------------------------- Zip ---------------------------------
    (0, 4, b'PK\x03\x04', lambda f: True,
     lambda f, m, p: zip.ZipFile(f, mode=m, progress=p)),
    (0, 4, b'PK\x05\x06', lambda f: True,
     lambda f, m, p: zip.ZipFile(f, mode=m, progress=p)),
    (0, 4, b'PK\x07\x08', lambda f: True,
     lambda f, m, p: zip.ZipFile(f, mode=m, progress=p)),
)

# -----------------------------------------------------------------------------
# Private Magic Number Based Constructor Lambda Function
# -----------------------------------------------------------------------------
__CONSTRUCTOR = lambda f, m, p: list(
    _cll(f, m, p) for _off, _n, _mgk, _cnd, _cll in __CONSTRUCTORS if (
            pathlib.Path(f).read_bytes()[_off:_off+_n] == _mgk and _cnd(f)))[0]


# -----------------------------------------------------------------------------
# Public Module Methods
# -----------------------------------------------------------------------------
def open_data(file_in: typing.Union[str, pathlib.Path],
              mode_in: _modeT = _modes[0],
              progress_in = None) -> _archT:
    if isinstance(file_in, (str, pathlib.Path)):
        if isinstance(mode_in, str): #and mode_in is _modes:
            try:
                return __CONSTRUCTOR(file_in, mode_in, progress_in)
            except IndexError as _:
                raise ValueError(
                    f"Error: Unknown File Type: {file_in}")
        else:
            raise TypeError(
                f"Error: Invalid Mode: {mode_in}")
    else:
        raise TypeError(
            f"Error: Invalid File: {type(
                file_in).__name__}")


if __name__ == "__main__":
    files = [
        pathlib.Path(__file__).parent.parent /
        "test" / "AX3LBRAVO - Damsels in Distress.cbz",
        pathlib.Path(__file__).parent.parent /
        "test" / "Ay-Papi 1.cbr",
        pathlib.Path(__file__).parent.parent /
        "test" / "National Geographic 2010-06-01.cb7",
        pathlib.Path(__file__).parent.parent /
        "test" / "[1995] The Calvin and Hobbes Tenth Anniversary Book.cbt",
        pathlib.Path(__file__).parent.parent /
        "test" / "Masou Gakuen HxH vol.01.epub",
        pathlib.Path(__file__).parent.parent /
        "test" / "Space Visual Encyclopedia By DK.pdf",
    ]

    for file in files:
        arc = open_data(file)
        pass
