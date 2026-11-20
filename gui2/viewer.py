#!/usr/bin/env python3
import sys, pathlib, PIL.Image, PIL.ImageTk, PIL.ImageOps, tkinter, tkinter.ttk, tkinter.filedialog

if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.utils import resolver, converter
    from comicutils.comics2 import book
    from comicutils.gui2 import popup, toolbars, readframe, canvasframe #, webframe
else:
    from ..utils import resolver, converter
    from ..comics2 import book
    from . import popup, toolbars, readframe, canvasframe #, webframe


# =============================================================================
# ComicViewer
# =============================================================================
class ComicViewer(tkinter.Tk):
    ICONS = resolver.icon_root()

    def __init__(self, path_in: str | pathlib.Path = None):
        super().__init__()
        self.title("Comic Viewer")
        self.minsize(1000, 800)
        self.__load_id = None

        self.__icon = PIL.ImageTk.PhotoImage(
            PIL.Image.open(self.ICONS / "icon2.jpg"))
        self.iconphoto(True, self.__icon)

        self.columnconfigure(0, weight=1)
        self.__toolbar = toolbars.ViewerToolBar(self, font=("Impact", 16)) #, font=("Bangers", 16))
        self.__toolbar.grid(row=0,column=0, sticky=tkinter.EW)

        self.__viewer = None
        self.rowconfigure(1, weight=1)
        self.__canvasframe = canvasframe.CanvasReadFrame(self, None) #, font=("Bangers", 13))
        # self.rowconfigure(1, weight=1)
        # self.__webframe = webframe.WebReadFrame(self, None) #, font=("Bangers", 13))

        self.__status = tkinter.StringVar(self, value="Ready...")
        self.__statusbar = tkinter.Label(
            self, textvariable=self.__status, bd=2,
            anchor=tkinter.W, relief=tkinter.SUNKEN)
        self.__statusbar.grid(row=2, column=0, sticky=tkinter.EW)

        # Subscribe to events
        self.__toolbar.comic_control.subscribe(
            "opencomic", self.__open)
        self.__toolbar.comic_control.subscribe(
            "prevcomic", self.__load_prev)
        self.__toolbar.comic_control.subscribe(
            "nextcomic", self.__load_next)

        # Initially, setup the canvas reader.
        self.__subscribe_reader(
            self.__canvasframe)

        self.lift()
        if path_in is not None:
            self.load(path_in)
        self.mainloop()

    def load(self, path_in: pathlib.Path, bar: popup.ProgressBar = None):
        if self.__load_id is not None:
            self.after_cancel(self.__load_id)
        bar = popup.ProgressBar(self, "Loading...") if bar is None else bar
        self.__load_id = self.after(25, self.__load, path_in, bar)

    def __subscribe_reader(self, frame_in: readframe.ReadFrame):
        if frame_in is not None and not frame_in.winfo_manager():
            self.__unsubscribe_reader(self.__viewer)
            frame_in.grid(row=1, column=0, sticky=tkinter.NSEW)

            # Subscribe to events
            frame_in.context.subscribe("open", self.__open)
            frame_in.context.subscribe("add", self.__add_page)
            frame_in.context.subscribe("delete", self.__delete_page)
            frame_in.context.subscribe("convert", self.__convert)
            frame_in.context.subscribe("from-dir", self.__make_from_directory)
            frame_in.context.subscribe("from-files", self.__make_from_files)
            frame_in.context.subscribe("extract", self.__extract)
            frame_in.context.subscribe("exit", self.destroy)

            self.__toolbar.layout_control.subscribe(
                "single", lambda: setattr(
                    frame_in.context, "double", False))
            self.__toolbar.layout_control.subscribe(
                "double", lambda: setattr(
                    frame_in.context, "double", True))
            self.__toolbar.layout_control.subscribe(
                "vertical", lambda: setattr(
                    frame_in, "orientation", readframe.VERTICAL_SCROLL))
            self.__toolbar.layout_control.subscribe(
                "horizontal", lambda: setattr(
                    frame_in, "orientation", readframe.HORIZONTAL_SCROLL))
            self.__toolbar.layout_control.subscribe(
                "manga", lambda: frame_in.set_manga(
                    self.__toolbar.layout_control.manga))

            if hasattr(frame_in, "fit"):
                self.__toolbar.view_control.subscribe("fit", frame_in.fit)
            self.__toolbar.view_control.subscribe("zoom+", frame_in.zoom_in)
            self.__toolbar.view_control.subscribe("zoom-", frame_in.zoom_out)

            self.__toolbar.comic_control.subscribe(
                "contents", frame_in.goto,
                where_in=frame_in.CONTENTS)
            self.__toolbar.comic_control.subscribe(
                "firstpage", frame_in.goto,
                where_in=frame_in.BEGINNING)
            self.__toolbar.comic_control.subscribe(
                "prevpage", frame_in.goto,
                where_in=frame_in.PREVIOUS)
            self.__toolbar.comic_control.subscribe(
                "setpage", lambda: frame_in.goto(
                frame_in.PAGE, self.__toolbar.comic_control.pages))
            self.__toolbar.comic_control.subscribe(
                "nextpage", frame_in.goto,
                where_in=frame_in.NEXT)
            self.__toolbar.comic_control.subscribe(
                "lastpage", frame_in.goto,
                where_in=frame_in.END)
            self.__toolbar.comic_control.subscribe(
                "back", frame_in.go_back)

            frame_in.subscribe("page", self.__status_change)
            frame_in.subscribe("scale", self.__status_change)
        self.__viewer = frame_in
        self.pages = []

    def __unsubscribe_reader(self, frame_in: readframe.ReadFrame = None):
        if frame_in is not None and frame_in.winfo_manager():
            frame_in.comic = None
            frame_in.grid_forget()

            # Subscribe to events
            frame_in.context.unsubscribe("open", self.__open)
            frame_in.context.unsubscribe("add", self.__add_page)
            frame_in.context.unsubscribe("delete", self.__delete_page)
            frame_in.context.unsubscribe("convert", self.__convert)
            frame_in.context.unsubscribe("from-dir", self.__make_from_directory)
            frame_in.context.unsubscribe("from-files", self.__make_from_files)
            frame_in.context.unsubscribe("extract", self.__extract)
            frame_in.context.unsubscribe("exit", self.destroy)

            self.__toolbar.layout_control.unsubscribe(
                "single", lambda: setattr(
                    frame_in.context, "single", False))
            self.__toolbar.layout_control.unsubscribe(
                "double", lambda: setattr(
                    frame_in.context, "double", True))
            self.__toolbar.layout_control.unsubscribe(
                "vertical", lambda: setattr(
                    frame_in, "orientation", readframe.VERTICAL_SCROLL))
            self.__toolbar.layout_control.unsubscribe(
                "horizontal", lambda: setattr(
                    frame_in, "orientation", readframe.HORIZONTAL_SCROLL))
            self.__toolbar.layout_control.unsubscribe(
                "manga", lambda: frame_in.set_manga(
                    self.__toolbar.layout_control.manga))

            if hasattr(frame_in, "fit"):
                self.__toolbar.view_control.unsubscribe("fit", frame_in.fit)
            self.__toolbar.view_control.unsubscribe("zoom+", frame_in.zoom_in)
            self.__toolbar.view_control.unsubscribe("zoom-", frame_in.zoom_out)

            self.__toolbar.view_control.unsubscribe(
                "contents", frame._goto,
                where=frame_in.CONTENTS)
            self.__toolbar.comic_control.unsubscribe(
                "firstpage", frame_in.goto,
                where_in=frame_in.BEGINNING)
            self.__toolbar.comic_control.unsubscribe(
                "prevpage", frame_in.goto,
                where_in=frame_in.PREVIOUS)
            self.__toolbar.comic_control.unsubscribe(
                "setpage", lambda: frame_in.goto(
                frame_in.PAGE, self.__toolbar.comic_control.pages))
            self.__toolbar.comic_control.unsubscribe(
                "nextpage", frame_in.goto,
                where_in=frame_in.NEXT)
            self.__toolbar.comic_control.unsubscribe(
                "lastpage", frame_in.goto,
                where_in=frame_in.END)
            self.__toolbar.comic_control.unsubscribe(
                "back", frame_in.go_back)

            frame_in.unsubscribe("page", self.__status_change)
            frame_in.unsubscribe("scale", self.__status_change)
            frame_in.pages = []
            # frame_in.configure(state=tkinter.HIDDEN)
        self.__viewer = None

    def __load(self, file_in: pathlib.Path, progress_in: popup.ProgressBar = None):
        self.title(file_in.name)
        if (self.__viewer.comic is None or
                self.__viewer.comic.file != file_in):
            self.__viewer.update_idletasks()
            self.__viewer.set_file(
                file_in,  progress=progress_in)
            self.__toolbar.comic_control.contents_enabled = (
                    self.__viewer.comic.toc is not None)
            if self.__viewer.comic.author:
                self.title(
                    f"{self.__viewer.comic.title} "
                    f"by: {self.__viewer.comic.author}")
            else:
                self.title(self.__viewer.comic.title)
            self.__viewer.draw(False, progress_in)
        self.__toolbar.comic_control.total = len(self.__viewer.comic)
        self.__toolbar.title = self.__viewer.comic.title
        self.__clean_toplevel()

    def __comics(self, path_in: pathlib.Path = None) -> list:
        path_in = self.__viewer.file.parent if path_in is None else path_in
        if path_in is not None:
            return sorted(
                [f for f in path_in.iterdir() if f.suffix in book.Book.EXTENSIONS],
                key=lambda f: f"{f}")
        else:
            return []

    def __open(self):
        # try:
            file = pathlib.Path(
                    tkinter.filedialog.askopenfilename(
                        title="Select a File",
                        filetypes=[
                            ("Comic", " ".join(book.Book.EXTENSIONS)),
                            ("All Files", "*.*")])).resolve()
            if file.is_file() and file.suffix in book.Book.EXTENSIONS:
                self.load(file)

        # except (TypeError, ValueError) as error:
        #     print(f"Error: {error}")

    def __load_prev(self):
        comics = self.__comics()
        if self.__viewer.comic is not None:
            self.load(comics[(comics.index(
                self.__viewer.comic.file) + len(comics) - 1) % len(comics)])
        elif len(comics):
            self.load(comics[0])

    def __load_next(self):
        comics = self.__comics()
        if self.__viewer.comic is not None:
            self.load(comics[(comics.index(
                self.__viewer.comic.file) + 1) % len(comics)])
        elif len(comics):
            self.load(comics[0])

    def __add_page(self):
        file = pathlib.Path(
            tkinter.filedialog.askopenfilename(
                title="Select a File",
                filetypes=[
                    ("Images", f"{" ".join([f"*{e}" for e in PIL.Image.registered_extensions()])}"),
                    ("All Files", "*.*")])).resolve()
        self.__viewer.comic.add_page(file)

    def __delete_page(self):
        page = self.__viewer.which_page(self.__viewer.context_event)
        progress, semaphore = popup.ProgressBar(
            self,
            "Processing",
            f"Deleting Page: {page}..."), tkinter.BooleanVar(self)
        self.after(50, self.__viewer.comic.delete_page, page, progress, semaphore)
        self.__pair = 0
        self.wait_variable(semaphore)
        self.__viewer.draw()

    def __convert(self):
        new_comic = book.Book(
            pathlib.Path(
                tkinter.filedialog.asksaveasfilename(
                    title="Select a new comic",
                    filetypes=[(t, t) for t in [".cbz", ".cb7"]] + [("All Files", "*.*")],
                    initialfile=f"{self.__viewer.comic.file.stem}.cbz")), self)

        if new_comic.file != self.__viewer.comic.file:
            convert = converter.Converter(self.__viewer.comic.file, new_comic.file)
            convert.convert()
            self.load(new_comic.file)
        else:
            pass

    def __make_from_directory(self):
        path = pathlib.Path(
            tkinter.filedialog.askdirectory(
                title="Select a Directory"))
        self.__make([p for p in path.iterdir() if p.is_file()], f"{path.name}.cbz")

    def __make_from_files(self):
        self.__make([pathlib.Path(f).resolve() for f in
            tkinter.filedialog.askopenfilenames(
                initialdir=f"~",
                title="Select all page images",
                filetypes=[("Images", f"{" ".join([f"*{e}" for e in PIL.Image.registered_extensions()])}")])])

    def __extract(self):
        if self.__viewer.comic is not None:
            path = pathlib.Path(
                tkinter.filedialog.askdirectory(
                    initialdir=f"{self.__viewer.comic.file.parent}",
                    title="Select a extraction destination directory"))
            path = path / f"{self.__viewer.comic.file.stem}"
            path.mkdir(parents=True, exist_ok=True, mode=750)
            self.__viewer.comic.extractall(path)

    def __make(self, pages_in: list[pathlib.Path], name_in: str = None):
        pages_in = [p for p in pages_in if p.suffix in PIL.Image.registered_extensions()]
        new_comic = book.Book(
            pathlib.Path(
                tkinter.filedialog.asksaveasfilename(
                    title="Create New Comice",
                    filetypes=[
                        ("Comics", f"{" ".join(book.Book.EXTENSIONS)}"),
                        ("All Files", "*.*")],
                    initialfile=("New Comic.cbz" if name_in is None else name_in))), self)

        # Make sure that the existing file is cleared.
        with new_comic.archive("w") as archive:
            new_comic.close(archive)
        progress = popup.ProgressBar(self, "Creating Comic", "Adding Pages...", len(pages_in) - 1)
        self.after(20, new_comic.write_pages, pages_in, progress)
        self.wait_window(progress)

        # Load the new comic
        # self.__viewer.comic = comic
        self.load(new_comic.file)

    def __status_change(self):
        self.__status.set(
            f"Page: {" - ".join(self.__viewer.names)}, "
            f"Scale: {round(self.__viewer.scale * 100.0)}%")
        self.__toolbar.comic_control.pages = self.__viewer.pages

    def __motion(self, event_in: tkinter.Event):
        self.__status_change()
        self.__status.set(
            f"{self.__status.get()}, "
            f"Position: "
            f"{self.__viewer.canvasx(event_in.x)}, "
            f"{self.__viewer.canvasy(event_in.y)}")

    def __clean_toplevel(self):
        for widget in self.winfo_children():
            if isinstance(widget, tkinter.Toplevel):
                widget.destroy()
