import io, os, tarfile, time, datetime, pathlib, typing
if __name__ == '__main__':
    import sys, pathlib
    sys.path.append(f"{pathlib.Path(__file__).parent.parent.parent.parent}")
    from comicutils.utils import attributes
else:
    from ...utils import attributes

# <<< --------------------------- ENG IMPORTS ---------------------------- >>>


# -----------------------------------------------------------------------------
# Magic Numbers
# -----------------------------------------------------------------------------
MAGICS = ((257, 8, b'ustar\x00\x30\x30', "tar"), (257, 8, b'ustar\x20\x20\x00', "tar"), # Uncompressed
          (0, 6, b'\xFD\x37\x7A\x58\x5A\x00', "xz"), # xz (lzma) compressed
          (0, 2, b'\x1F\x8B', "gz"), # gz, (GZip) compressed
          (0, 3, b'BZh', "bz2")) # bz2 (BZip2) compressed
MAGIC = lambda f: tuple(cmp for off, n, magic, cmp in MAGICS if (
    pathlib.Path(f).read_bytes()[off:off+n] == magic))


def is_tarfile(path_in: pathlib.Path | str) -> bool:
    return bool(MAGIC(path_in))


# -----------------------------------------------------------------------------
# TarInfo
# -----------------------------------------------------------------------------
class TarInfo(tarfile.TarInfo):
    """A TarInfo subclass that adapts and exposes the zipfile.ZipInfo API."""

    # --- Properties mapping ZipInfo attributes to TarInfo equivalents ---
    def __init__(self, info_in: tarfile.TarInfo):
        super().__init__()
        attributes.copy_parent(self, info_in)

    @property
    def filename(self) -> str:
        """Name of the file in the archive."""
        return self.name

    @filename.setter
    def filename(self, file_in: typing.Union[str | pathlib.Path]):
        self.name = f"{file_in}"

    @property
    def file_size(self) -> int:
        """Size of the uncompressed file in bytes."""
        return self.size

    @file_size.setter
    def file_size(self, value: int):
        self.size = value

    @property
    def compress_size(self) -> int:
        """Size of the compressed data (TarInfo does not compress individually, matches size)."""
        return self.size

    @compress_size.setter
    def compress_size(self, value: int):
        pass  # No-op since tar doesn't support per-file compression sizes

    @property
    def date_time(self) -> tuple[int, int, int, int, int, int]:
        """Return the modification time as a ZipInfo-style tuple:
        (year, month, day, hour, minute, second)
        """
        # tarfile stores mtime as a float point timestamp
        dt = datetime.fromtimestamp(self.mtime)
        return dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second

    @date_time.setter
    def date_time(self, time_in: typing.Union[
        typing.Tuple[int, int, int, int, int, int], datetime.datetime, float]):
        """Set modification time using a ZipInfo-style tuple."""
        self.mtime = time_in if isinstance(time_in, float) else (
            datetime.datetime(*time_in).timestamp()) if (
                isinstance(time_in, tuple)) else (
                    time_in.timestamp())

    def is_dir(self) -> bool:
        """Return True if the archive member is a directory."""
        return self.isdir()

    @property
    def CRC(self) -> int:
        """CRC-32 checksum (Not natively tracked by TarInfo; returns a dummy 0)."""
        return 0

    @property
    def compress_type(self) -> int:
        """Compression type (Returns 0 for ZIP_STORED / uncompressed)."""
        return 0

    @property
    def external_attr(self) -> int:
        """Construct a UNIX-compatible external attribute mask from the tar mode."""
        return (self.mode & 0xFFFF) << 16

    @external_attr.setter
    def external_attr(self, value: int):
        self.mode = (value >> 16) & 0xFFFF


# -----------------------------------------------------------------------------
# TarFile
# -----------------------------------------------------------------------------
class TarFile(tarfile.TarFile):
    """
    Wraps a tarfile to expose a read-only zipfile.ZipFile interface.
    """

    def __init__(self, file_in: typing.Union[str, pathlib.Path], **args_in):
        progress = args_in.pop("progress") if "progress" in args_in.keys() else None
        if isinstance(file_in, (str, pathlib.Path)):
            super().__init__(f"{file_in}", **args_in)
        else:
            raise TypeError(
                f"Invalid file type: {type(
                    file_in)}")

    def namelist(self) -> typing.List[str]:
        """
        Return a list of archive members by name.
        """
        return self.getnames()

    def infolist(self) -> typing.List[TarInfo]:
        """
        Return a list of ZipInfo objects for all archive members.
        """
        return [TarInfo(m) for m in self.getmembers()]

    def getinfo(self, name_in: str) -> TarInfo:
        """
        Return a ZipInfo object for a specific member.
        """
        return TarInfo(self.getmember(f"{name_in}"))

    def read(self, name: str) -> bytes:
        """
        Return the bytes of the specified file in the archive.
        """
        with self.open(name, "r") as f:
            try:
                return f.read()
            finally:
                f.close()

    def write(self, file_in: typing.Union[str, pathlib.Path],
              arcname_in: typing.Union[str, pathlib.Path] = None,
              **kwargs_in) -> None:
        archname_in = pathlib.PurePosixPath(file_in if arcname_in is None else arcname_in)
        self.add(name=file_in, arcname=archname_in, **kwargs_in)

    def writestr(self, info_in: typing.Union[str, TarInfo],
                 data_in: typing.Union[str, bytes], **kwargs_in) -> None:
        data_in = io.BytesIO(data_in.encode('utf-8') if (
            isinstance(data_in, str)) else data_in)
        if not isinstance(info_in, TarInfo):
            info_in = TarInfo(tarfile.TarInfo(
                name=f"{info_in}".replace(os.sep, '/')))
            info_in.mtime = time.time()
            info_in.mode = 0o644
            info_in.type = tarfile.REGTYPE
        info_in.size = len(data_in)

        # Wrap raw bytes in a stream buffer and write to the tar file
        self.addfile(tarinfo=info_in, fileobj=data_in)

    def open(self, info_in: typing.Union[str, TarInfo],
             mode_in: str = 'r', **kwargs_in) -> typing.Union[typing.IO[bytes]]:
        """Access a member as a binary file-like object."""
        if mode not in ('r', 'rb'):
            raise ValueError(
                "TarFile.open() only supports "
                "read modes ('r' or 'rb')")
        if not isinstance(info_in, TarInfo):
            info_in = self.getmember(info_in)
        if not info_in.isreg():
            return io.BytesIO()
        else:
            return io.BytesIO(self.extractfile(info_in).read())

    def extractall(self, path_in: typing.Optional[typing.Union[str, pathlib.Path]] = None,
                   **kwargs_in):
        """
        Extract all members from the archive.
        """
        path_in = pathlib.Path(path_in) if path_in is not None else pathlib.Path.cwd()
        if path_in.is_file():
            path_in = pathlib.Path(path_in).parent
        path_in.mkdir(parents=True, exist_ok=True)
        super().extractall(path=f"{path_in}")

    def extract(self, info_in: typing.Union[str, TarInfo, tarfile.TarInfo],
                path_in: typing.Optional[str] = None, **kwargs_in) -> str:
        """
        Extract a single member from the archive to the current working
        directory or specified path.
        """
        path_in = pathlib.Path(path_in) if path_in is not None else pathlib.Path.cwd()
        if not isinstance(info_in, (TarInfo, tarfile.TarInfo)):
            info_in = self.getmember(info_in)
        if path_in.is_file():
            path_in = path_in.parent
        super().extract(info_in, path=f"{path_in}", **kwargs)
        return pathlib.Path(path_in, info_in.filename).resolve()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    file = (pathlib.Path(__file__).parent.parent.parent /
            "test" / "[1995] The Calvin and Hobbes Tenth Anniversary Book.cbt")
    cmp = MAGIC(file)
    if cmp:
        tarball = TarFile(file, mode='r')
        infos = tarball.infolist()
        tarball.extractall(
            pathlib.Path(__file__).parent / file.stem)
    else:
        bytes = pathlib.Path(file).read_bytes()[257:6]
        pass
