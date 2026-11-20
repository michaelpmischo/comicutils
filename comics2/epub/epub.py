#!/usr/bin/env python3
import sys, pathlib, typing, types, io, PIL.Image
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent.parent}")
    from comicutils.utils import packages, attributes
else:
    from ...utils import packages, attributes
packages.require({
    "pymupdf": ("pymupdf", "pymupdf"),
    "numpy": ("numpy", "numpy")},
    __name__)
# <<< --------------------------- ENG IMPORTS ---------------------------- >>>


# -----------------------------------------------------------------------------
# Magic Numbers
# -----------------------------------------------------------------------------
MAGICS = (
    (0, 4, b'PK\x03\x04', "zip"),
    (0, 4, b'PK\x05\x06', "zip"),
    (0, 4, b'PK\x07\x08', "zip"))
MAGIC = lambda f: tuple(cmp for off, n, magic, cmp in __MAGICS if (
        pathlib.Path(f).suffix == ".epub" and
        pathlib.Path(f).read_bytes()[off:off+n] == magic))


def is_epubfile(path_in: str) -> bool:
    return bool(MAGIC(path_in))


# -----------------------------------------------------------------------------
# EPubInfo
# -----------------------------------------------------------------------------
class EPubInfo(pymupdf.Page):
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
            self.__info["data"] = self.__extract_image(info_in)
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

    def __extract_image(self, info_in: pymupdf.Page) -> bytes:
        images = [
            b.get("image") for b in
            info_in.get_text("dict").get("blocks", []) if (
                    b.get("type") == 1)]
        # Only trim pages with a single image and no text.
        #if len(images) == 1 and not self.info.get_text().strip():
        if self.is_cover:
            return self.__make_opaque(
                pymupdf.Pixmap(images[0])).tobytes("png")
        else:
            return self.__make_opaque(
                info_in.get_pixmap(
                    dpi=300)).tobytes('png')

    @property
    def is_cover(self) -> bool:
        keys, html = ((
            r'class="cover"',
            r'id="cover"',
            r'epub:type="cover"',
            r'role="cover"'),
            self.info.get_text('html').lower())

        # 1. Filter out deep pages immediately
        if self.info.number != 0:
            return False
        else:
            # Check for specific image markers or metadata indicators
            # A true cover usually has an image block and minimal to
            # no text blocks. Otherwise, search for the html tags.
            return ((self.info.get_image_info(xrefs=True) and
                    len(self.info.get_text("blocks")) <= 2) or
                    any(k for k in keys if k in html))

    @property
    def is_blank(self) -> bool:
        """
        Returns True ONLY if a page is a truly empty, transparent placeholder.
        Returns False if it is a structural vector cover (like Onyx Storm).
        """
        # If the page contains text, images or drawings...
        if (self.info.get_text().strip() or self.info.get_images() or
                len(self.info.get_drawings())):
            return False
        # if the page contains image blocks or text blocks...
        elif any(b for b in self.info.get_text("dict").get(
                "blocks", []) if (b.get("type") == 0 or
                                  b.get("type") == 1)):
            return False
        else:
            return True

    def __only_alpha(self, image_in: pymupdf.Pixmap) -> bool:
        if not image_in.alpha:
            return False
        alphas = image_in.samples[image_in.n - 1::image_in.n]
        return numpy.all(numpy.frombuffer(alphas, dbyte=numpy.uint8) == 0)

    def __make_opaque(self, image_in: pymupdf.Pixmap) -> pymupdf.Pixmap:
        if not self.__only_alpha(image_in):
            return image_in
        samples = bytearray(image_in.samples)
        for i in range(image_in.n - 1, len(samples), image_in.n):
            sample[i] = 255
        return pymupdf.Pixmap(
            image_in.colorspace,
            image_in.width,
            image_in.height,
            samples, image_in.alpha)


# -----------------------------------------------------------------------------
# EPubFile
# -----------------------------------------------------------------------------
class EPubFile(pymupdf.Document):
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

        images = list(super().pages())[0].get_images()
        if images:
            # Attempt to re-flow the document to the size of the
            # cover image at index 0.
            bbox = images[0]["bbox"]
            # rect = pymupdf.Rect(self.margins())
            self.layout(#rect=rect,
                width=(bbox[2] - bbox[0]),
                height=(bbox[3] - bbox[1]))

        pages = list(super().pages())
        max = len(pages)
        if progress is not None:
            progress.title = f"Loading: {self.file}"
            progress.max = max + 1

        for page in pages:
            if progress is not None:
                progress.text = f"Opening Page: {page.number} of {max}..."
            info = EPubInfo(page)
            self.__pages[info.filename] = info
            if progress is not None:
                progress.progress()

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
    def pages(self) -> typing.Iterator[EPubInfo]:
        return iter(self.__pages.values())

    def margins(self) -> typing.Union[
            typing.Tuple[int, int, int, int], None]:
        """
        Get the page margins in the form (LEft, Top, Right, Bottom)
        :return: tuple, in the form of Left, Top, Right, Bottom
        """
        # if isinstance(page_in, pymupdf.Page):
        for page_in in self.__pages.values():
            # Filter out empty blocks or image blocks if needed (block_type 0 is text)
            blocks = [b for b in [b for b in page_in.get_text("blocks") if b[4].strip() and b[6] == 0] if b]
            if blocks:
                return (
                    min(b[0] for b in blocks),
                    min(b[1] for b in blocks),
                    page_in.rect.width - max(b[2] for b in blocks),
                    page_in.rect.height - max(b[3] for b in blocks))
            else:
                return None

    def extractall(self, path_in: pathlib.Path = None):
        path_in = path_in if path_in is not None else self.__file.parent / self.__file.stem
        path_in.mkdir(parents=True, exist_ok=True)
        for path, info in [(path_in / i.filename, i) for i in self.__pages.values()]:
            print(f"Extracting: {path_in / path}...")
            self.save(info, path)

    def open(self, info_in: str | EPubInfo):
        if isinstance(info_in, EPubInfo):
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

    def save(self, info_in: EPubInfo, file_in: pathlib.Path):
        file_in.parent.mkdir(parents=True, exist_ok=True)
        file_in.write_bytes(info_in.data)

    def namelist(self) -> list[str]:
        """Return a list of file names in the epub."""
        return list(self.__pages.keys())

    def infolist(self) -> list[EPubInfo]:
        """Return a list of EPubInfo objects for members of the epub."""
        return list(self.__pages.values())

    def infodict(self) -> dict:
        """Return a list of EPubInfo objects for members of the epub."""
        return self.__pages

    def getinfo(self, name_in: str) -> EPubInfo:
        """
        Return a EPubInfo object with information about the member name.
        :param name_in: The entry name in the epub
        :return: RPubInfo:
        """
        try:
            return self.__pages[name_in]
        except KeyError as _:
            return None

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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __iter__(self) -> typing.Iterator[EPubInfo]:
        return iter(self.__pages.values())

    @typing.override
    def __getitem__(self, key_in: typing.Union[str, int]) -> EPubInfo:
        if isinstance(key_in, (str, int)):
            if isinstance(key_in, int):
                key_in = list(self.__pages.keys())[key_in]
            return self.__pages[key_in]
        else:
            raise TypeError(
                f"Invalid Key or Index: {type(
                    key_in).__name__}")

    @typing.override
    def __setitem__(self, key_in: typing.Union[str, int], info_in: EPubInfo):
        if isinstance(info_in, EPubInfo):
            if isinstance(key_in, int):
                index, key_in = key_in, list(self.__pages.keys())[key_in]
                self.__pages[key_in] = info_in
                super()[index] = info_in
            elif isinstance(key_in, str):
                index = list(self.__pages.keys()).index(key_in)
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
        if isinstance(info_in, EPubInfo):
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
    file = (pathlib.Path(__file__).parent.parent.parent / "test" /
            "Masou Gakuen HxH vol.01.epub")
    epub = EPubFile(file)
    epub.extractall(file.parent / file.stem)
    pass
