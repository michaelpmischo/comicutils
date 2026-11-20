#!/usr/bin/env python3
import pathlib, ast, types, typing
import PIL.Image, PIL.ImageTk, PIL.ImageOps, tkinter, tkinter.ttk, tkinter.filedialog
# For testing..
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.utils import packages, resolver
    from comicutils.gui2 import callbackmanager, popup
else:
    from ..utils import packages, resolver
    from . import callbackmanager, popup


MAX = (200, 36)
ICONS = resolver.icon_root()
SELECTED = "#FFFFC5"


# =============================================================================
# ViewController
# =============================================================================
class ViewController(callbackmanager.CallbackManager, tkinter.Frame):
    def __init__(self, master_in: tkinter.Misc, **args_in):
        callbackmanager.CallbackManager.__init__(self, ["fit", "zoom+", "zoom-"])
        self.__font = args_in.pop("font") if "font" in args_in.keys() else ("Impact", 18)
        tkinter.Frame.__init__(self, master_in, **args_in)
        self.__row, self.__col = 0, 0
        self.__relief = args_in.pop("relief") if "relief" in args_in.keys() else tkinter.FLAT
        self.__scale = 1.0

        self.__tips = ["Fit the Comic to the Window.", "Zoom In", "Zoom Out"]
        self.__tooltips = []

        fit = tkinter.Button(self, relief=self.__relief)
        self._set_widget("fit", fit)
        fit.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(
                PIL.Image.open(ICONS / "fit.png"), MAX))
        fit.configure(image=fit.photo)
        fit.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(fit, self.__tips[self.__col], 1000))
        self.__col += 1

        zoom_in = tkinter.Button(self, relief=self.__relief)
        self._set_widget("zoom+", zoom_in)
        zoom_in.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(
                PIL.Image.open(ICONS / "zoom+.png"), MAX))
        zoom_in.configure(image=zoom_in.photo)
        zoom_in.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(zoom_in, self.__tips[self.__col], 1000))
        self.__col += 1

        zoom_out = tkinter.Button(self, relief=self.__relief)
        self._set_widget("zoom-", zoom_out)
        zoom_out.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(
                PIL.Image.open(ICONS / "zoom-.png"), MAX))
        zoom_out.configure(image=zoom_out.photo)
        zoom_out.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(zoom_out, self.__tips[self.__col], 1000))
        self.__col += 1

    @property
    def scale(self) -> float:
        return self.__scale

    @scale.setter
    def scale(self, scale_in: float):
        if isinstance(scale_in, (float, int)):
            self.__scale = scale_in
        else:
            raise ValueError(
                f"Invalid Type For Scale: {scale_in}")


# =============================================================================
# LayoutController
# =============================================================================
class LayoutController(callbackmanager.CallbackManager, tkinter.Frame):

    def __init__(self, master_in: tkinter.Misc, **args_in):
        callbackmanager.CallbackManager.__init__(self, ["single", "double", "vertical", "horizontal", "manga"])
        self.__font = args_in.pop("font") if "font" in args_in.keys() else ("Impact", 18)
        tkinter.Frame.__init__(self, master_in, **args_in)
        self.__row, self.__col = 0, 0
        self.__relief = args_in.pop("relief") if "relief" in args_in.keys() else tkinter.FLAT
        self.__total = None
        self.__last = None

        self.__tips = [
            "Single Page Layout",
            "Double Page Layout",
            "Web Comic Layout",
            # "Horizontal Scroll Layout",
            "Manga/Japanese Reading Mode"]
        self.__tooltips = []

        single = tkinter.Button(
            self, relief=self.__relief, command=lambda: self.__on_select(
                single, "single"))
        single.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "single.png"), MAX))
        single.configure(image=single.photo)
        single.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(single, self.__tips[self.__col], 1000))
        self._set_widget("single", single)
        self.__col += 1

        double = tkinter.Button(
            self, relief=self.__relief, command=lambda: self.__on_select(
                double, "double"))
        double.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "double.png"), MAX))
        double.configure(image=double.photo)
        double.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(double, self.__tips[self.__col], 1000))
        self._set_widget("double", double)

        # Double is selected by default.
        self.__current = self._get_widget("double")
        self.__col += 1

        vertical = tkinter.Button(self, relief=self.__relief)
        self._set_widget("vertical", vertical)
        self.subscribe("vertical", lambda: self.__on_select(
             vertical, "vertical"))
        vertical.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "weblayout.png"), MAX))
        vertical.configure(image=vertical.photo)
        vertical.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(vertical, self.__tips[self.__col], 1000))
        self.__col += 1

        # horizontal = tkinter.Button(
        #     self, relief=self.__relief, command=lambda: self.__on_select(
        #         horizontal, "horizontal"))
        # horizontal.photo = PIL.ImageTk.PhotoImage(
        #     PIL.ImageOps.contain(PIL.Image.open(ICONS / "horizontal.png"), MAX))
        # horizontal.configure(image=horizontal.photo)
        # horizontal.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        # self.__tooltips.append(popup.Tooltip(horizontal, self.__tips[self.__col], 1000))
        # self._set_widget("horizontal", horizontal)
        # self.__col += 1

        manga = tkinter.Button(self, relief=self.__relief)
        self._set_widget("manga", manga)
        self.subscribe("manga", lambda e, w: self.__on_manga)
        manga.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(
                PIL.Image.open(ICONS / "manga.png"), MAX))
        manga.configure(image=manga.photo)
        manga.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(manga, self.__tips[self.__col], 1000))
        self.__col += 1

        # Select Double as default.
        self.__on_select(double, "double")

    @property
    def manga(self) -> bool:
        return self._get_widget("manga").cget("relief") == tkinter.SUNKEN

    def __on_select(self, button_in: tkinter.Button, event_in: str):
        if self.__current is not None:
            self.__current.configure(relief=self.__relief, state=tkinter.NORMAL, bg="white")
            self._set_states()
        self.__current = button_in
        self.__current.configure(relief=tkinter.SUNKEN, state=tkinter.DISABLED, bg=SELECTED)

    def __on_manga(self):
        self._get_widget("manga").configure(
            relief=(self.__relief if self.manga else tkinter.SUNKEN),
            bg=("white" if self.manga else SELECTED))
        self._callback("manga")


# =============================================================================
# ComicController
# =============================================================================
class ComicController(callbackmanager.CallbackManager, tkinter.Frame):

    def __init__(self, master_in: tkinter.Misc, **args_in):
        callbackmanager.CallbackManager.__init__(
            self, ["opencomic", "contents", "prevcomic", "firstpage", "prevpage",
                   "setpage", "nextpage", "lastpage", "nextcomic", "back"])
        self.__font = args_in.pop("font") if "font" in args_in.keys() else ("Impact", 18)
        tkinter.Frame.__init__(self, master_in, **args_in)
        self.__row, self.__col = 0, 0
        self.__relief = args_in.pop("relief") if "relief" in args_in.keys() else tkinter.FLAT
        self.__total = None

        self.__tips = [
            "Open a comic",
            "Go to the table of contents",
            "Open the previous comic in the folder",
            "Go to the the first page(s)",
            "Go to the previous page(s)",
            "The Current Page(s)",
            "",
            "Total Page(s)",
            "Gp tp the next page(s)",
            "To to the last page(s)",
            "Open the next comic in the folder",
            "Back to previously viewed page(s)"]
        self.__tooltips = []

        opencomic = tkinter.Label(self,  relief=self.__relief)
        opencomic.configure(text="Open", pady=0, font=(self.__font[0], self.__font[1] + 4))
        opencomic.grid(row=self.__row, column=self.__col, padx=1, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(opencomic, self.__tips[self.__col], 1000))
        self._set_widget("opencomic", opencomic)
        self.__col += 1

        contents = tkinter.Button(self, relief=self.__relief)
        self._set_widget("contents", contents)
        contents.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(
                PIL.Image.open(ICONS / "toc.png"), MAX))
        contents.configure(image=contents.photo)
        contents.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(contents, self.__tips[self.__col], 1000))
        self.__col += 1

        prevcomic = tkinter.Button(self, relief=self.__relief)
        self._set_widget("prevcomic", prevcomic)
        prevcomic.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(
                PIL.Image.open(ICONS / "comicprev.png"), MAX))
        prevcomic.configure(image=prevcomic.photo)
        prevcomic.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(prevcomic, self.__tips[self.__col], 1000))
        self.__col += 1

        firstpage = tkinter.Button(self, relief=self.__relief)
        self._set_widget("firstpage", firstpage)
        firstpage.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(
                PIL.Image.open(ICONS / "first.png"), MAX))
        firstpage.configure(image=firstpage.photo)
        firstpage.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(firstpage, self.__tips[self.__col], 1000))
        self.__col += 1

        prevpage = tkinter.Button(self, relief=self.__relief)
        self._set_widget("prevpage", prevpage)
        prevpage.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(
                PIL.Image.open(ICONS / "pageprev.png"), MAX))
        prevpage.configure(image=prevpage.photo)
        prevpage.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(prevpage, self.__tips[self.__col], 1000))
        self.__col += 1

        setpage = tkinter.Entry(self, width=10, justify=tkinter.RIGHT,
            font=self.__font, relief=tkinter.SUNKEN)
        self._set_widget("setpage", setpage)
        setpage.grid(row=self.__row, column=self.__col, padx=0, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(setpage, self.__tips[self.__col], 1000))
        self.__col += 1

        self.__label = tkinter.Label(
            self, font=self.__font, text="", width=3,
            justify=tkinter.CENTER, relief=tkinter.FLAT)
        self.__label.grid(row=self.__row, column=self.__col, padx=0, pady=0, sticky=tkinter.NSEW)
        self.__col += 1

        self.__total = tkinter.StringVar(self, value="")
        self.__total_label = tkinter.Label(self, font=self.__font, textvariable=self.__total,
            pady=0, padx=0, width=4, relief=tkinter.FLAT, anchor=tkinter.W)
        self.__total_label.grid(row=self.__row, column=self.__col, padx=0, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(self.__total_label, self.__tips[self.__col], 1000))
        self.__col += 1

        nextpage = tkinter.Button(self, relief=self.__relief)
        self._set_widget("nextpage", nextpage)
        nextpage.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(
                PIL.Image.open(ICONS / "pagenext.png"), MAX))
        nextpage.configure(image=nextpage.photo)
        nextpage.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(nextpage, self.__tips[self.__col], 1000))
        self.__col += 1

        lastpage = tkinter.Button(self, relief=self.__relief)
        self._set_widget("lastpage", lastpage)
        lastpage.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(
                PIL.Image.open(ICONS / "last.png"), MAX))
        lastpage.configure(image=lastpage.photo)
        lastpage.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(lastpage, self.__tips[self.__col], 1000))
        self.__col += 1

        nextcomic = tkinter.Button(self, relief=self.__relief)
        self._set_widget("nextcomic", nextcomic)
        nextcomic.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(
                PIL.Image.open(ICONS / "comicnext.png"), MAX))
        nextcomic.configure(image=nextcomic.photo)
        nextcomic.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(nextcomic, self.__tips[self.__col], 1000))
        self.__col += 1

        back = tkinter.Button(self, relief=self.__relief)
        self._set_widget("back", back)
        back.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(
                PIL.Image.open(ICONS / "back.png"), MAX))
        back.configure(image=back.photo)
        back.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(back, self.__tips[self.__col], 1000))
        self.__col += 1

    @property
    def pages(self) -> list[int]:
        widget = self._get_widget("setpage")
        text = widget.get()
        if text == "-":
            return []
        else:
            return [i-1 for i in ast.literal_eval(f"[{text}]")]

    @pages.setter
    def pages(self, pages_in: list[int] | None):
        if isinstance(pages_in, (tuple, list, str, int)):
            pages_in = [int(pages_in)] if isinstance(
                pages_in, (str, int)) else [
                int(p) for p in pages_in]
            widget = self._get_widget("setpage")

            # Need to enable the tkinter.Text prior to setting the value.
            state = widget.cget("state")
            widget.configure(state=tkinter.NORMAL)
            widget.delete(0, tkinter.END)
            if pages_in is not None:
                text = f"{", ".join([f"{p+1}" for p in pages_in])}"
                widget.insert(0, text)
            else:
                widget.insert(0, "-")
            widget.configure(state=state)
        else:
            raise TypeError(
                f"Invalid Type For Pages: {type(
                    pages_in).__name__}")

    @property
    def contents_enabled(self) -> bool:
        return self._get_widget("contents").cget("state")

    @contents_enabled.setter
    def contents_enabled(self, enable_in: bool):
        if isinstance(enable_in, bool):
            self._get_widget("contents").configure(
                state=(tkinter.NORMAL if enable_in else tkinter.DISABLED),
                relief=(tkinter.RAISED if enable_in else tkinter.SUNKEN))
        else:
            raise TypeError(
                f"Invalid Argument For Contents Enabled: {type(
                    enable_in).__name__}")

    @property
    def total(self) -> int | None:
        return int(self.__total.get()) if self.__total.get() != "" else 0

    @total.setter
    def total(self, total_in: int | None):
        if isinstance(total_in, (int, types.NoneType)):
            if self.__total.get() is None:
                self.__total.set("")
                self.__label.configure(text="")
            else:
                self.__total.set(total_in if total_in else "")
                self.__label.configure(text=f" of ")
        else:
            raise TypeError(
                f"Invalid Type For Scale: {type(
                    total_in).__name__}")


# =============================================================================
# ViewerToolBar
# =============================================================================
class ViewerToolBar(callbackmanager.CallbackManager, tkinter.ttk.Frame):

    def __init__(self, master_in: tkinter.Misc, **args_in):
        callbackmanager.CallbackManager.__init__(self, ["down", "up", "next", "prev"])
        self.__font = args_in.pop("font") if "font" in args_in.keys() else ("MS Comic Sans", 14, "bold italic")
        tkinter.ttk.Frame.__init__(self, master_in, **args_in)
        self.__frame = tkinter.Frame(self)

        self.__row, self.__col = 0, 0
        self.__relief = args_in.pop("relief") if "relief" in args_in.keys() else tkinter.FLAT
        self.__labels = []
        self.__title = tkinter.StringVar(self, "")

        # self.__add_labels(["Title", "Layout", "View", "Comics"])
        # self.__next_row()

        self.__insert_gap()

        self.__comic_control = ComicController(
            self, bd=4, bg="gray", font=self.__font, relief=self.__relief)
        self.__comic_control.grid(row=self.__row, column=self.__col, padx=2, pady=0, sticky=tkinter.NSEW)
        self.__col += 1

        self.__layout_control = LayoutController(
            self, bd=4, bg="gray", font=self.__font, relief=self.__relief)
        self.__layout_control.grid(row=self.__row, column=self.__col, padx=2, pady=0, sticky=tkinter.NSEW)
        self.__col += 1

        self.__view_control = ViewController(
            self, bd=4, bg="gray", font=self.__font, relief=self.__relief)
        self.__view_control.grid(row=self.__row, column=self.__col, padx=2, pady=0, sticky=tkinter.NSEW)
        self.__col += 1

        self.__insert_gap()

        self.__title_display = tkinter.Label(
            self, textvariable=self.__title, relief=tkinter.FLAT,
            bg="white", bd=0, font=(self.__font[0], 20))
        self.__title_display.grid(row=self.__row + 1, column=0, columnspan=self.__col, sticky=tkinter.NSEW)

    @property
    def layout_control(self) -> LayoutController:
        return self.__layout_control

    @property
    def view_control(self) -> ViewController:
        return self.__view_control

    @property
    def comic_control(self) -> ComicController:
        return self.__comic_control

    @property
    def title(self) -> str:
        return self.__title.get()

    @title.setter
    def title(self, title_in: str):
        self.__title.set(f"{title_in}")

    def bind(self, sequence: str | None = None,
             func: callable  = None,
             add: str | bool | None = None,) -> str:
        return self.bind_all(sequence, func, add)

    def __add_labels(self, labels_in: list[str|None]):
        self.__labels = []
        for label in labels_in:
            if label is not None:
                self.__labels.append(tkinter.Label(self, text=label, font=self.__font))
                self.__labels[-1].grid(row=self.__row, column=self.__col, sticky=tkinter.NSEW)
            else:
                self.__labels.append(label)
            self.__col += 1

    def __insert_gap(self):
        self.columnconfigure(self.__col, weight=1)
        self.__col += 1

    def __next_row(self):
        self.__col = 0
        self.__row += 1
