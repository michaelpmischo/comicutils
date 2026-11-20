#!/usr/bin/env python3
import zipfile, pathlib, io, typing, PIL.Image


ZipInfo = zipfile.ZipInfo

class ZipFile(zipfile.ZipFile):

    def __init__(self, file, mode, compression=zipfile.ZIP_DEFLATED, **args_in):
        super().__init__(file, mode, compression, **args_in)

    @property
    def pages(self) -> list:
        return list((i.filename, PIL.Image.open(
            io.BytesIO(self.open(i).read()))) for i in self.infolist() if (
                pathlib.Path(i.filename).suffix in
                PIL.Image.registered_extensions()))
