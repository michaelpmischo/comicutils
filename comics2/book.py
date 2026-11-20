#!/usr/bin/env python3
import sys, pathlib, io, re, typing, types, tempfile, collections, json, functools
import tkinter
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.comics2 import factory, zip, rar, sevenzip, tar, epub, pdf
    from comicutils.gui2 import popup
    from comicutils.utils import packages, resolver
else:
    from . import factory, zip, rar, sevenzip, tar, epub, pdf
    from ..gui2 import popup
    from ..utils import packages, resolver
packages.require({
    # "bs4": ("bs4", "beautifulsoup4"),
    "PIL": ("PIL", "pillow"),
    "PIL.Image": ("PIL.Image", "pillow"),
    "PIL.ImageTk": ("PIL.ImageTk", "pillow"),
    "PIL.ImageOps": ("PIL.ImageOps", "pillow"),
    "bs4": ("bs4", "BeautifulSoup4"),
    "tkextrafont": ("tkextrafont", "tkextrafont"),
    "av": ("av", "av")},
    __name__)
# <<< --------------------------- ENG IMPORTS ---------------------------- >>>


# -----------------------------------------------------------------------------
# Module Constants
# -----------------------------------------------------------------------------
(BOOKITEM_UNKNOWN, BOOKITEM_IMAGE, BOOKITEM_VIDEO, BOOKITEM_AUDIO,
 BOOKITEM_BOOKMARKS, BOOKITEM_DIR, BOOKITEM_TEXT, BOOKITEM_FONT,
 BOOKITEM_HTML, BOOKITEM_XML, BOOKITEM_CSS) = (
    "UNKNOWN", "IMAGE", "VIDEO", "AUDIO", "BOOKMARKS",
    "DIR", "TEXT", "FONT", "HTML", "XML", "CSS")
_TYPE_EXT = {
    BOOKITEM_IMAGE: tuple(PIL.Image.registered_extensions().keys()),
    BOOKITEM_AUDIO: tuple(sorted({f".{e}" for v in av.formats_available for f in [
        av.format.ContainerFormat(v)] if f.extensions for e in f.extensions if any(
        x in v or x in f.long_name.lower() for x in [
            'audio', 'sound', 'music', 'pcm', 'wav', 'mp3', 'flac', 'ogg', 'aiff'])})),
    BOOKITEM_VIDEO: tuple(sorted({f".{e}" for v in av.formats_available for f in [
        av.format.ContainerFormat(v)] if f.extensions for e in f.extensions if any(
        x in v or x in f.long_name.lower() for x in [
            'video', 'movie', 'mp4', 'mkv', 'avi', 'h264', 'hevc', 'webm'])})),
    BOOKITEM_BOOKMARKS: (".bookmarks",),
    BOOKITEM_TEXT: (".txt",),
    BOOKITEM_FONT: ('.ttf', '.otf', '.ttc', '.fon', '.fnt') if (
        sys.platform.startswith('win')) else (
        ('.ttf', '.otf', '.ttc') if (
            sys.platform.startswith('linux')) else ()),
    BOOKITEM_HTML: (".html", ".xhtml", ".mhtml",),
    BOOKITEM_XML: (".xml",),
    BOOKITEM_CSS: (".css",),
}


# -----------------------------------------------------------------------------
# Module Types
# -----------------------------------------------------------------------------
# Types Used in this module.
_infoT = typing.Union[zip.ZipInfo, rar.RarInfo, sevenzip.SevenZipInfo, tar.TarInfo, epub.EPubInfo, pdf.PdfInfo]
_arcT = typing.Union[zip.ZipFile, rar.RarFile, sevenzip.SevenZipFile, tar.TarFile, epub.EPubFile, pdf.PdfFile]
_typeT = typing.Literal[
    BOOKITEM_UNKNOWN, BOOKITEM_IMAGE, BOOKITEM_VIDEO,
    BOOKITEM_AUDIO, BOOKITEM_BOOKMARKS, BOOKITEM_TEXT,
    BOOKITEM_FONT, BOOKITEM_HTML, BOOKITEM_XML,
    BOOKITEM_CSS]


# -----------------------------------------------------------------------------
# BookItem
# -----------------------------------------------------------------------------
class BookItem:
    """
    BookItem is any data item in the contents of a book file. For instance, if
    the book contains a set of compressed image file, then there shall be a
    BookItem produced per image in the book. Items consist of images, audio,
    videos, html, xml, fonts, text, stylesheets (css), and many other unknown
    BookItem types.

    Each book item contains a set of attributes pertaining to the object.

    number: The number position in the book of the item or None if it is a
    silent object such as a stylesheet, or font.
    title: The title of the item. In the case of a chapter, page, or bookmark.
    file: The file name of the item, if one exists.
    data: The bytes representation of the raw data of the object. This could be
    an image, text, a/v streams, etc... represented in bytes.

    """
    _BROKEN = resolver.icon_root() / "broken.png"

    def __init__(self, info_in: _infoT, archive_in: _arcT, number_in: int = None):
        self.__FMTS, self.__TYPE2OBJ = {
            zip.ZipInfo: self.__handle_zipinfo,
            rar.RarInfo: self.__handle_rarinfo,
            sevenzip.SevenZipInfo: self.__handle_7zinfo,
            tar.TarInfo: self.__handle_tarinfo,
            epub.EPubInfo: self.__handle_epubinfo,
            pdf.PdfInfo: self.__handle_pdfinfo,
        }, {
            BOOKITEM_UNKNOWN: self.__open_unknown,
            BOOKITEM_IMAGE: self.__open_image,
            BOOKITEM_AUDIO: self.__open_audio,
            BOOKITEM_VIDEO: self.__open_video,
            BOOKITEM_BOOKMARKS: self.__open_bookmarks,
            BOOKITEM_DIR: self.__open_dir,
            BOOKITEM_TEXT: self.__open_text,
            BOOKITEM_FONT: self.__open_font,
            BOOKITEM_HTML: self.__open_html,
            BOOKITEM_XML: self.__open_xml,
            BOOKITEM_CSS: self.__open_css,
        }
        if isinstance(info_in, _infoT):
            self.__info = {
                "number": -1,
                "info": info_in,
                "title": "BookItem",
                "file": "",
                "data": b"",
                "links": [],
            }

            # Set the values.
            self.set_info(info_in, archive_in, number_in)
        else:
            raise ValueError(
                f"Invalid Page Info: {type(info_in).__name__}")

    @property
    def info(self) -> _infoT:
        return self.__info["info"]

    def set_info(self, info_in: _infoT, archive_in: _arcT, number_in: int = -1):
        for _T, _cll in self.__FMTS.items():
            if isinstance(info_in, _T):
                self.__info["info"] = info_in
                self.__handle_generic(info_in, archive_in, number_in)
                # _cll(info_in, archive_in, number_in)
                return
        else:
            raise ValueError(
                f"Invalid Page Info: {type(
                    info_in).__name__}")

    @property
    def number(self) -> int:
        return self.__info["number"]

    @property
    def title(self) -> str:
        return self.__info["title"]

    @property
    def filename(self) -> str:
        return self.__info["file"]

    @property
    def data(self) -> bytes:
        return self.__info["data"]

    @data.setter
    def data(self, data_in: bytes):
        if isinstance(data_in, bytes):
            self.__info["data"] = data_in
        else:
            raise ValueError(
                f"Invalid Data: {type(data_in).__name__}")

    @property
    def links(self) -> typing.List[...]:
        return self.__info["links"]

    @property
    def type(self) -> _typeT:
        try:
            return [_ty for _ty in [t for t, e in _TYPE_EXT.items() if self.filename.endswith(e)]][0]
        except IndexError as _:
            return BOOKITEM_UNKNOWN

    @property
    def object(self) -> typing.Any:
        return self.__TYPE2OBJ[self.type]()

    @property
    def text(self) -> typing.Union[str, bytes, None]:
        try:
            return self.open('r').read()
        except UnicodeError as _:
            return None

    @property
    def file_size(self) -> int:
        return len(self.data)

    @property
    def size(self) -> typing.Tuple[int, int]:
        return self.width, self.height

    @property
    def width(self) -> int:
        object = self.object
        if isinstance(object, PIL.Image.Image):
            return object.width
        else:
            return 0

    @property
    def height(self) -> int:
        object = self.object
        if isinstance(object, PIL.Image.Image):
            return object.height
        else:
            return 0

    def open(self, mode_in = 'rb') -> typing.Union[io.BytesIO, io.TextIOWrapper]:
        if mode_in.lower() in ('rb', 'wb'):
            return io.BytesIO(self.data)
        elif mode_in.lower() in ('r', 'w'):
            return io.TextIOWrapper(io.BytesIO(self.data))
        else:
            raise ValueError(
                f"Invalid Open Mode: {mode_in}")

    def save(self, path_in: pathlib.Path):
        if isinstance(path_in, pathlib.Path):
            path_in.parent.mkdir(parents=True, exist_ok=True, mode=750)
            path_in.write_bytes(self.data)
        else:
            raise ValueError(
                f"Invalid Save Path: {type(
                    path_in).__name__}")

    def __handle_zipinfo(self, info_in: zip.ZipInfo,
            archive_in: zip.ZipFile = None, number_in: int = -1):
        if isinstance(info_in, zip.ZipInfo):
            self.__info["number"] = number_in
            self.__info["file"] = info_in.filename
            self.__info["name"] = pathlib.Path(
                info_in.filename).stem.title()
            self.__info["links"] = None
            if isinstance(archive_in, zip.ZipFile):
                self.__info["data"] = archive_in.open(
                    info_in).read()
            elif not isinstance(archive_in, types.NoneType):
                raise ValueError(
                    f"Invalid ZipFile: {type(
                        info_in).__name__}")
        else:
            raise ValueError(
                f"Invalid ZipInfo: {type(
                    info_in).__name__}")

    def __handle_rarinfo(self, info_in: rar.RarInfo,
            archive_in: rar.RarFile = None, number_in: int = -1):
        if isinstance(info_in, rar.RarInfo):
            self.__info["number"] = number_in
            self.__info["file"] = info_in.filename
            self.__info["name"] = pathlib.Path(
                info_in.filename).stem.title()
            self.__info["links"] = None
            if isinstance(archive_in, rar.RarFile):
                self.__info["data"] = archive_in.open(
                    info_in).read()
            elif not isinstance(archive_in, types.NoneType):
                raise ValueError(
                    f"Invalid RarFile: {type(
                        info_in).__name__}")
        else:
            raise ValueError(
                f"Invalid RarInfo: {type(
                    info_in).__name__}")

    def __handle_7zinfo(self, info_in: sevenzip.SevenZipInfo,
            archive_in: sevenzip.SevenZipFile = None, number_in: int = -1):
        if isinstance(info_in, sevenzip.SevenZipInfo):
            self.__info["number"] = number_in
            self.__info["file"] = info_in.filename
            self.__info["name"] = pathlib.Path(
                info_in.filename).stem.title()
            self.__info["links"] = None
            if isinstance(archive_in, sevenzip.SevenZipFile):
                self.__info["data"] = archive_in.open(
                    info_in).read()
            elif not isinstance(archive_in, types.NoneType):
                raise ValueError(
                    f"Invalid SevenZipFile: {type(
                        info_in).__name__}")
        else:
            raise ValueError(
                f"Invalid SevenZipInfo: {type(
                    info_in).__name__}")

    def __handle_tarinfo(self, info_in: tar.TarInfo,
            archive_in: tar.TarFile = None, number_in: int = -1):
        if isinstance(info_in, tar.TarInfo):
            self.__info["number"] = number_in
            self.__info["file"] = info_in.filename
            self.__info["name"] = pathlib.Path(
                info_in.filename).stem.title()
            self.__info["links"] = None
            if isinstance(archive_in, tar.TarFile):
                self.__info["data"] = archive_in.open(
                    info_in).read()
            elif not isinstance(archive_in, types.NoneType):
                raise ValueError(
                    f"Invalid TarFile: {type(
                        info_in).__name__}")
        else:
            raise ValueError(
                f"Invalid TarInfo: {type(
                    info_in).__name__}")

    def __handle_epubinfo(self, info_in: epub.EPubInfo,
            archive_in: epub.EPubFile = None, number_in: int = -1):
        if isinstance(info_in, epub.EPubInfo):
            self.__info["number"] = number_in
            self.__info["file"] = info_in.filename
            self.__info["name"] = pathlib.Path(
                info_in.filename).stem.title()
            self.__info["links"] = self.__epub_link_locations()
            if isinstance(archive_in, epub.EPubFile):
                self.__info["data"] = archive_in.open(
                    info_in).read()
            elif not isinstance(archive_in, types.NoneType):
                raise ValueError(
                    f"Invalid EPubFile: {type(
                        info_in).__name__}")
        else:
            raise ValueError(
                f"Invalid EPubInfo: {type(
                    info_in).__name__}")

    def __handle_pdfinfo(self, info_in: pdf.PdfInfo,
            archive_in: pdf.PdfFile = None, number_in: int = -1):
        if isinstance(info_in, pdf.PdfInfo):
            self.__info["number"] = number_in
            self.__info["file"] = info_in.filename
            self.__info["name"] = pathlib.Path(
                info_in.filename).stem.title()
            self.__info["links"] = self.__epub_link_locations()
            if isinstance(archive_in, pdf.PdfFile):
                self.__info["data"] = archive_in.open(
                    info_in).read()
            elif not isinstance(archive_in, types.NoneType):
                raise ValueError(
                    f"Invalid PdfFile: {type(
                        info_in).__name__}")
        else:
            raise ValueError(
                f"Invalid PdfInfo: {type(
                    info_in).__name__}")

    def __handle_generic(self, info_in: _infoT,
            archive_in: _arcT = None, number_in: int = -1):
        if isinstance(info_in, _infoT):
            self.__info["number"] = number_in
            self.__info["file"] = info_in.filename
            self.__info["name"] = pathlib.Path(
                info_in.filename).stem.title()
            self.__info["links"] = self.__epub_link_locations()
            if isinstance(archive_in, _arcT):
                self.__info["data"] = archive_in.open(
                    info_in).read()
            elif not isinstance(archive_in, types.NoneType):
                raise ValueError(
                    f"Invalid Argument 'archive_in': {type(
                        archive_in).__name__}")
        else:
            raise ValueError(
                f"Invalid Argument 'info_in': {type(
                    info_in).__name__}")

    def __open_unknown(self) -> io.BytesIO:
        return self.open('rb')

    def __open_image(self) -> PIL.Image.Image:
        try:
            return PIL.Image.open(self.open('rb'))
        except PIL.UnidentifiedImageError as _:
            return PIL.Image.open(
                io.BytesIO(pathlib.Path(
                    self._BROKEN).read_bytes()))

    def __open_video(self) -> typing.Tuple[av.VideoStream, ...]:
        try:
            return av.open(self.open('rb')).streams.video
        except Exception as _:
            return ()

    def __open_audio(self) -> typing.Tuple[av.AudioStream, ...]:
        try:
            return av.open(self.open('rb')).streams.audio
        except Exception as _:
            return ()

    def __open_bookmarks(self) -> typing.Union[typing.List, typing.Dict]:
        return json.loads(self.text)

    def __open_dir(self) -> pathlib.Path:
        return pathlib.Path(self.filename)

    def __open_text(self) -> io.TextIOWrapper:
        return self.open('r')

    def __open_font(self) -> tkextrafont.Font:
        path = pathlib.Path(self.filename)
        with tempfile.NamedTemporaryFile(
                prefix=path.stem, suffix=path.suffix, delete=False) as font:
            font.write(self.data)
        try:
            return tkextrafont.Font(
                file=font.name, family=PIL.ImageFont.truetype(
                    path, 1).font.family)
        except Exception as error:
            raise error

    def __open_html(self) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(
            self.__fix_tags(self.text), "lxml")

    def __open_xml(self) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(self.text, "xml")

    def __open_css(self) -> io.TextIOWrapper:
        return self.open('r')

    def __fix_tags(self, html_in: str) -> str:
        html_in = re.sub(
            r"<image\s", "<img ", re.sub(
                r"\sxlink:href=", " src=", html_in,
                flags=re.MULTILINE),
            flags=re.MULTILINE)
        return html_in

    def __epub_link_locations(self):
        links = []
        if isinstance(self.info, (epub.EPubInfo, pdf.PdfInfo)):
            for (l1, l2) in self.__links():
                try:
                    links.append(((l1.rect.x0, l1.rect.y0, l1.rect.x1, l1.rect.y1),
                        l2["page"] if "page" in l2.keys() else l2["uri"] if l1.is_external else None,
                            l1.uri.split("#")[0]))
                except KeyError as _:
                    pass
        return links

    def __links(self):
        l1 = self.info.first_link
        for l2 in self.info.get_links():
            if l1 is not None:
                yield l1, l2
                l1 = l1.next
            else:
                break

    def __enter__(self) -> 'BookItem':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __str__(self) -> str:
        return self.filename

    def __repr__(self) -> str:
        return f"{self}"


# -----------------------------------------------------------------------------
# Book
# -----------------------------------------------------------------------------
class Book(collections.OrderedDict):
    """
    A set of written, printed, visual, or items bound together between
    a front and back cover. Usually, that yields knowledge or understanding.
    A book includes a bounding or spine that contains the pages that resides
    on a given side of the book when looking at its cover in an upright
    orientation.

    """
    EXTENSIONS = [
        '.cbz', '.zip',
        '.cbr', '.rar',
        '.cb7', '.7z',
        '.cbt', '.tar', '.tar.gz', '.tar.xz', '.tar.bz2',
        '.epub',
        '.pdf']
    __SINGLE_RATIO = 1.1

    def __init__(self, file_in: typing.Union[str, pathlib.Path],
                 types_in: typing.Union[typing.List[_typeT], _typeT],
                 root_in: tkinter.Widget = None,
                 sorted_in: bool = False,
                 **args_in):
        super().__init__()
        progress = args_in.pop("progress") if "progress" in args_in.keys() else None
        mode_in = args_in.pop("mode") if "mode" in args_in.keys() else 'r'
        (self.__data, self.__types, self.__sorted, self.__file,
         self.__pairs, self.__root, self.__data_id, self.__loading) = (
            None, BOOKITEM_UNKNOWN, sorted_in, file_in, [], root_in, None,
            None if root_in is None else tkinter.BooleanVar(
                root_in, value=False))
        self.page_types = types_in
        self.open(mode_in, progress=progress)

    @property
    def pages(self) -> typing.List[typing.Tuple[str,BookItem]]:
        """
        All the BookItems considered pages in this book.
        :return: list[BookItem]: A list of BookItems considered pages of this
        book.
        """
        return list((p, i) for p, i in self.items() if i.type in self.page_types)

    @property
    def pairs(self) -> typing.List[typing.Tuple[
        typing.Union[typing.Tuple[str, BookItem], types.NoneType], ...]]:
        """
        All the page pairs for the book in a list of tuples.
        :return: list[BookItem]: A list of BookItems pairs for a double page
        display layout.
        """
        # TODO: Need to work this method. AND need to create the page pairs
        pair, pairs = (), []
        for i, (_, info) in enumerate(self.pages):
            # If the width is greater than the height by the configured
            # ratio, then dump the info index and add the
            if i == 0 or info.width >= (info.height * self.__SINGLE_RATIO):
                if len(pair) > 0:
                    pairs.append(pair)
                pairs.append((i,))
                pair = ()
            # Dump at an even page
            elif not i & 1:
                pairs.append(pair + (i,))
                pair = ()
            else:
                pair += (i,)

        # Dump any remaining pair
        if len(pair) > 0:
            pairs.append(pair)
        return pairs

    @property
    def file(self) -> pathlib.Path:
        return self.__file

    @file.setter
    def file(self, file_in: typing.Union[str, pathlib.Path]):
        if isinstance(file_in, (str, pathlib.Path)):
            self.__file = file_in
            self.data = factory.open_data(
                self.__file, 'r')
        else:
            raise TypeError(
                f"Invalid File: {type(
                    file_in).__name__}")

    @property
    def title(self):
        try:
            return self.data.title
        except AttributeError as _:
            return self.file.stem

    @property
    def author(self) -> str:
        try:
            return self.data.author
        except AttributeError as _:
            return ""

    @property
    def toc(self):
        try:
            toc, toc_keywords = (
                self.data.get_toc(),
                {"table of contents", "contents", "toc"})
            for level, title, page in toc:
                if title.strip().lower() in toc_keywords:
                    return page - 1
            else:
                try:
                    return max(
                        (p for _, p in self.pages if p.links),
                        key=lambda p: len(p.links)).number
                except ValueError as _:
                    return None
        except AttributeError as _:
            return None

    @property
    def data(self) -> _arcT:
        """
        The raw representation of the book data, archive, items, etc...
        :return:
        """
        return self.__data
    
    @data.setter
    def data(self, data_in: _arcT):
        """
        The raw representation of the book data, archive, items, etc...
        :param data_in: The raw representation of the book data, archive,
        etc... This must be of the types: zip.ZipFile, rar.RarFile,
        sevenzip.SevenZipFile, tar.TarFile, epub.EPubFile, or pdf.PdfFile.
        """
        self.set_data(data_in)

    def set_data(self, data_in: _arcT, **args_in):
        if isinstance(data_in, _arcT):
            if self.__root is not None:
                self.__loading.set(True)
                progress = args_in.pop('progress') if (
                        'progress' in args_in.keys()) else (
                    popup.ProgressBar(self.__root))
                progress.txt = "Processing Book..."
                if self.__data_id is not None:
                    self.__root.after_cancal(self.__data_id)
                self.__root.after(50, functools.update_wrapper(
                    functools.partial(
                        self._data, data_in,
                        progress=progress, **args_in),
                    self._data))
            else:
                self._data(data_in, **args_in)
        else:
            raise ValueError(
                f"Invalid Book Data: {type(
                    data_in).__name__}")

    def _data(self, data_in: _arcT, **args_in):
        progress = args_in.pop("progress") if (
                "progress" in args_in.keys()) else None
        try:
            self.clear()
            self.__data = data_in
            if self.__data is not None:
                # Consider the spine order if it exists.
                items = self.data.spine + self.__data.infolist() if (
                    hasattr(self.data, "spine")) else (
                        self.__data.infolist())
                if self.__sorted:
                    items = sorted(items, key=self.__key)
                if progress:
                    progress.max, progress.text = (
                        len(items) + 1, f"Processing: {self.file}...")
                for n, i in enumerate(sorted(items, key=self.__key)):
                    self.__add_item(i, n, progress)
        finally:
            if self.__loading is not None:
                self.__loading.set(False)

    def __add_item(self, item_in: _infoT, number_in: int,
                   progress_in: popup.ProgressBar = None):
        if progress_in is not None:
            progress_in.text = f"Processing: {item_in.filename}"
        i = BookItem(item_in, self.__data, number_in)
        self[i.filename] = i
        if progress_in is not None:
            progress_in.progress()

    def wait_on_loading(self):
        """
        Wait for this book to complete loading. If the book isn't currently
        loading data, this method will return immediately. Otherwise, it
        will pend your thread until loading is complete.
        """
        if self.__loading is not None and self.__loading.get():
            self.__root.wait_variable(self.__loading)

    @property
    def page_types(self) -> typing.List[_typeT]:
        """
        The set of types defining which BookItems are considered pages of the
        book. i.e. if IMAGE is in the page types, images items will be returned
        in the pages attribute.
        :return: The list of item types considered pages.
        """
        return self.__types

    @page_types.setter
    def page_types(self, types_in: typing.Union[typing.List[_typeT], _typeT]):
        """
        The set of types defining which BookItems are considered pages of the
        book. i.e. if IMAGE is in the page types, images items will be returned
        in the pages attribute.

        :param types_in: The list of item types considered pages. This must be
        tuple or list of string in Literal[]: _typeT
        """
        types_in = [types_in] if not isinstance(
            types_in, (tuple, list)) else types_in
        if not any(t for t in types_in if t not in _TYPE_EXT.keys()):
            self.__types = types_in
        else:
            raise ValueError(
                f"Invalid BookItem Type: {types_in}")

    @property
    def is_sorted(self) -> bool:
        """
        Indication of the sorting of the BookItems. True if the BookItems
        should be sorted in AlphaNumeric order, otherwise False.

        :return: True if the BookItems should be sorted in AlphaNumeric
        order, else False.
        """
        return self.__sorted

    def extractall(self, path_in: pathlib.Path = pathlib.Path.cwd()):
        """
        Extract all BookItems from this book to 'path_in'. This will create
        any subdirectories specified in the items with the root at 'path_in'.
        If 'path_in' doesn't exist, it will be created without error.

        :param path_in: The root path of the directory to extract all of
        the BookItems.
        """
        for item in self.values():
            item.save(path_in)

    def extract(self, item_in: BookItem, path_in: pathlib.Path = pathlib.Path.cwd()):
        """
        Extract 'item_in' BookItem from this book to 'file_in'. This will
        create the parents of 'path_in' and any subdirectories specified.
        If 'path_in' is a directory, extract will us it as a root path and
        create any further subdirectories specified in the BookItem itself.

        :param item_in: The BookItem to extract.
        :param path_in: The root path or file name of the extracted BookItem's
        file.
        """
        if isinstance(item_in, BookItem):
            print(f"Extracting: {path_in}...")
            item_in.save(path_in)

    def compressall(self, path_in: pathlib.Path = pathlib.Path.cwd()):
        for item in self.values():
            self.compress(item, path_in)

    def compress(self, item_in: BookItem, file_in: pathlib.Path = pathlib.Path.cwd()):
        # TODO: Need to add this capability to BookItem? write?
        pass

    @staticmethod
    def __key(item_in: BookItem) -> typing.List:
        return [int(c) if c.isdigit() else c.lower() for c in
                re.split(r'(\d+)', f"{item_in.filename}")]

    def open(self, mode_in: typing.Literal['r', 'w', 'a', 'x'] = 'r', **args_in) -> 'Book':
        progress = args_in.pop("progress") if (
                "progress" in args_in.keys()) else None
        self.set_data(
            factory.open_data(self.__file, mode_in, progress),
            progress=progress, **args_in)
        return self

    def close(self):
        try:
            self.__data.close()
        except (AttributeError, ValueError) as _:
            pass

    def __dict__(self) -> dict:
        """
        :return: dict: An unordered filename-BookItem pair dictionary of the
        book's items.
        """
        return super()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __len__(self) -> int:
        return len(self.pages)

    def __getitem__(self, key_in: typing.Union[int | str]) -> BookItem:
        if isinstance(key_in, (str, int)):
            if isinstance(key_in, int):
                # Allow this to raise an index error...
                key_in = list(self.keys())[key_in]
            return super().__getitem__(key_in)
        else:
            raise ValueError(
                f"Invalid Key/Index: {type(
                    key_in).__name__}")

    def __setitem__(self, key_in: typing.Union[int | str], item_in: BookItem):
        if isinstance(key_in, (str, int)):
            if isinstance(key_in, int):
                try:
                    key_in = list(self.keys())[key_in]
                except IndexError as _:
                    key_in = item_in.filename
            super().__setitem__(key_in, item_in)
        else:
            raise ValueError(
                f"Invalid Key/Index: {type(
                    key_in).__name__}")

    def __delitem__(self, key_in: typing.Union[int | str]):
        if isinstance(key_in, (str, int)):
            if isinstance(key_in, int):
                # Allow this to raise an index error...
                key_in = list(self.keys())[key_in]
            super().__delitem__(key_in)
        else:
            raise ValueError(
                f"Invalid Key/Index: {type(
                    key_in).__name__}")


if __name__ == "__main__":
    __cases = [
        # (pathlib.Path(__file__).parent.parent /
        #  "test" / "AX3LBRAVO - Damsels in Distress.cbz", BOOKITEM_IMAGE, True),
        # (pathlib.Path(__file__).parent.parent /
        #  "test" / "Ay-Papi 1.cbr", BOOKITEM_IMAGE, True),
        # (pathlib.Path(__file__).parent.parent /
        #  "test" / "National Geographic 2010-06-01.cb7", BOOKITEM_IMAGE, True),
        # (pathlib.Path(__file__).parent.parent.parent /
        #  "test" / "[1995] The Calvin and Hobbes Tenth Anniversary Book.cbt", BOOKITEM_IMAGE, True),
        (pathlib.Path(__file__).parent.parent /
         "test" / "Masou Gakuen HxH vol.01.epub", BOOKITEM_IMAGE, False),
        (pathlib.Path(__file__).parent.parent /
         "test" / "Space Visual Encyclopedia By DK.pdf", BOOKITEM_IMAGE, False)
    ]

    for __f, __t, __sort in __cases:
        with Book(__f, __t, None, 'r', __sort) as book:
            try:
                for item in book:
                    #item.save()
                    pass
            finally:
                book.close()
            pass
    pass
