#!/usr/bin/env python3
import sys, pathlib, io, os, typing, datetime
from py7zr import Bad7zFile
__all__ = ["Bad7zFile"]
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent.parent}")
    from comicutils.utils import packages, attributes
else:
    from ...utils import packages, attributes
# install/import required packages
packages.require({
    "py7zr": ("py7zr", "py7zr")},
    __name__)
# <<< --------------------------- ENG IMPORTS ---------------------------- >>>


# -----------------------------------------------------------------------------
# Magic Numbers
# -----------------------------------------------------------------------------
MAGICS = ((0, 6, b'7z\xBC\xAF\x27\x1C', "7z"),)
MAGIC = lambda f: tuple(cmp for off, n, magic, cmp in MAGICS if (
    pathlib.Path(f).read_bytes()[off:off+n] == magic))


def is_7zfile(path_in: pathlib.Path | str) -> bool:
    return bool(MAGIC(path_in))


# -----------------------------------------------------------------------------
# 7zip Filters
# -----------------------------------------------------------------------------
FILTER_LZMA2_DELTA = [{'id': py7zr.FILTER_DELTA}, {'id': py7zr.FILTER_LZMA2, 'preset': py7zr.PRESET_DEFAULT}]
FILTER_LZMA2_BCJ = [{'id': py7zr.FILTER_X86}, {'id': py7zr.FILTER_LZMA2, 'preset': py7zr.PRESET_DEFAULT}]
FILTER_LZMA2_ARM = [{'id': py7zr.FILTER_ARM}, {'id': py7zr.FILTER_LZMA2, 'preset': py7zr.PRESET_DEFAULT}]
FILTER_LZMA_BCJ = [{'id': py7zr.FILTER_X86}, {'id': py7zr.FILTER_LZMA}]
FILTER_LZMA2 = [{'id': py7zr.FILTER_LZMA2, 'preset': py7zr.PRESET_DEFAULT}]
FILTER_LZMA = [{'id': py7zr.FILTER_LZMA}]
FILTER_BZIP2 = [{'id': py7zr.FILTER_BZIP2}]
FILTER_DEFLATE = [{'id': py7zr.FILTER_DEFLATE}]
FILTER_ZSTD = [{'id': py7zr.FILTER_ZSTD, 'level': 3}]
FILTER_PPMD_24 = [{'id': py7zr.FILTER_PPMD, 'order': 6, 'mem': 24}]
FILTER_PPMD_16M = [{'id': py7zr.FILTER_PPMD, 'order': 6, 'mem': "16m"}]
FILTER_BROLTI = [{'id': py7zr.FILTER_BROTLI, 'level': 11}]
FILTER_AES256 = [{'id': py7zr.FILTER_CRYPTO_AES256_SHA256}]


# -----------------------------------------------------------------------------
# SevenZipFileIO (io.BytesIO for 7zip files)
# -----------------------------------------------------------------------------
class SevenZipFileIO(py7zr.io.Py7zIO):
    """Memory buffer receiver mimicking a file stream for a single file."""
    def __init__(self):
        self._buffer = io.BytesIO()

    def write(self, data):
        return self._buffer.write(data)

    def seek(self, offset, whence=0):
        return self._buffer.seek(offset, whence)

    def read(self, size=-1):
        return self._buffer.read(size)

    def getvalue(self):
        return self._buffer.getvalue()

    def flush(self):
        self._buffer.flush()

    def size(self) -> int:
        current = self._buffer.tell()
        self._buffer.seek(0, os.SEEK_END)
        size = self._buffer.tell()
        self._buffer.seek(current, os.SEEK_SET)
        return size


# -----------------------------------------------------------------------------
# SevenZipFileMemoryFactory (Dynamic Stream Factory for 7zip files)
# -----------------------------------------------------------------------------
class SevenZipFileMemoryFactory(py7zr.WriterFactory):
    """Factory that redirects a specific file extraction targeted to RAM."""
    def __init__(self, file_in: str):
        self.__file = file_in
        self.__stream = None

    def create(self, filename: str):
        # Only create a memory stream for the file we asked to open
        if filename == self.__file:
            self.__stream = SevenZipFileIO()
            return self.__stream
        # Ignore other files (py7zr skips writing them)
        return None

    @property
    def stream(self):
        self.__stream.seek(0)
        return self.__stream


# -----------------------------------------------------------------------------
# SevenZipInfo (7zip equivalent to zipfile.ZipInfo class)
# -----------------------------------------------------------------------------
class SevenZipInfo(py7zr.FileInfo):
    """Proxies py7zr.FileInfo properties to match zipfile.ZipInfo attributes."""

    def __init__(self, info_in: py7zr.FileInfo):
        self.__file = info_in.filename
        super().__init__(
            filename=info_in.filename, compressed=info_in.compressed,
            uncompressed=info_in.uncompressed, archivable=info_in.archivable,
            is_file=info_in.is_file, is_directory=info_in.is_directory,
            is_symlink=info_in.is_symlink, creationtime=None,
            crc32=info_in.crc32,)
        if isinstance(info_in, py7zr.FileInfo):
            attributes.copy_parent(self, info_in)
        else:
            raise TypeError(
                f"Invalid Info: Expected py7zr.FileInfo, got {type(
                    info_in).__name__}")

    @property
    def filename(self) -> str:
        return self.__file

    @filename.setter
    def filename(self, file_in: str):
        self.__file = file_in

    @property
    def file_size(self) -> int:
        return super().uncompressed

    @property
    def compress_size(self) -> int:
        return super().compressed

    def is_dir(self) -> bool:
        return super().is_directory

    def is_file(self) -> bool:
        return super().is_file

    @property
    def CRC(self):
        return super().crc32


# -----------------------------------------------------------------------------
# SevenZipFile (py7zr wrapper for zipfile.ZipFile API) + [pages, infodict] methods
# -----------------------------------------------------------------------------
class SevenZipFile(py7zr.SevenZipFile):
    def __init__(self, file_in: pathlib.Path, **args_in):
        progress = args_in.pop("progress") if "progress" in args_in.keys() else None
        self.__file, self.__mode = file_in, args_in.pop("mode") if (
                "mode" in args_in.keys()) else "r"
        if "compression" in args_in.keys():
            args_in["filters"] = args_in.pop("compression")
        super().__init__(self.__file, mode=self.__mode, **args_in)

    @property
    def file(self) -> pathlib.Path:
        return self.filename

    def read(self, name_in: typing.Union[str, pathlib.Path, SevenZipInfo]) -> bytes:
        """
        Return the bytes of the specified file in the archive.
        """
        with self.open(name_in) as f:
            try:
                return f.read()
            finally:
                f.close()

    def getinfo(self, name_in: str) -> SevenZipInfo:
        """Return a SevenZipInfoProxy object with information about the member name."""
        return SevenZipInfo(super().getinfo(name_in))

    def infolist(self) -> typing.List[SevenZipInfo]:
        """Return a list of SevenZipInfo objects for members of the archive."""
        return [SevenZipInfo(i) for i in super().list()]

    def dictlist(self) -> dict:
        """Return a dict of SevenZipInfo objects for members of the archive."""
        return {i.filename: i for i in self.infolist()}

    def open(self, file_in: typing.Union[str, pathlib.Path, SevenZipInfo]):
        file_in = pathlib.Path(
            file_in.filename if isinstance(
                file_in, SevenZipInfo) else file_in)
        factory = SevenZipFileMemoryFactory(f"{file_in}")
        super().extract(targets=[f"{file_in}"], factory=factory)
        if factory.stream is None:
            raise IOError(f"Failed to read: {file_in}")
        else:
            return factory.stream

    def extract(self, file_in: typing.Union[str, pathlib.Path, SevenZipInfo],
                path_in: typing.Union[str, pathlib.Path], **kwargs_in):
        file_in = pathlib.Path(file_in.filename if isinstance(file_in, SevenSipInfo) else file_in)
        path_in = pathlib.Path(path_in if path_in is not None else pathlib.Path.cwd())
        super().extract(path=f"{path_in}", targets=file_in, **kwargs_in)

    def extractall(self, path_in: typing.Union[str, pathlib.Path, SevenZipInfo] = None,
                   members_in: typing.List[typing.Union[str, pathlib.Path]] = None,
                   **kwargs_in):
        path_in = pathlib.Path(path_in if path_in is not None else pathlib.Path.cwd())
        super().extractall(path=path_in, **kwargs_in)

    def writestr(self, file_in: typing.Union[str, pathlib.Path, SevenZipInfo],
                 data_in: typing.Union[str, bytes]):
        """
         Write a file into the archive from a string or bytes payload.
        Mimics zipfile.ZipFile.writestr()

        :param file_in:
        :param data_in:
        :return:
        """
        if self.__mode != 'w':
            raise RuntimeError(
                "Archive opened in read mode")
        file_in = pathlib.Path(file_in.filename if isinstance(
            file_in, SevenZipInfo) else file_in)
        data_in = data_in.encode("utf-8") if isinstance(data, str) else (
            bytes(data_in) if isinstance(data, (bytes, bytearray)) else None)
        if data_in is None:
            raise TypeError(
                "Data must be a str, bytes, or bytearray payload.")
        super().writef(io.BytesIO(data_in), arcname=file_in)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
