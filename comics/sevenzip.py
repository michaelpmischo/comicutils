#!/usr/bin/env python3
import sys, pathlib, io, os, PIL.Image
# For testing..
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.utils import packages
else:
    from ..utils import packages
# install/import required packages
packages.require({
    "py7zr": ("py7zr", "py7zr")},
    __name__)


# -----------------------------------------------------------------------------
# Module Constants
# -----------------------------------------------------------------------------
ZIP_LZMA2 = [{"id": py7zr.FILTER_LZMA2, "preset": 9}]


# -----------------------------------------------------------------------------
# Module Methods
# -----------------------------------------------------------------------------
def is_7zfile(path_in: pathlib.Path | str) -> bool:
    with open(path_in, "rb") as arc:
        try:
            magic = arc.read(8)
        finally:
            arc.close()

    # Check for RAR 5+ (8 bytes)
    if magic == b"7z":
        return True
    else:
        return py7zr.is_7zfile(path_un)


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
class SevenZipInfo():
    """Proxies py7zr.FileInfo properties to match zipfile.ZipInfo attributes."""

    def __init__(self, info_in: py7zr.FileInfo | dict):
        self.__info = info_in

    @property
    def filename(self) -> str:
        return self.__info.filename

    @property
    def file_size(self) -> int:
        return self.__info.uncompressed

    @property
    def compress_size(self) -> int:
        return self.__info.compressed

    def is_dir(self) -> bool:
        return self.__info.is_directory

    def is_file(self) -> bool:
        return self.__info.is_file

    @property
    def CRC(self):
        return self.__info.crc32


# -----------------------------------------------------------------------------
# SevenZipFile (py7zr wrapper for zipfile.ZipFile API) + [pages, infodict] methods
# -----------------------------------------------------------------------------
class SevenZipFile(py7zr.SevenZipFile):
    def __init__(self, file_in: pathlib.Path, **args_in):
        if "compression" in args_in.keys():
            args_in["filters"] = args_in.pop("compression")
        self.__mode = args_in.pop("mode") if "mode" in args_in.keys() else "r"
        self.__file = file_in
        super().__init__(self.__file, mode=self.__mode, **args_in)

    def open(self, file_in: str | SevenZipInfo):
        file_in = file_in.filename if isinstance(file_in, SevenZipInfo) else file_in
        factory = SevenZipFileMemoryFactory(file_in)
        super().extract(targets=[file_in], factory=factory)
        if factory.stream is None:
            raise IOError(
                f"Failed to read stream metadata payload for {file_in}")
        return factory.stream

    def namelist(self) -> list[str]:
        """Return a list of file names in the archive."""
        return super().getnames()

    def infolist(self) -> list[SevenZipInfo]:
        """Return a list of SevenZipInfo objects for members of the archive."""
        return [SevenZipInfo(i) for i in super().list()]

    def dictlist(self) -> dict:
        """Return a dict of SevenZipInfo objects for members of the archive."""
        return {i.filename: i for i in self.infolist()}

    def getinfo(self, name_in: str) -> SevenZipInfo:
        """Return a SevenZipInfoProxy object with information about the member name."""
        return SevenZipInfo(super().getinfo(name_in)[name_in])

    def writestr(self, file_in: str | SevenZipInfo, data_in: bytes):
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

        file_in = file_in.filename if isinstance(file_in, SevenZipInfo) else file_in
        data_in = data_in.encode("utf-8") if isinstance(data, str) else (
            bytes(data_in) if isinstance(data, (bytes, bytearray)) else None)
        if data_in is None:
            raise TypeError(
                "Data matching must be a str, bytes, or bytearray payload.")

        with io.BytesIO(data_in) as stream:
            self.writef(stream, arcname=file_in)

    @property
    def pages(self) -> list:
        return list((i.filename, PIL.Image.open(
            io.BytesIO(self.open(i).read()))) for i in self.infolist() if (
                pathlib.Path(i.filename).suffix in
                PIL.Image.registered_extensions()))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getitem__(self, index_in: int) -> SevenZipInfo:
        return self.infolist()[index_in]

