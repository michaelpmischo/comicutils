#!/usr/bin/env python3
import subprocess, sys, pathlib, shutil, io, PIL.Image
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent.parent}")
    from comicutils.utils import packages
else:
    from ...utils import packages
packages.require({
    "rarfile": ("unrar.cffi.rarfile", "unrar-cffi")},
    __name__)
# <<< --------------------------- ENG IMPORTS ---------------------------- >>>


# -----------------------------------------------------------------------------
# Magic Numbers
# -----------------------------------------------------------------------------
MAGICS = (
    (0, 7, b'Rar!\x1A\x07\x00', "rar"),
    (0, 8, b'Rar!\x1A\x07\x01\x00', "rar5"))
MAGIC = lambda f: tuple(cmp for off, n, magic, cmp in MAGICS if (
    pathlib.Path(f).read_bytes()[off:off+n] == magic))


def is_rarfile(path_in: pathlib.Path | str) -> bool:
    return bool(MAGIC(path_in))


# -----------------------------------------------------------------------------
# RarInfo
# -----------------------------------------------------------------------------
# Define RarInfo Class in this module.
RarInfo = rarfile.RarInfo


# -----------------------------------------------------------------------------
# RarFile
# -----------------------------------------------------------------------------
class RarFile(rarfile.RarFile):
    __COMMAND = 'rar' if sys.platform.startswith('linux') else r'C:\Program Files\WinRAR\Rar.exe'
    __ECHO = "echo"
    __APPEND = ".append"
    __OPTIONS = {
        "ADD": "u",
        "CWD": "-w",
        "DATA_IN": "-si",
        "DELETE": "d",
        "NO_PATH": "-ep",
        "RENAME": "rm",
        "STORE": "-m5"}

    def __init__(self, file_in: pathlib.Path, **args_in):
        progress = args_in.pop("progress") if "progress" in args_in.keys() else None
        self.__file, self.__first_write, self.__mode = (file_in, True,
            args_in.pop('mode') if 'mode' in args_in.keys() else 'r')
        if not pathlib.Path(self.__COMMAND).exists():
            raise rarfile.RarFileError(
                "No Tool Present: Please install rar/WinRAR...")
        try:
            super().__init__(file_in, **args_in)
        except Exception as _:
            pass

    def extract(self):
        # TODO: Finish this function.
        pass

    def write(self, file_in: str | pathlib.Path, arcname: str=None, compress_type=None):
        if self.__mode == "r":
            raise ValueError(
                f"Cannot Write to RarFile opened with mode=\"{self.__mode}\'")
        try:
            self.__check_first_write()
            self.__execute([
                self.__COMMAND,
                self.__OPTIONS["ADD"],
                self.__OPTIONS["STORE"],
                self.__OPTIONS["NO_PATH"],
                f"{self.__file}",
                f"{file_in}"])
            if arcname is not None:
                self.__execute([
                    self.__COMMAND,
                    self.__OPTIONS["RENAME"],
                    f"{file_in}",
                    f"{arcname}"])
        except subprocess.CalledProcessError as eerror:
            print(eerror.stdout)
            print(eerror.stderr)

    def writestr(self, info_in: rarfile.RarInfo | str, data: bytes,
                 compress_type=None, compresslevel=None):
        if self.__mode == "r":
            raise ValueError(
                f"Cannot Write to RarFile opened with mode=\"{self.__mode}\'")
        if isinstance(info_in, str):
            file_in = info_in
        else:
            file_in = info_in.filename
        command = [
            self.__COMMAND,
            self.__OPTIONS["ADD"],
            self.__OPTIONS["STORE"],
            self.__OPTIONS["NO_PATH"],
            f"{self.__OPTIONS["DATA_IN"]}'{file_in}'",
            f"{self.__file}"]
        self.__check_first_write()
        process = subprocess.Popen(command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)
        stdout, stderr = process.communicate(f"{str(data)}")
        if process.returncode != 0:
            print(f"Out: {stdout}")
            print(f"Err: {stderr}")
            raise subprocess.CalledProcessError(
                retcode=process.retcode,
                cdd=command,
                output=stdout,
                stderr=stderr)

    def mkdir(self, info_in: rarfile.RarInfo | str, mode=511):
        if self.__mode == "r":
            raise ValueError(
                f"Cannot Write to RarFile opened with mode=\"{self.__mode}\'")
        if isinstance(info_in, str):
            archname = info_in
        else:
            archname = info_in.filename
        directory = pathlib.Path(archname)
        directory.mkdir(parents=True, exist_ok=False)
        self.__execute([
            self.__COMMAND,
            self.__OPTIONS["ADD"], self.__OPTIONS["STORE"], self.__OPTIONS["NOPATH"],
            f"{self.__file}",
            f"{directory}"])
        shutil.rmtree(directory)

    def delete(self, file_in: str):
        try:
            if file_in is self.namelist():
                command = [
                    self.__COMMAND,
                    self.__OPTIONS["DELETE"],
                    self.__OPTIONS["STORE"],
                    f"{self.__file}",
                    f'{file_in}']
                self.__execute(command)
        except AttributeError as _:
            pass

    def __execute(self, command_in: str | list[str]):
        command_in, shell = (
            [command_in], True) if (
            isinstance(command_in, str)) else (
            [f"{p}" for p in command_in], False)
        try:
            result = subprocess.run(
                command_in,
                capture_output=True,
                text=True,
                shell=shell)
        except subprocess.CalledProcessError as error:
            print(error.stdout)
            print(error.stderr)
            raise error
        finally:
            pass

    def __check_first_write(self):
        if self.__first_write and self.__mode == "w":
            self.__file.unlink(missing_ok=True)
            self.__first_write = False
    #
    # @property
    # def pages(self) -> list:
    #     return list((i.filename, PIL.Image.open(
    #         io.BytesIO(self.open(i).read()))) for i in self.infolist() if (
    #             pathlib.Path(i.filename).suffix in
    #             PIL.Image.registered_extensions()))

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getitem__(self, index_in: int) -> rarfile.RarInfo:
        return self.infolist()[index_in]


if __name__ == '__main__':
    file = (pathlib.Path(__file__).parent.parent.parent /
            "test" / "Ay-Papi 1.cbr")
    rar = RarFile(file, mode='r')
    rar.extractall(pathlib.Path(__file__).parent / file.stem)


    rar = RarFile(file, mode="w")
    for file in [f for f in (pathlib.Path.cwd() / "1").iterdir() if f.is_file() and f.suffix in [".jpg", ".png"]]:
        print(f"Adding: {file}")
        rar.write(file)


