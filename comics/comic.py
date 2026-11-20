#!/usr/bin/env python3
import sys, pathlib, re, os, zipfile, io, PIL.Image, tkinter

# For testing..
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.comics import book, zip, rar, sevenzip, tarball, epub2, pdf
    from comicutils.gui import popup
    from comicutils.utils import resolver
else:
    from . import book, zip, rar, sevenzip, tarball, epub2, pdf
    from ..gui import popup
    from ..utils import resolver


# -----------------------------------------------------------------------------
# Comic
# -----------------------------------------------------------------------------
class Comic:
    ICONS = resolver.icon_root()

    TYPES = {
        ".epub": [
            {
                "magic": b"PK",  # .zip (PK ZIP)
                "constructor": {
                    "call": epub2.EPubFile,
                    "args": {},
                },
                "extreq": True,
                "sort": False,
                "mode": ""
            },
        ],
        ".pdf": [
            {
                "magic": b"%PDF",  # pdf standard
                "constructor": {
                    "call": pdf.PdfFile,
                    "args": {},
                },
                "extreq": False,
                "sort": False,
                "mode": ""
            },
        ],
        ".cbz": [
            {
                "magic": b"PK", # .zip (PK ZIP)
                "constructor": {
                    "call": zip.ZipFile,
                    "args": {
                        "compression": zipfile.ZIP_DEFLATED,
                        "allowZip64": True,
                        "compresslevel": 9,
                    },
                },
                "extreq": False,
                "sort": True,
                "mode": ""
            },
        ],
        ".cbr": [
            {
                "magic": b"Rar!", # .rar (RAR)
                "constructor": {
                    "call": rar.RarFile,
                    "args": {},
                },
                "extreq": False,
                "sort": True,
                "mode": ""
            },
        ],
        ".cb7": [
            {
                "magic": b"7z",  # .zip (PK ZIP)
                "constructor": {
                    "call": sevenzip.SevenZipFile,
                    "args": {
                        "compression": sevenzip.ZIP_LZMA2,
                    },
                },
                "extreq": False,
                "sort": True,
                "mode": ""
            },
        ],
        ".cbt": [
            {
                "magic": b'\xfd7zX', # .xz
                "constructor": {
                    "call": tarball.TarFile,
                    "args": {},
                },
                "extreq": False,
                "sort": True,
                "mode": ":xz",
            },
            {
                "magic": b'\x1f\x8b',  # .gz (gzip)
                "constructor": {
                    "call": tarball.TarFile,
                    "args": {},
                },
                "extreq": False,
                "sort": True,
                "mode": ":gz",
            },
            {
                "magic": b"BZh",  # .zip (PK ZIP)
                "constructor": {
                    "call": tarball.TarFile,
                    "args": {},
                },
                "extreq": False,
                "sort": True,
                "mode": ":bz2",
            },
        ],
    }

    __SINGLE_RATIO = 1.1

    def __init__(self, file_in: str | pathlib.Path, root_in: tkinter.Misc = None):
        (self.__pages, self.__page, self.__pairs, self.__file, self.__load_id,
         self.__loading, self.__root, self.__loaded) = (
            [], 0, [], file_in.resolve() if isinstance(
                file_in, pathlib.Path) else pathlib.Path(file_in).resolve(), None,
            tkinter.BooleanVar(root_in, value=False) if root_in is not None else None,
            root_in, False)
        if self.__file.exists():
            if not self.__file.is_file():
                raise ValueError(
                    f"Error: Invalid File: {self.__file}")
            else:
                self.__fix_extension()
            print(f"Magic: {self.__magic()}")
            self.load()
        else:
            self.archive("w")

    @property
    def file(self) -> pathlib.Path:
        return self.__file

    # @property
    # def pages(self) -> list[pages.Page]:
    #     return self.__pages

    @property
    def pages(self) -> list[PIL.Image.Image]:
        return [i for f, i in self.__pages]

    @property
    def files(self) -> list[str]:
        return [f for f, i in self.__pages]

    @property
    def pairs(self) -> list[tuple]:
        return self.__pairs

    @property
    def number_of_pages(self) -> int:
        return len(self.__pages)

    def page(self, page_in: int) -> PIL.Image.Image:
        if 0 <= page_in < self.number_of_pages:
            return self.__pages[page_in][1]
        else:
            raise ValueError(
                f"Page Out of Bounds: {page_in}")

    def delete_page(self, page_in: str | int, progress_in: popup.ProgressBar, sem_in: tkinter.BooleanVar = None):
        try:
            # Raise an exception if modifying a RAR file.
            if rar.is_rarfile(self.__file):
                raise NotImplementedError(
                    f"Modifying RAR Compression Doesn't Work, Yet. "
                    f"I don't want to ruin your files.")
            page_in = list(zip(*self.__pages))[0].index(page_in) if (
                isinstance(page_in, str)) else page_in
            self.__pages.pop(page_in)
            if progress_in is not None:
                progress_in.max = len(self.__pages) * 2
            with self.archive("w") as arch:
                try:
                    for i, (file, page) in enumerate(self.__pages):
                        if progress_in is not None:
                            progress_in.text = f"Compressing: {file}..."
                        data = io.BytesIO()
                        page.save(data, "JPEG", quality=80)
                        arch.writestr(file, data.getvalue())
                        if progress_in is not None:
                            progress_in.progress(i)
                finally:
                    self.close(arch)
        finally:
            self.__loaded = False
            self.load()
            if progress_in is not None:
                progress_in.stop()
            if sem_in is not None:
                sem_in.set(not sem_in.get())

    def write_pages(self, pages_in: list[pathlib.Path],
                    progress_in: popup.ProgressBar = None):
        if isinstance(pages_in, list):
            with self.archive("w") as archive:
                try:
                    for i, page in enumerate(pages_in):
                        if progress_in is not None:
                            progress_in.text = f"Adding: {page.name}"
                        self.add_page(page, archive)
                        if progress_in is not None:
                            progress_in.progress(i)
                finally:
                    self.close(archive)
                    self.__loaded = False
                    self.load()

        else:
            raise ValueError(
                f"Error: Invalid Pages: {pages_in}")

    def add_page(self, file_in: pathlib.Path, archive_in: any = None):
        if isinstance(file_in, pathlib.Path):
            if file_in.exists() and file_in.suffix in PIL.Image.registered_extensions():
                try:
                    archive = archive_in if archive_in is not None else self.archive("a")
                    try:
                        archive.write(f"{file_in.resolve()}", arcname=file_in.name)
                    finally:
                        if archive_in is None:
                            self.close(archive)
                            self.load()
                except TypeError as _:
                    pass
        else:
            raise ValueError(
                f"Error: File Doesn't Exist: {file_in}")

    def extract(self, path_out: str | pathlib.Path = None):
        path_out = pathlib.Path.cwd() / "tmp" if path_out is None else (
            path_out.resolve() if isinstance(
                path_out, pathlib.Path) else
            pathlib.Path(path_out).resolve())
        path_out.mkdir(parents=True, exist_ok=True)
        print(f"Extracting:  {self.__file}")
        try:
            with self.archive() as archive:
                try:
                    archive.extractall(path_out)
                finally:
                    self.close(archive)
        except TypeError as _:
            pass

    def compress(self, path_in: str | pathlib.Path = None):
        path_in = pathlib.Path.cwd() if path_in is None else (
            path_in.resolve() if isinstance(
                path_in, pathlib.Path) else
            pathlib.Path(path_in).resolve())
        print(f"Compressing: {self.__file}")
        try:
            with self.archive("w") as archive:
                try:
                    for file in sorted([f for f in path_in.iterdir() if (
                            self.is_image(f))], key=self.natural):
                        archive.write(file, arcname=file.name)
                finally:
                    self.close(archive)
        except TypeError as _:
            pass

        # Update the comic data.
        self.load()

    def is_image(self, file_in: str | pathlib.Path) -> bool:
        try:
            with self.archive() as archive:
                try:
                    if file_in in archive.namelist():
                        PIL.Image.open(io.BytesIO(archive.open(file_in).read())).verify()
                    else:
                        PIL.Image.open(file_in).verify()
                finally:
                    self.close(archive)
            return True
        except (IOError, SyntaxError) as _:
            return False

    def load(self):
        if not self.__loaded:
            if self.__root is not None:
                self.__loading.set(True)
                bar = popup.ProgressBar(self.__root, "Loading...", "Loading...")
                if self.__load_id is not None:
                    self.__root.after_cancel(self.__load_id)
                self.__load_id = self.__root.after(50, self.__load, bar)
                self.__root.wait_variable(self.__loading)
                bar.stop()
            else:
                self.__load()

    def __load(self, progress_in: popup.ProgressBar = None):
        self.__pages, self.__pairs, (_, config) = [], [], self.config
        with self.archive() as archive:
            # self.__pages = book.Book(archive)
            self.__pages = archive.pages
            if progress_in is not None:
                progress_in.max = len(self.__pages)
            if config["sort"]:
                self.__pages = sorted(self.__pages, key=self.basic)
            try:
                pair = ()
                for i, (name, page) in enumerate(self.__pages):
                    if progress_in is not None:
                        progress_in.text = f"Loading: {name} ..."
                    pair = self.__add_pair(i, pair, page)
                    if progress_in is not None:
                        progress_in.progress()
                if len(pair) > 0:
                    self.__pairs.append(pair)  # + (None,))
                self.__loaded = True

            except IOError as _:
                pass
            finally:
                self.close(archive)
                if progress_in is not None:
                    progress_in.stop()
                if self.__root is not None:
                    self.__loading.set(False)

    @staticmethod
    def natural(text_in: str | pathlib.Path):
        return [int(c) if c.isdigit() else c.lower() for c in
                re.split(r'(\d+)', f"{text_in}")]

    @staticmethod
    def basic(page_in: tuple):
        return [int(c) if c.isdigit() else c.lower() for c in
                re.split(r'(\d+)', f"{page_in[0]}")]

    @staticmethod
    def close(archive_in):
        try:
            archive_in.close()
        except AttributeError as _:
            pass

    @property
    def extension(self) -> str:
        return self.config[0]

    @property
    def config(self) -> tuple[str, dict]:
        magic_in = self.__magic()
        for extension, infos in self.TYPES.items():
            for info in infos:
                if info["extreq"]:
                    if extension == self.__file.suffix and magic_in.startswith(info["magic"]):
                        return extension, info
                elif magic_in.startswith(info["magic"]):
                    return extension, info

        raise ValueError(
            f"Error: Unknown File Type: {self.__file}")

    def archive(self, mode_in: chr = "r") -> any:
        extension, config = self.config
        try:
            return config["constructor"]["call"](
                self.__file,
                mode=f"{mode_in}{config["mode"]}",
                **config["constructor"]["args"])
        except tarball.tarfile.ReadError as _:
            if mode_in == "w":
                self.__file.unlink()
                return self.archive(mode_in)
            else:
                return None

    def __fix_extension(self):
        extension = self.extension
        if extension != self.__file.suffix:
            file = self.__file.with_suffix(extension)
            self.__file.rename(file)
            self.__file = file

    def __add_pair(self, page_in: int, pair_in: tuple, image_in: PIL.Image.Image) -> tuple:
        if page_in == 0 or not isinstance(image_in, PIL.Image.Image):
            self.__pairs.append((page_in,)) #(None, page_in))
            return ()
        elif image_in.width >= (image_in.height * self.__SINGLE_RATIO):
            if len(pair_in) > 0:
                self.__pairs.append(pair_in)
            self.__pairs.append((page_in,))
            return ()
        elif len(pair_in) > 1:
            self.__pairs.append(pair_in)
            return (page_in,)
        else:
            return pair_in + (page_in,)

    def __magic(self, offset_in: int = 0):
        if self.__file.exists():
            with open(self.__file, "rb") as file:
                try:
                    file.seek(offset_in, os.SEEK_SET)
                    return file.read(4)
                finally:
                    file.close()
        else:
            return self.TYPES[self.__file.suffix][0]["magic"]

    def __getitem__(self, index_in: int) -> PIL.Image.Image:
        return self.page(index_in)


if __name__ == '__main__':
    root = tkinter.Tk()
    root.geometry("1200x1200")
    _f = pathlib.Path(__file__).parent.parent / "test" / "AX3LBRAVO - Damsels in Distress.cbz"
    _f = pathlib.Path(__file__).parent.parent / "test" / "Ay-Papi 1.cbr"
    _f = pathlib.Path(__file__).parent.parent / "test"/ "Masou Gakuen HxH vol.01.epub"
    _C = Comic(_f, root)
    _C.load()
    # comic = epub.EPubFile(file, mode='r')
    pass