#!/usr/bin/env python3
import sys, pathlib, io, re, zlib, typing, types, tempfile, collections
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.comics import zip, rar, sevenzip, tarball, epub, pdf
    from comicutils.utils import packages, resolver
else:
    from . import zip, rar, sevenzip, tarball, epub, pdf
    from ..utils import packages, resolver
packages.require({
    # "bs4": ("bs4", "beautifulsoup4"),
    "PIL": ("PIL", "pillow"),
    "PIL.Image": ("PIL.Image", "pillow"),
    "PIL.ImageTk": ("PIL.ImageTk", "pillow"),
    "PIL.ImageOps": ("PIL.ImageOps", "pillow"),
    "tkextrafont": ("tkextrafont", "tkextrafont"),
    "av": ("av", "av")},
    __name__)

__all__ = [
    "UNKNOWN", "IMAGE", "TEXT", "VIDEO", "AUDIO", "FONT", "HTML", "XML", "CSS"]

UNKNOWN, IMAGE, VIDEO, AUDIO, TEXT, FONT, HTML, XML, CSS = (
    "UNKNOWN", "IMAGE", "AUDIO", "VIDEO", "TEXT", "FONT", "HTML", "XML", "CSS")

# Types Used in this module.
_itemT = typing.Union[zip.ZipInfo, rar.RarInfo, sevenzip.SevenZipInfo, tarball.TarInfo, epub.EPubInfo, pdf.PdfInfo]
_dataT = typing.Union[zip.ZipFile, rar.RarFile, sevenzip.SevenZipFile, tarball.TarFile, epub.EPubFile, pdf.PdfFile]
_imgT = typing.Union[PIL.Image, PIL.ImageTk.PhotoImage]
_typeT = typing.Literal[UNKNOWN, IMAGE, VIDEO, AUDIO, TEXT, FONT, HTML, XML, CSS]

_TYPE_EXT = {
    IMAGE: tuple(PIL.Image.registered_extensions().keys()),
    AUDIO: tuple(sorted({f".{e}" for v in av.formats_available for f in [
        av.format.ContainerFormat(v)] if f.extensions for e in f.extensions if any(
        x in v or x in f.long_name.lower() for x in [
            'audio', 'sound', 'music', 'pcm', 'wav', 'mp3', 'flac', 'ogg', 'aiff'])})),
    VIDEO: tuple(sorted({f".{e}" for v in av.formats_available for f in [
        av.format.ContainerFormat(v)] if f.extensions for e in f.extensions if any(
        x in v or x in f.long_name.lower() for x in [
            'video', 'movie', 'mp4', 'mkv', 'avi', 'h264', 'hevc', 'webm'])})),
    TEXT: (".txt",),
    FONT: ('.ttf', '.otf', '.ttc', '.fon', '.fnt') if (
        sys.platform.startswith('win')) else (
        ('.ttf', '.otf', '.ttc') if (
            sys.platform.startswith('linux')) else ()),
    HTML: (".html", ".xhtml", ".mhtml",),
    XML: (".xml",),
    CSS: (".css",),
}


# -----------------------------------------------------------------------------
# BookItem
# -----------------------------------------------------------------------------
class BookItem:
    _BROKEN = resolver.icon_root() / "broken.png"

    def __init__(self, info_in: _itemT, archive_in: _dataT):
        self.__FMTS, self.__TYPE2CREATOR = {
            zip.ZipInfo: self.__handle_zipinfo,
            rar.RarInfo: self.__handle_rarinfo,
            sevenzip.SevenZipInfo: self.__handle_7zinfo,
            tarball.TarInfo: self.__handle_tarinfo,
            epub.EPubInfo: self.__handle_epubinfo,
            pdf.PdfInfo: self.__handle_pdfinfo,
        }, {
            UNKNOWN: self.__handle_unknown,
            IMAGE: self.__create_image,
            AUDIO: self.__create_audio,
            VIDEO: self.__create_video,
            TEXT: self.__create_text,
            FONT: self.__create_font,
            HTML: self.__create_html,
            XML: self.__create_xml,
            CSS: self.__create_css,
        }
        if isinstance(info_in, _itemT):
            self.__archive = archive_in
            self.__info = {
                "info": info_in,
                "name": "BookItem",
                "file": "",
                "path": pathlib.Path.cwd(),
                "data": b"",
                "type": UNKNOWN,
                "object": None,
            }

            # Set the values.
            self.info = info_in
        else:
            raise ValueError(
                f"Invalid Page Info: {type(info_in).__name__}")

    @property
    def info(self) -> _itemT:
        return self.__info["info"]

    @info.setter
    def info(self, info_in: _itemT):
        for _T, _cll in self.__FMTS.items():
            if isinstance(info_in, _T):
                self.__info["info"] = info_in
                _cll(info_in)
                return
        else:
            raise ValueError(
                f"Invalid Page Info: {type(
                    info_in).__name__}")

    @property
    def name(self) -> str:
        return self.__info["name"]

    @property
    def filename(self) -> str:
        return self.__info["file"]

    @property
    def path(self) -> pathlib.Path:
        return self.__info["path"]

    @path.setter
    def path(self, path_in: pathlib.Path):
        if isinstance(path_in, pathlib.Path):
            if path_in.is_file():
                if self.__info["info"].is_file():
                    self.__info["path"] = path_in
                else:
                    self.__info["path"] = path_in.parent
            elif path_in.is_dir():
                if self.__info["info"].is_file():
                    self.__info["path"] = path_in / self.__info["file"]
                else:
                    self.__info["path"] = path_in
        else:
            raise ValueError(
                f"Invalid Page Path: {type(
                    path_in).__name__}")

    @property
    def data(self) -> bytes:
        return self.__info["data"]

    @property
    def type(self) -> _typeT:
        return self.__info["type"]

    @property
    def object(self) -> typing.Any:
        return self.__info["object"]

    @property
    def text(self) -> typing.Union[str, bytes, None]:
        try:
            if hasattr(self.info, "text"):
                return self.info.text
            else:
                return self.data.decode("utf-8")
        except UnicodeError as _:
            return None

    @property
    def file_size(self) -> int:
        return len(self.data)

    @property
    def compress_size(self) -> int:
        return self.__info["info"].compress_size

    @property
    def CRC(self):
        if hasattr(self.info, "CRC"):
            return self.info.CRC
        else:
            return zlib.crc32(self.data)

    def is_dir(self) -> bool:
        return self.__info["info"].is_dir()

    def is_file(self) -> bool:
        return not self.__info["info"].is_dir()

    def read(self) -> bytes:
        return self.open().read()

    def  write(self):
        self.archive.writestr(
            self.filename, self.data)

    def save(self, path_in: pathlib.Path = None):
        """
        Save the object to a local file a 'path'
        :param path_in:
        :return:
        """
        path_in = path_in if path_in is not None else self.path
        path_in.mkdir(parents=True, exist_ok=True)
        if path_in.is_file():
            path_in.write_bytes(self.data)
        elif path_in.is_dir():
            path_in.mkdir(parents=True, exist_ok=True)

    def load(self, path_in: pathlib.Path = None):
        """
        Load data from a local file at 'path'.
        :param path_in:
        :return: None
        """
        path_in = path_in if path_in is not None else self.path
        if path_in.exists():
            self.__info["data"] = path_in.read_bytes()
        else:
            raise FileNotFoundError(
                f"{path_in} does not exist!")

    def open(self) -> io.BytesIO:
        if self.is_file():
            return self.__archive.open(
                self.__info["info"])
        else:
            return io.BytesIO()

    def __handle_zipinfo(self, info_in: zip.ZipInfo):
        if isinstance(info_in, zip.ZipInfo):
            self.__info["file"] = info_in.filename
            self.__info["name"] = info_in.filename
            self.__info["path"] = pathlib.Path.cwd() / info_in.filename
            self.__info["data"] = self.read()
            self.__info["type"] = self._get_info_type(info_in)
            self.__info["object"] = self._get_info_object(info_in)
        else:
            raise ValueError(
                f"Invalid ZipInfo: {type(
                    info_in).__name__}")

    def __handle_rarinfo(self, info_in: rar.RarInfo):
        if isinstance(info_in, rar.RarInfo):
            self.__info["file"] = info_in.filename
            self.__info["name"] = info_in.filename
            self.__info["path"] = pathlib.Path.cwd() / info_in.filename
            self.__info["data"] = self.read()
            self.__info["type"] = self._get_info_type(info_in)
            self.__info["object"] = self._get_info_object(info_in)
        else:
            raise ValueError(
                f"Invalid RarInfo: {type(
                    info_in).__name__}")

    def __handle_7zinfo(self, info_in: sevenzip.SevenZipInfo):
        if isinstance(info_in, sevenzip.SevenZipInfo):
            self.__info["file"] = info_in.filename
            self.__info["name"] = info_in.filename
            self.__info["path"] = pathlib.Path.cwd() / info_in.filename
            self.__info["data"] = self.read()
            self.__info["type"] = self._get_info_type(info_in)
            self.__info["object"] = self._get_info_object(info_in)
        else:
            raise ValueError(
                f"Invalid SevenZipInfo: {type(
                    info_in).__name__}")

    def __handle_tarinfo(self, info_in: tarball.TarInfo):
        if isinstance(info_in, tarball.TarInfo):
            self.__info["file"] = info_in.filename
            self.__info["name"] = info_in.filename
            self.__info["path"] = pathlib.Path.cwd() / info_in.filename
            self.__info["data"] = self.read()
            self.__info["type"] = self._get_info_type(info_in)
            self.__info["object"] = self._get_info_object(info_in)
        else:
            raise ValueError(
                f"Invalid TarballInfo: {type(
                    info_in).__name__}")

    def __handle_epubinfo(self, info_in: epub.EPubInfo):
        if isinstance(info_in, epub.EPubInfo):
            self.__info["file"] = info_in.filename
            self.__info["name"] = self.__archive.name(info_in)
            self.__info["path"] = pathlib.Path.cwd() / info_in.filename
            self.__info["data"] = info_in.data
            self.__info["type"] = self._get_info_type(info_in)
            self.__info["object"] = info_in.object
        else:
            raise ValueError(
                f"Invalid EPubInfo: {type(
                    info_in).__name__}")

    def __handle_pdfinfo(self, info_in: pdf.PdfInfo):
        if isinstance(info_in, pdf.PdfInfo):
            self.__info["file"] = info_in.filename
            self.__info["name"] = info_in.filename
            self.__info["path"] = pathlib.Path.cwd() / info_in.filename
            self.__info["data"] = info_in.data
            self.__info["type"] = self._get_info_type(info_in)
            self.__info["object"] = info_in.object
        else:
            raise ValueError(
                f"Invalid PdfInfo: {type(
                    info_in).__name__}")

    def _get_info_type(self, info_in: _itemT) -> str:
        if isinstance(info_in, _itemT):
            if hasattr(info_in, "filename"):
                for _ty, _ext in _TYPE_EXT.items():
                    if info_in.filename.endswith(_ext):
                        return _ty
                return UNKNOWN
        raise ValueError(
            f"Invalid Info: {type(
                info_in).__name__}")

    def _get_info_object(self, info_in: _itemT) -> typing.Any:
        if isinstance(info_in, _itemT):
            if hasattr(info_in, "object"):
                return info_in.object
            else:
                _ty = self._get_info_type(info_in)
                return self.__TYPE2CREATOR[_ty](info_in)
        else:
            raise ValueError(
                f"Invalid Info: {type(
                    info_in).__name__}")

    def __handle_unknown(self, info_in: _itemT) -> bytes:
        """

        :param info_in:
        :return:
        """
        return self.__archive.open(info_in).read()

    def __create_image(self, info_in: _itemT) -> PIL.Image.Image:
        """

        :param info_in:
        :return:
        """
        try:
            if (hasattr(info_in, "object") and
                    isinstance(info_in.object, PIL.Image.Image)):
                return info_in.object
            else:
                return PIL.Image.open(
                    io.BytesIO(self.data))
        except PIL.UnidentifiedImageError as _:
            return PIL.Image.open(
                io.BytesIO(pathlib.Path(
                    self._BROKEN).read_bytes()))

    def __create_audio(self, info_in: _itemT) -> typing.Tuple[av.AudioStream, ...]:
        return av.open(io.BytesIO(self.read())).streams.audio

    def __create_video(self, info_in: _itemT) -> typing.Tuple[av.VideoStream, ...]:
        return av.open(io.BytesIO(self.read())).streams.video

    def __create_text(self, info_in: _itemT) -> str:
        return self.read().decode("utf-8")

    def __create_font(self, info_in: _itemT) -> tkextrafont.Font:
        if hasattr(info_in, "filename"):
            path = pathlib.Path(info_in.filename)
            with tempfile.NamedTemporaryFile(
                    prefix=path.stem, suffix=path.suffix,
                    delete=False) as font:
                font.write(info_in.get_content())
                self.__info["file"] = font.name
            try:
                return tkextrafont.Font(
                    file=path, family=PIL.ImageFont.truetype(
                        path, 1).font.family)
            except Exception as error:
                raise error
        else:
            raise ValueError(
                f"Invalid Info: {type(info_in).__name__}")

    def __create_html(self, info_in: _itemT) -> str:
        return self.__fix_tags(
            self.__info["archive"].open(info_in).read())

        # return bs4.BeautifulSoup(
        #     self.__info["archive"].open(info_in).read(),
        #     "lxml")

    def __create_xml(self, info_in: _itemT) -> bytes:
        pass

    def __create_css(self, info_in: _itemT) -> bytes:
        pass

    def __fix_tags(self, html_in: str) -> str:
        html_in = re.sub(
            r"<image\s", "<img ", re.sub(
                r"\sxlink:href=", " src=", html_in,
                flags=re.MULTILINE),
            flags=re.MULTILINE)
        return html_in

    def __enter__(self) -> 'BookItem':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __str__(self) -> str:
        return self.filename


# -----------------------------------------------------------------------------
# Book
# -----------------------------------------------------------------------------
class Book:
    """
    A set of written, printed, visual, or items bound together between
    a front and back cover. Usually, that yields knowledge or understanding.
    A book includes a bounding or spine that contains the pages that resides
    on a given side of the book when looking at its cover in an upright
    orientation.

    """
    def __init__(self, data_in: _dataT,
                 types_in: typing.Union[typing.List[_typeT], _typeT],
                 sorted_in: bool = False):
        self.__data, self.__types, self.__sorted, self.__items = (
            data_in, UNKNOWN, sorted_in, [])
        self.page_types = types_in
        self.data = data_in

    @property
    def items(self) -> typing.List[BookItem]:
        """

        :return: A list of all BookItems in this book.
        """
        return list(self.__items.values())

    @property
    def pages(self) -> typing.List[BookItem]:
        """

        :return: A list of BookItems considered pages of the book.
        """
        return list(i for i in self.__items.values() if i.type in self.page_types)
    
    @property
    def data(self) -> _dataT:
        return self.__data
    
    @data.setter
    def data(self, data_in: _dataT):
        if isinstance(data_in, _dataT):
            items = [BookItem(i, self.__data) for i in self.__data.infolist()]
            # Consider the spine order if it exists.
            if hasattr(self.data, "spine"):
                items = self.data.spine + items

            if self.__sorted:
                self.__items = collections.OrderedDict(
                    (i.filename, i) for i in sorted(
                        items, key=self.__key))
            else:
                self.__items = collections.OrderedDict(
                    (i.filename, i) for i in items)
        else:
            raise ValueError(
                f"Invalid Book Data: {type(
                    data_in).__name__}")

    @property
    def page_types(self) -> _typeT:
        """
        The set of types defining which BookItems are considered pages of the
        book. i.e. if IMAGE is in the page types, images items will be returned
        in the pages attribute.
        :return: The list of item types considered pages.
        """
        return self.__types

    @page_types.setter
    def page_types(self, types_in: typing.Union[typing.List[_typeT], _typeT]):
        types_in = [types_in] if not isinstance(
            types_in, (tuple, list)) else types_in
        if not any(t for t in types_in if t not in _TYPE_EXT.keys()):
            self.__types = types_in
        else:
            raise ValueError(
                f"Invalid Book Data: {type(
                    types_in).__name__}")

    @property
    def sorted(self) -> bool:
        return self.__sorted

    @staticmethod
    def __key(item_in: BookItem) -> typing.List:
        return [int(c) if c.isdigit() else c.lower() for c in
                re.split(r'(\d+)', f"{item_in.filename}")]

    def __len__(self) -> int:
        return len(self.__items)

    def __iter__(self) -> iter:
        return iter(self.__items.values())

    def __dict__(self) -> dict:
        """
        :return: dict: An unordered filename-BookItem pair dictionary of the
        book's items.
        """
        return {_k: _v for _k, _v in self.__items.items()}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __getitem__(self, key_in: typing.Union[int | str]) -> BookItem:
        if isinstacne(key_in, str):
            return {i.filename: i for i in self.__items}[key_in]
        elif isinstacne(key_in, int):
            return self.__items[
                0 if index_in < 0 else -1 if index >= len(
                    self.__items) else index_in]
        else:
            raise ValueError(
                f"Invalid Key/Index: {type(key_in).__name__}")

    def __setitem__(self, key_in: typing.Union[int | str], item_in: BookItem):
        if isinstacne(key_in, (str, int)):
            pass
        else:
            raise ValueError(
                f"Invalid Key/Index: {type(key_in).__name__}")


if __name__ == "__main__":
    cases = [
        # (zip.ZipFile, pathlib.Path(__file__).parent.parent /
        #  "test" / "AX3LBRAVO - Damsels in Distress.cbz", IMAGE, True),
        # (rar.RarFile, pathlib.Path(__file__).parent.parent /
        #  "test" / "Ay-Papi 1.cbr", IMAGE, True),
        # (sevenzip.SevenZipFile, pathlib.Path(__file__).parent.parent /
        #  "test" / "National Geographic 2010-06-01.cb7", IMAGE, True),
        # (tarball.TarFile, pathlib.Path(__file__).parent.parent /
        #  "test" / "[1995] The Calvin and Hobbes Tenth Anniversary Book.cbt", IMAGE, True),
        (epub.EPubFile, pathlib.Path(__file__).parent.parent /
         "test" / "Masou Gakuen HxH vol.01.epub", HTML, False),
        (pdf.PdfFile, pathlib.Path(__file__).parent.parent /
         "test" / "Space Visual Encyclopedia By DK.pdf", IMAGE, False)
    ]

    for (_C, _f, type, sort) in cases:
        with _C(_f, mode="r") as archive:
            book = Book(archive, type, sort)
            pass

    pass
