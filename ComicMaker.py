#!/usr/bin/env python3
import pathlib, zipfile, re, argparse, os, shutil, subprocess, PIL.Image


# =============================================================================
# ComicMaker
# =============================================================================
class ComicMaker:
    PDF_EXTRACT = ["pdftoppm", "-r", "300", "-png", "-aa", "yes"]
    IMG_EXTENSIONS = PIL.Image.registered_extensions()
    COMICS = [".cbz", ".cbr", ".cb7", ".cbt"]

    def __init__(self, path_in: pathlib.Path | str, path_out: pathlib.Path | str, force_in: bool = False):
        self.__path_in = (path_in if isinstance(path_in, pathlib.Path) else pathlib.Path(path_in)).resolve()
        if not self.__path_in.exists():
            raise ValueError(
                f"ERROR: {self.__path_in} doesn't exits!")
        if path_out is not None:
            self.__path_out = (path_out if isinstance(path_out, pathlib.Path) else pathlib.Path(path_out)).resolve()
            self.__path_out.mkdir(parents=True, exist_ok=True)
        else:
            self.__path_out = None
        self.__force = force_in

    def make(self):
        self.__handle_pdfs(self.__path_in)
        if self.__has_dirs(self.__path_in):
            self.__make_dir(self.__path_in)
        elif not self.__has_comics(self.__path_in):
            self.__make_comic(self.__path_in)

    def __make_dir(self, path_in: pathlib.Path):
        for path in [p for p in path_in.iterdir() if p.is_dir()]:
            ComicMaker(path, self.__path_out, self.__force).make()

    def __make_comic(self, path_in: pathlib.Path):
        path = path_in.parent if self.__path_out is None else self.__path_out
        comic = path / f'{path_in.name}.cbz'
        if not comic.exists() or self.__force:
            print(f"{'-'*80}\n{path_in.stem}\n{'-'*80}")
            path = self.__extract_pdf(path_in) if path_in.suffix == ".pdf" else path_in
            print(f"Creating: {comic}")
            with zipfile.ZipFile(comic, mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                try:
                    for file in sorted([f for f in path.iterdir() if (
                            f.is_file() and f.suffix in self.IMG_EXTENSIONS)],
                                    key=self.__natural):
                        print(f"Adding: {file}")
                        archive.write(f"{file}", arcname=file.name)
                finally:
                    archive.close()

            if path != path_in:
                shutil.rmtree(path)

            print(f"{'-'*80}\n")

        else:
            print(f"WARNING: {comic} already exists. Use the -f "
                  f"option to force a remake of this comic "
                  f"from source files.")

    def __handle_pdfs(self, path_in: pathlib.Path):
        for file in [f for f in path_in.iterdir() if f.is_file() and f.suffix == ".pdf"]:
            self.__make_comic(file)

    def __extract_pdf(self, file_in: pathlib.Path) -> pathlib.Path:
        path_out = file_in.parent / file_in.stem
        path_out.mkdir(parents=True, exist_ok=True)
        command = self.PDF_EXTRACT + [f"{file_in}", file_in.stem]
        print(' '.join(command))
        try:
            subprocess.run(command, check=True, cwd=f"{path_out}")
        except subprocess.CalledProcessError as error:
            print(f"STDOUT: {error.stdout}")
            print(f"STDERR: {error.stderr}")
            raise error
        return path_out

    @staticmethod
    def __natural(path_in: pathlib.Path):
        # Splits the string into text and digits. Converts digits to ints.
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', f"{path_in}")]

    def __has_comics(self, path_in: pathlib.Path) -> bool:
        return any(
            f for f in path_in.iterdir() if (
                    f.is_file() and f.suffix in self.COMICS))

    @staticmethod
    def __has_dirs(path_in: pathlib.Path) -> bool:
        return any(p for p in path_in.iterdir() if p.is_dir())

    def __images(self, path_in: pathlib.Path) -> list[pathlib.Path]:
        return sorted(
            [f for f in path.iterdir() if (
                f.is_file() and f.suffix in self.IMG_EXTENSIONS)],
            key=self.__natural)

    @staticmethod
    def __pdfs(path_in: pathlib.Path) -> list[pathlib.Path]:
        return [f for f in path_in.iterdir() if (
                f.is_file() and f.suffix == ".pdf")]


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Comic Maker")
    parser.add_argument(
        "-f",
        "--force",
        action='store_true',
        help="force generation of new comics from "
             "source even if they already exist.")

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="path to place the output files. default to same path as input.")

    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=f"{pathlib.Path.cwd()}",
        help="path to files. each comic should be "
             "separated into individual directories.")
    args = parser.parse_args()
    args.path = pathlib.Path(args.path).resolve()
    args.output = pathlib.Path(args.output) if args.output is not None else None
    maker = ComicMaker(args.path, args.output, args.force)
    maker.make()

