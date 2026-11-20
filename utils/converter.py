#!/usr/bin/env python3
import pathlib, re, argparse, os
from ..comics import comic


# =============================================================================
# Converter
# =============================================================================
class Converter:
    def __init__(self, path_in: pathlib.Path, path_out: pathlib.Path,
                 extension_in: str = None, strip_in: bool = None,
                 delete_in: bool = False):
        self.__path_in = path_in.resolve()
        if not self.__path_in.exists():
            raise ValueError(
                f"Invalid Path: {self.__path_in}")

        self.__path_out = path_out.resolve()
        if self.__path_out.is_dir():
            self.__path_out.mkdir(parents=True, exist_ok=True)
        else:
            self.__path_out.parent.mkdir(parents=True, exist_ok=True)

        if self.__path_out.is_file():
            self.__extension = self.__path_out.suffix
        else:
            self.__extension = extension_in
        if (self.__extension is not None and
                self.__extension not in list(comic.Comic.TYPES.keys()) + ["auto"]):
            raise ValueError(
                f"Error: Invalid Extension: {self.__extension}")

        self.__strip = strip_in
        self.__delete = delete_in
        self.__total = 0

    def convert(self):
        self.__total = 0
        if self.__path_in.is_dir():
            self.__convert_directory(self.__path_in)
        elif self.__path_in.is_file():
            if self.__strip:
                self.__strip_retromag(self.__path_in)
            else:
                self.__convert_file(self.__path_in)
        print(f"Total Saved: {self.__total} Byte(s)")

    def __convert_directory(self, path_in: pathlib.Path = None):
        path_in = path_in.resolve() if path_in is not None else self.__path_in
        print(f"Converting Directory: {path_in}...")
        for path in sorted([d for d in path_in.iterdir() if d.is_dir()]):
            self.__convert_directory(path)
        for path in sorted([f for f in path_in.iterdir() if f.suffix in comic.Comic.TYPES.keys()]):
            if self.__strip:
                self.__strip_retromag(path)
            else:
                self.__convert_file(path)

    def __strip_retromag(self, file_in: pathlib.Path):
        print(f"{"-"*80}\n{file_in}\n{"-"*80}")
        file_out = self.__get_file_out(file_in)
        if file_in == file_out:
            file_in = file_in.with_suffix(".old" + file_in.suffix)
            file_out.replace(file_in)
        print(f"Stripping: {file_out}")
        try:
            with comic.Comic(file_in).archive('r') as archive_in, comic.Comic(file_out).archive('w') as archive_out:
                for item in archive_in.infolist():
                    if (re.search(r"x-x-retromags", item.filename) or
                            pathlib.Path(item.filename).name.startswith(".")):
                        print(f"Removing: {item.filename}")
                    else:
                        archive_out.writestr(item, archive_in.read(item.filename))
            if self.__delete:
                print(f"Deleting: {file_in}")
                file_in.unlink()
        except Exception as error:
            file_in.replace(file_out)
            raise error
        finally:
            print(f"{"-" * 80}\n")

    def __convert_file(self, file_in: pathlib.Path):
        extension = self.__extension if self.__extension is not None else file_in.suffix
        print(f"{"-"*80}\n{file_in}\n{"-"*80}")
        file_out = self.__get_file_out(file_in)
        if file_in != file_out:
            print(f"Converting: {file_in}\n"
                  f"To:         {file_out}")
            with comic.Comic(file_in).archive("r") as archive_in, comic.Comic(file_out).archive("w") as archive_out:
                for item in archive_in.infolist():
                    print(f"Adding: {item.filename}")
                    data = archive_in.read(item.filename)
                    if os.path.basename(item.filename) in archive_out.namelist():
                        archive_out.writestr(f"duplicates/{os.path.basename(item.filename)}", data)
                    else:
                        archive_out.writestr(os.path.basename(item.filename), data)

            src_size, dst_size = file_in.stat().st_size, file_out.stat().st_size
            if self.__delete:
                print(f"Deleting: {file_in}")
                file_in.unlink()

            print(f"Src Size: {src_size}\n"
                  f"Dst Size: {dst_size}\n"
                  f"Saved:    {src_size - dst_size} Byte(s)")
            self.__total += (src_size - dst_size)
            print("Done.")
        else:
            print(f"Skipping: {file_in}")
        print(f"{"-" * 80}\n")

    def __get_file_out(self, file_in: pathlib.Path) -> pathlib.Path:
        if self.__path_out.is_dir():
            if self.__path_in.is_dir():
                return self.__path_out / pathlib.Path(
                    os.path.relpath(
                        f"{file_in}", f"{self.__path_in}")).with_suffix(
                    self.__extension).resolve()
            else:
                return self.__path_out / f"{self.__path_in.stem}{self.__extension}"
        else:
            return self.__path_out.with_suffix(self.__extension)
