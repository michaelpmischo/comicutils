import io, os, tarfile, time, zipfile, datetime, pathlib, typing, copy


class TarInfo(tarfile.TarInfo):

    """A TarInfo subclass that adapts and exposes the zipfile.ZipInfo API."""
    # --- Properties mapping ZipInfo attributes to TarInfo equivalents ---
    def __init__(self, info_in: tarfile.TarInfo):
        super().__init__()
        for k in info_in.__slots__.keys():
            try:
                setattr(self, k, getattr(info_in, k))
            except AttributeError as _:
                try:
                    setattr(self, k, getattr(info_in, k.strip("_")))
                except AttributeError as _:
                    pass

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


class TarFile:
    """Wraps a tarfile to expose a read-only zipfile.ZipFile interface."""

    def __init__(self, file_in: typing.Union[str, bytes, os.PathLike, io.BytesIO], mode: str = 'r', **kwargs):
        # file_in = f"{file_in}" if isinstance(file_in, pathlib.Path) else file_in
        self.__tar = tarfile.open(file_in, mode=mode, **kwargs)

    def namelist(self) -> typing.List[str]:
        """Return a list of archive members by name."""
        return self.__tar.getnames()

    def infolist(self) -> typing.List[TarInfo]:
        """Return a list of ZipInfo objects for all archive members."""
        return [TarInfo(m) for m in self.__tar.getmembers()]

    def getinfo(self, name_in: str) -> TarInfo:
        """Return a ZipInfo object for a specific member."""
        return TarInfo(self.__tar.getmember(f"{name_in}"))

    def read(self, name: str) -> bytes:
        """Return the bytes of the specified file in the archive."""
        with self.open(name, "r") as f:
            try:
                return f.read()
            finally:
                f.close()

    def write(self, filename: str, arcname: str = None, compress_type: any = None, compresslevel: any = None) -> None:
        self.__tar.add(
            name=filename,
            arcname=(filename if arcname is None else arcname).replace(
                os.sep, '/'))

    def writestr(self, info_in: typing.Union[str, TarInfo], data_in: typing.Union[str, bytes],
                 compress_type: any = None, compresslevel: any = None) -> None:
        data_in = io.BytesIO(
            data_in.encode('utf-8') if isinstance(data_in, str) else data_in)
        if not isinstance(info_in, TarInfo):
            info_in = TarInfo(tarfile.TarInfo(
                name=f"{info_in}".replace(os.sep, '/')))
            info_in.mtime = time.time()
            info_in.mode = 0o644
            info_in.type = tarfile.REGTYPE
        info_in.size = len(data_in)

        # Wrap raw bytes in a stream buffer and write to the tar file
        self.__tar.addfile(tarinfo=info_in, fileobj=data_in)

    def open(self, info_in: typing.Union[str, TarInfo],
             mode: str = 'r', pwd: typing.Optional[bytes] = None):
        """Access a member as a binary file-like object."""
        if mode not in ('r', 'rb'):
            raise ValueError(
                "TarFile.open() only supports "
                "read modes ('r' or 'rb')")
        if not isinstance(info_in, TarInfo):
            info_in = self.__tar.getmember(info_in)
        if not info_in.isreg():
            return io.BytesIO()
        else:
            return self.__tar.extractfile(info_in)

    def extract(self, info_in: typing.Union[str, TarInfo, tarfile.TarInfo], path_in: typing.Optional[str] = None,
                pwd: typing.Optional[bytes] = None) -> str:
        """Extract a single member from the archive to the current working directory or specified path."""
        if not isinstance(info_in, (TarInfo, tarfile.TarInfo)):
            info_in = self.__tar.getmember(info_in)
        self.__tar.extract(info_in, path=f"{path_in}", filer='data')
        return os.path.join(path or '.', name)

    def extractall(self, path_in: typing.Optional[typing.Union[str, pathlib.Path]] = None,
                   members_in: typing.Optional[typing.List[str]] = None,
                   pwd_in: typing.Optional[bytes] = None):
        """Extract all members from the archive."""
        self.__tar.extractall(path=f"{path_in}", members=[
            self.__tar.getmember(m) for m in members_in] if (
                members_in is not None) else None,
            filter='data')

    @property
    def pages(self) -> list:
        return list((i.filename, PIL.Image.open(
            io.BytesIO(self.open(i).read()))) for i in self.infolist() if (
                pathlib.Path(i.filename).suffix in
                PIL.Image.registered_extensions()))

    def close(self):
        self.__tar.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    file = (pathlib.Path(__file__).parent.parent /
            "test" / "[1995] The Calvin and Hobbes Tenth Anniversary Book.cbt")
    tarball = TarFile(file, mode='r')

    infos = tarball.infolist()


    tarball.extractall(pathlib.Path(__file__).parent)