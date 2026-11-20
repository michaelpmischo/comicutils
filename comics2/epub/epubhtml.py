#!/usr/bin/env python3
import sys, os, re, pathlib, tempfile, html, io, urllib, types, typing, zlib, warnings, tkinter
import PIL.Image, PIL.ImageTk, PIL.ImageOps, PIL.ImageFont
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils import packages, resolver
else:
    from .. import packages, resolver

# Cairo Workaround Hack...
gtk_root = f"{resolver.gtk_root() / "bin"}"
os.add_dll_directory(gtk_root)

packages.require({
    "ebooklib": ("ebooklib", "EbookLib"),
    "ebooklib.epub": ("ebooklib.epub", "EbookLib"),
    "cairosvg": ("cairosvg", "cairosvg"), # cairosvg
    "lxml": ("lxml", "lxml"),
    # "bs4": ("bs4", "beautifulsoup4"),
    "tkextrafont": ("tkextrafont", "tkextrafont"),
    "av": ("av", "av")},
    __name__)
# warnings.filterwarnings("ignore", category=bs4.XMLParsedAsHTMLWarning)


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
ITEM_UNKNOWN = ebooklib.ITEM_UNKNOWN
ITEM_IMAGE = ebooklib.ITEM_IMAGE
ITEM_DOCUMENT = ebooklib.ITEM_DOCUMENT
ITEM_STYLE = ebooklib.ITEM_STYLE
ITEM_COVER = ebooklib.ITEM_COVER
ITEM_AUDIO = ebooklib.ITEM_AUDIO
ITEM_FONT = ebooklib.ITEM_FONT
ITEM_NAVIGATION = ebooklib.ITEM_NAVIGATION
ITEM_VECTOR = ebooklib.ITEM_VECTOR
ITEM_VIDEO = ebooklib.ITEM_VIDEO
ITEM_SMIL = ebooklib.ITEM_SMIL


def is_epubfile(path_in: str) -> bool:
    if pathlib.Path(path_in).suffix != ".epub":
        return False
    with open(path_in, "rb") as arc:
        try:
            return arc.read(8).decode("utf-8").startswith("PK")
        finally:
            arc.close()


class EPubInfo:
    _BROKEN = resolver.icon_root() / "broken.png"

    def __init__(self, info_in: ebooklib.epub.EpubItem):
        self.__info = {
            "info": info_in,
            "file": "",
            "title": "",
            "data": b"",
            "type": ebooklib.ITEM_UNKNOWN,
            "object": None,
        }
        # Set the values.
        self.info = info_in

    @property
    def info(self) -> ebooklib.epub.EpubItem:
        return self.__info["info"]

    @info.setter
    def info(self, info_in: ebooklib.epub.EpubItem):
        if isinstance(info_in, ebooklib.epub.EpubItem):
            info_type = info_in.get_type()
            self.__info["info"] = info_in
            self.__info["file"] = info_in.get_name()
            self.__info["data"] = info_in.get_content()
            self.__info["type"] = info_type
            if info_type in [ebooklib.ITEM_IMAGE,
                             ebooklib.ITEM_COVER]:
                self.__handle_image(info_in)

            elif info_type in [ebooklib.ITEM_DOCUMENT,
                               ebooklib.ITEM_STYLE,
                               ebooklib.ITEM_SCRIPT,
                               ebooklib.ITEM_NAVIGATION]:
                self.__handle_doc(info_in)
            elif info_type in [ebooklib.ITEM_VECTOR]:
                self.__handle_vector(info_in)
            elif info_type in [ebooklib.ITEM_FONT]:
                self.__handle_font(info_in)
            elif info_type in [ebooklib.ITEM_VIDEO]:
                self.__handle_video(info_in)
            elif info_type in [ebooklib.ITEM_SMIL]:
                pass
            else:
                pass
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
        return html.unescape(
            self.__info["data"].decode("utf-8"))

    @property
    def file_size(self) -> int:
        return len(self.__info["data"])

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

    def __handle_image(self, info_in: ebooklib.epub.EpubItem):
        try:
            # In some cases, SVGs dont fall under the ITEM_VECTOR type.
            if "svg" in info_in.media_type:
                self.__handle_vector(info_in)
            else:
                self.__info["object"] = PIL.Image.open(
                    io.BytesIO(info_in.get_content()))

        except PIL.UnidentifiedImageError as _:
            self.__info["object"] = PIL.Image.open(
                io.BytesIO(pathlib.Path(
                    self._BROKEN).read_bytes()))

    def __handle_doc(self, info_in: ebooklib.epub.EpubItem):
        self.__info["object"] = self.__fix_tags(
            info_in.get_content().decode("utf-8"))
        self.__info["data"] = self.__info["object"].encode("utf-8")
        # self.__info["object"] = bs4.BeautifulSoup(
        #     self.text, "lxml")

    def __fix_tags(self, html_in: str) -> str:
        html_in = re.sub(r"<image\s", "<img ", re.sub(
            r"\sxlink:href=", " src=", html_in, flags=re.MULTILINE),
                         flags=re.MULTILINE)
        return html_in

        # soup = bs4.BeautifulSoup(html_in, "lxml")
        # # XHTML Hack for this non-standard tag...
        # images = soup.find_all("image")
        # if len(images):
        #     for image in images:
        #         image.name = "img"
        #         # parent = tag.parent
        #         attrs = {"src": image.attrs.pop('xlink:href').replace("../", "")}
        #         image.update(tag.attrs)
        #         image.attrs = attrs
        # return soup.encode()

    def __handle_vector(self, info_in: ebooklib.epub.EpubItem):
        image = PIL.Image.open(
            io.BytesIO(cairosvg.svg2png(
                bytestring=info_in.get_content())))

        # We need to attempt to preserve the Alpha channel from SVG and
        # PNG file types. In order to accomplish this, we need to convert
        # any non "RBG" modes to RBG... then, to "RBGA".
        if image.mode in ("P", "1"):
            image = image.convert("RGB")
        self.__info["object"] = image.convert("RGBA")

    def __handle_video(self, info_in: ebooklib.epub.EpubItem):
        self.__info["object"] = av.open(
            io.BytesIO(info_in.get_content()))

    def __handle_font(self, info_in: ebooklib.epub.EpubItem):
        path = pathlib.Path(info_in.get_name())
        with tempfile.NamedTemporaryFile(
                prefix=path.stem, suffix=path.suffix,
                delete=False) as font:
            font.write(info_in.get_content())
            self.__info["file"] = font.name
        try:
            self.__info["object"] = tkextrafont.Font(
                file=path, family=PIL.ImageFont.truetype(
                    font.name, 1).font.family,
                size=16)
        except tkinter.TclError as _:
            self.__info["object"] = self.data

    def __enter__(self) -> 'EPubInfo':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class EPubFile:

    def __init__(self, file_in: pathlib.Path, **args_in):
        self.__infos, self.__book, self.__file = (
            {}, None, None)
        self.__mode = args_in.pop("mode") if "mode" in args_in.keys() else "r"
        self.file = file_in

    @property
    def file(self) -> pathlib.Path:
        return self.__file

    @file.setter
    def file(self, file_in: str | pathlib.Path):
        self.__file, self.__book, self.__infos, self.__names = file_in, None, {}, {}
        if isinstance(file_in, (str, pathlib.Path, types.NoneType)):
            self.__file = pathlib.Path(file_in)
            self.__book = ebooklib.epub.read_epub(f"{self.__file}")
            if self.__file.exists():
                self.__infos = {i.get_name(): EPubInfo(i) for i in self.__book.get_items()}
                self.__names = self.__titles()
        elif isinstance(file_in, types.NoneType):
            pass
        else:
            raise ValueError(
                f"Invalid File: {type(file_in).__name__}")

    @property
    def title(self) -> str:
        try:
            return self.__book.title
        except AttributeError as _:
            return ""

    def name(self, info_in: EPubInfo) -> str:
        try:
            return self.__names[info_in.filename]
        except KeyError as _:
            return pathlib.Path(
                info_in.filename).stem.title()

    @property
    def author(self) -> str:
        try:
            return self.metadata("creator")[0][0]
        except AttributeError as _:
            return ""

    @property
    def language(self) -> str:
        return self.__book.language

    @property
    def isbn(self) -> str:
        try:
            return self.metadata("identifier")[0][0]
        except AttributeError as _:
            return ""

    @property
    def cover(self) -> PIL.Image.Image:
        return list([i.object for i in self.__infos if (
                i.type == ebooklib.ITEM_COVER)])[0]

    @property
    def spine(self) -> typing.List[str]:
        if self.__book.spine:
            return list(EPubInfo(i) for i in [
                (self.__book.get_item_with_id(i[0]) if (
                    isinstance(i, tuple)) else (
                        self.__book.get_item_with_id(i))) for i in
                            self.__book.spine])
        else:
            return []

    def metadata(self, key_in: str) -> str:
        try:
            return self.__book.get_metadata("DC", key_in)
        except KeyError as _:
            try:
                return self.__book.get_metadata("OPF", key_in)
            except KeyError as _:
                return ""

    def extractall(self, path_in: pathlib.Path = None):
        path_in = path_in if path_in is not None else self.__file.parent / self.__file.stem
        path_in.mkdir(parents=True, exist_ok=True)
        for path, info in [(path_in / i.filename, i) for i in self.__infos.values()]:
            print(f"Extracting: {path_in / path}...")
            self.save(info, path)

    def __find_info(self, url_in: str) -> EPubInfo | None:
        name = os.path.relpath(
            urllib.parse.urlparse(url_in).path.lstrip("/").lstrip("..\\"),
            f"{pathlib.Path(__file__).parent}")
        if name in self.__infos.keys():
            return self.__infos[name]
        else:
            name = pathlib.Path(urllib.parse.urlparse(url_in).path).name
            for n, i in self.__infos.items():
                if n.endswith(name):
                    return i
        return None

    def open(self, info_in: str | EPubInfo):
        if isinstance(info_in, EPubInfo):
            return info_in.data
        elif isinstance(info_in, (str | pathlib.Path)):
            try:
                return io.BytesIO(self.__find_info(info_in).data)
            except AttributeError as _:
                raise FileNotFoundError(
                    f"Failed To File: {info_in}")
        else:
            raise ValueError(
                f"Invalid Info: {type(info_in).__name__}")

    def namelist(self) -> list[str]:
        """Return a list of file names in the epub."""
        return list(self.__infos.keys())

    def infolist(self) -> list[EPubInfo]:
        """Return a list of EPubInfo objects for members of the epub."""
        return list(self.__infos.values())

    def infodict(self) -> dict:
        """Return a list of EPubInfo objects for members of the epub."""
        return self.__infos

    def getinfo(self, name_in: str) -> EPubInfo:
        """
        Return a EPubInfo object with information about the member name.
        :param name_in: The entry name in the epub
        :return: RPubInfo:
        """
        return self.__find_info(name_in)

    def writestr(self, info_in: str | EPubInfo, data_in: bytes):
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

        file_in = info_in.filename if isinstance(info_in, EPubInfo) else info_in

    @property
    def pages(self) -> list:
        if self.__book.spine:
            return list((i.get_name(), EPubInfo(i)) for i in [
                (self.__book.get_item_with_id(i[0]) if (
                    isinstance(i, tuple)) else (
                        self.__book.get_item_with_id(i))) for i in
                            self.__book.spine])
        else:
            return list((i.filename, f"{i.object}") for i in self.__infos if (
                    i.type == ebooklib.ITEM_DOCUMENT))

    @property
    def table_of_contents(self):
        return self.__book.toc

    def close(self):
        pass

    def write(self, file_in: str | pathlib.Path | None):
        path_in = pathlib.Path(file_in).resolve() if file_in is not None else self.__file
        ebooklib.epub.write_epub(path_in, self.__book, compresslevel=9)

    def save(self, info_in: EPubInfo, file_in: pathlib.Path):
        file_in.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(info_in.object, PIL.Image.Image):
            info_in.object.save(f"{file_in}")
        else:
            file_in.write_bytes(info_in.data)

    def title(self, item_in: EPubInfo) -> str:
        pass

    def __titles(self, element_in = None) -> dict:
        """Recursively extracts all readable titles from an ebook's TOC structure."""
        titles = {}
        element_in = element_in if element_in is not None else self.__book.toc
        if isinstance(element_in, (list, tuple)):
            for item in element_in:
                titles.update(self.__titles(item))
        elif isinstance(element_in, (
                ebooklib.epub.Section, ebooklib.epub.Link)):
            if element_in.href:
                titles[element_in.href.split("#")[0]] = element_in.title
        elif hasattr(element_in, "title"):
            titles.append[element_in.title] = element_in.title
        return titles

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __getitem__(self, index_in: int) -> EPubInfo:
        return self.infolist()[index_in]


if __name__ == "__main__":
    # Replace with the path to your DRM-free EPUB file
    file = pathlib.Path(__file__).parent.parent / "test" / "Masou Gakuen HxH vol.01.epub"
    epub = EPubFile(file, mode='r')
    epub.extractall(pathlib.Path(__file__).parent)

