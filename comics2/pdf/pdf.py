#!/usr/bin/env python3
import sys, pathlib, typing, types, io, PIL.Image
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.utils import packages, attributes
else:
    from ...utils import packages, attributes
packages.require({
    "pymupdf": ("pymupdf", "pymupdf")},
    __name__)
# <<< --------------------------- ENG IMPORTS ---------------------------- >>>


# -----------------------------------------------------------------------------
# Magic Numbers
# -----------------------------------------------------------------------------
MAGICS = ((0, 4, b'%PDF', ""),)
MAGIC = lambda f: tuple(cmp for off, n, magic, cmp in MAGICS if (
    pathlib.Path(f).read_bytes()[off:off+n] == magic))


def is_pdffile(path_in: pathlib.Path | str) -> bool:
    return bool(MAGIC(path_in))


# -----------------------------------------------------------------------------
# PdfInfo
# -----------------------------------------------------------------------------
class PdfInfo(pymupdf.Page):
    def __init__(self, info_in: pymupdf.Page):
        if isinstance(info_in, pymupdf.Page):
            super().__init__(page=info_in.this, document=info_in.parent)
            self.__info = {
                "info": info_in,
                "file": "",
                "data": b"",
                "type": -1,
            }

            # Set the values.
            self.info = info_in
        else:
            raise TypeError(
                f"Invalid Info: {type(
                    info_in).__name__}")

    @property
    def info(self) -> pymupdf.Page:
        return self.__info["info"]

    @info.setter
    def info(self, info_in: pymupdf.Page):
        if isinstance(info_in, pymupdf.Page):
            self.__info["info"] = info_in
            self.__info["file"] = f"page_{info_in.number:0>4}.png"
            self.__info["data"] = info_in.get_pixmap(
                matrix=pymupdf.Matrix(1.5, 1.5)).tobytes("png")
            self.__info["type"] = 0
        else:
            raise ValueError(
                f"Invalid Item: {type(info_in).__name__}")

    @property
    def filename(self) -> str:
        return self.__info["file"]

    @property
    def data(self) -> bytes:
        return self.__info["data"]

    @property
    def type(self) -> int:
        return self.__info["type"]

    @property
    def text(self) -> str:
        return self.__info["data"].decode("utf-8")

    @property
    def file_size(self) -> int:
        return len(self.data)

    @property
    def compress_size(self) -> int:
        return self.file_size

    @property
    def CRC(self):
        return zlib.crc32(self.__info["data"])

    def is_dir(self) -> bool:
        return False

    def is_file(self) -> bool:
        return True

    def read(self) -> bytes:
        return self.data


# -----------------------------------------------------------------------------
# PdfFile
# -----------------------------------------------------------------------------
class PdfFile(pymupdf.Document):
    def __init__(self, file_in: pathlib.Path | str, **args_in):
        progress = args_in.pop("progress") if "progress" in args_in.keys() else None
        if isinstance(file_in, (str, pathlib.Path, types.NoneType)):
            self.__pages, self.__mode = (
                {}, args_in.pop("mode") if (
                    "mode" in args_in.keys()) else "r")
            file_in = pathlib.Path(file_in) if file_in is not None else file_in
            if file_in is not None and file_in.exists():
                super().__init__(file_in, **args_in)
            else:
                super().__init__(**args_in)
        else:
            raise TypeError(
                f"Invalid File: {type(file_in).__name__}")
        self.__pages = {i.filename: i for i in [
            PdfInfo(p) for p in super().pages()]}
    @property
    def file(self) -> pathlib.Path:
        return self.name

    @property
    def title(self) -> str:
        try:
            return self.metadata["title"]
        except KeyError as _:
            return ""

    @property
    def author(self) -> str:
        try:
            return self.metadata["author"]
        except KeyError as _:
            return ""

    @property
    def pages(self) -> typing.Iterator[PdfInfo]:
        return iter(self.__pages.values())

    def extractall(self, path_in: pathlib.Path = None):
        path_in = path_in if path_in is not None else self.__file.parent / self.__file.stem
        path_in.mkdir(parents=True, exist_ok=True)
        for path, info in [(path_in / i.filename, i) for i in self.__pages.values()]:
            print(f"Extracting: {path_in / path}...")
            self.save(info, path)

    def open(self, info_in: str | PdfInfo):
        if isinstance(info_in, PdfInfo):
            return io.BytesIO(
                info_in.data)
        elif isinstance(info_in, (str | pathlib.Path)):
            try:
                return io.BytesIO(
                    self.getifo(imfo_in).data)
            except AttributeError as _:
                raise FileNotFoundError(
                    f"Failed To File: {info_in}")
        else:
            raise ValueError(
                f"Invalid Info: {type(info_in).__name__}")

    def save(self, info_in: PdfInfo, file_in: pathlib.Path):
        file_in.parent.mkdir(parents=True, exist_ok=True)
        file_in.write_bytes(info_in.data)

    def namelist(self) -> list[str]:
        """Return a list of file names in the epub."""
        return list(self.__pages.keys())

    def infolist(self) -> list[PdfInfo]:
        """Return a list of PdfInfo objects for members of the epub."""
        return list(self.__pages.values())

    def infodict(self) -> dict:
        """Return a list of PdfInfo objects for members of the epub."""
        return self.__pages

    def getinfo(self, name_in: str) -> PdfInfo:
        """
        Return a PdfInfo object with information about the member name.
        :param name_in: The entry name in the epub
        :return: RPubInfo:
        """
        try:
            return self.__pages[name_in]
        except KeyError as _:
            return None

    def writestr(self, info_in: str | PdfInfo, data_in: bytes):
        """
        Write a file into the archive from a string or bytes payload.
        Mimics zipfile.ZipFile.writestr()

        :param info_in:
        :param data_in:
        :return:
        """
        if self.__mode != 'w':
            raise RuntimeError(
                "Pdf opened in read mode")
        else:
            pass

        file_in = info_in.filename if isinstance(info_in, PdfInfo) else info_in

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __iter__(self) -> typing.Iterator[PdfInfo]:
        return iter(self.__pages.values())
    @typing.override
    def __getitem__(self, key_in: typing.Union[str, int]) -> PdfInfo:
        if isinstance(index_in, (str, int)):
            if isinstance(key_in, int):
                key_in = list(self.pages.keys())[key_in]
            return self.__pages[key_in]
        else:
            raise TypeError(
                f"Invalid Key or Index: {type(
                    key_in).__name__}")

    @typing.override
    def __setitem__(self, key_in: typing.Union[str, int], info_in: PdfInfo):
        if isinstance(info_in, PdfInfo):
            if isinstance(key_in, int):
                index, key_in = key_in, list(self.pages.keys())[key_in]
                self.__pages[key_in] = info_in
                super()[index] = info_in
            elif isinstance(key_in, str):
                index = list(self.pages.keys()).index(key_in)
                self.__pages[key_in] = info_in
                super()[index] = info_in
            else:
                raise TypeError(
                    f"Invalid Key or Index: {type(
                        key_in).__name__}")
        else:
            raise TypeError(
                f"Invalid Info: {type(
                    info_in).__name__}")

    @typing.override
    def __delitem__(self, key_in: typing.Union[str, int]):
        if isinstance(info_in, PdfInfo):
            if isinstance(key_in, int):
                index, key_in = key_in, list(self.__pages.keys())[key_in]
                del self.__pages[key_in]
                del super()[index]
            elif isinstance(key_in, str):
                index = list(self.__pages.keys()).index(key_in)
                del self.__pages[key_in]
                del super()[index]
            else:
                raise TypeError(
                    f"Invalid Key or Index: {type(
                        key_in).__name__}")
        else:
            raise TypeError(
                f"Invalid Info: {type(
                    info_in).__name__}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} object at {hex(id(self))}>"


if __name__ == '__main__':
    file = (pathlib.Path(__file__).parent.parent /
            "test" / "Space Visual Encyclopedia By DK.pdf")
    pdf = PdfFile(file)
    pdf.extractall(file.parent / file.stem)
    pass