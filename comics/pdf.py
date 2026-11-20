#!/usr/bin/env python3
import sys, pathlib, typing, types, io, PIL.Image


if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.utils import packages, resolver
else:
    from ..utils import packages, resolver

packages.require({
    "pymupdf": ("pymupdf", "pymupdf")},
    __name__)


INFO_IMAGE = 0
INFO_TEXT = 1


def is_pdffile(path_in: pathlib.Path | str) -> bool:
    with open(path_in, "rb") as arc:
        try:
            magic = arc.read(5)
        finally:
            arc.close()

    # Check for PDF "%PDF-" magic number
    if magic == b"\x25\x50\x44\x46\x2D":
        return True
    else:
        return False


class PdfInfo:
    def __init__(self, info_in: pymupdf.Page):
        self.__info = {
            "info": info_in,
            "file": "",
            "data": b"",
            "type": -1,
            "object": None,
        }

        # Set the values.
        self.info = info_in

    @property
    def info(self) -> pymupdf.Page:
        return self.__info["info"]

    @info.setter
    def info(self, info_in: pymupdf.Page):
        if isinstance(info_in, pymupdf.Page):
            self.__info["info"] = info_in
            self.__info["file"] = f"page_{info_in.number:0>4}.png"
            self.__info["data"] = info_in.get_pixmap(
                matrix=pymupdf.Matrix(1.5, 1.5)).tobytes("ppm")
            self.__info["type"] = INFO_IMAGE
            self.__info["object"] = PIL.Image.open(
                io.BytesIO(self.data))
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
    def object(self) -> any:
        return self.__info["object"]

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


class PdfFile:
    def __init__(self, file_in: pathlib.Path | str, **args_in):
        self.__infos, self.__book, self.__file = (
            {}, None, None)
        self.__mode = args_in.pop("mode") if "mode" in args_in.keys() else "r"
        self.file = file_in

    @property
    def file(self) -> pathlib.Path:
        return self.__file

    @file.setter
    def file(self, file_in: str | pathlib.Path):
        self.__file, self.__book, self.__infos = file_in, None, []
        if isinstance(file_in, (str, pathlib.Path, types.NoneType)):
            self.__file = pathlib.Path(file_in)
            self.__book = pymupdf.open(f"{file_in}")
            if self.__file.exists():
                self.__infos = {i.filename: i for i in [PdfInfo(p) for p in self.__book.pages()]}

        elif isinstance(file_in, types.NoneType):
            pass
        else:
            raise ValueError(
                f"Invalid File: {type(file_in).__name__}")

    @property
    def title(self) -> str:
        try:
            return self.__book.metadata["title"]
        except KeyError as _:
            return ""

    @property
    def author(self) -> str:
        try:
            return self.__book.metadata["author"]
        except KeyError as _:
            return ""

    def extractall(self, path_in: pathlib.Path = None):
        path_in = path_in if path_in is not None else self.__file.parent / self.__file.stem
        path_in.mkdir(parents=True, exist_ok=True)
        for path, info in [(path_in / i.filename, i) for i in self.__infos.values()]:
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
        if isinstance(info_in.object, PIL.Image.Image):
            info_in.object.save(f"{file_in}")
        else:
            file_in.write_bytes(info_in.data)

    def namelist(self) -> list[str]:
        """Return a list of file names in the epub."""
        return list(self.__infos.keys())

    def infolist(self) -> list[PdfInfo]:
        """Return a list of EPubInfo objects for members of the epub."""
        return list(self.__infos.values())

    def infodict(self) -> dict:
        """Return a list of EPubInfo objects for members of the epub."""
        return self.__infos

    def getinfo(self, name_in: str) -> PdfInfo:
        """
        Return a EPubInfo object with information about the member name.
        :param name_in: The entry name in the epub
        :return: RPubInfo:
        """
        try:
            return self.__infos[name_in]
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
                "EPub opened in read mode")
        else:
            pass

        file_in = info_in.filename if isinstance(info_in, PdfInfo) else info_in

    @property
    def pages(self) -> list:
        return list((i.filename, i.object) for i in self.__infos.values())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __getitem__(self, index_in: int) -> PdfInfo:
        return self.infolist()[index_in]


if __name__ == '__main__':
    file = (pathlib.Path(__file__).parent.parent /
            "test" / "Space Visual Encyclopedia By DK.pdf")
    pdf = PdfFile(file)
    pdf.extractall(file.parent / file.stem)
    pass