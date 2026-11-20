#!/usr/bin/env python3
import pathlib, ast, types, PIL.Image, PIL.ImageTk, PIL.ImageOps, tkinter, tkinter.ttk, tkinter.filedialog

# For testing..
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.utils import packages, resolver
    from comicutils.gui import callbackmanager, popup
else:
    from ..utils import packages, resolver
    from . import callbackmanager, popup

MAX = (200, 36)
ICONS = resolver.icon_root()


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

        fit = tkinter.Button(self, relief=self.__relief, pady=0,
                             command=lambda: self._callback("fit"))
        fit.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "fit.png"), MAX))
        fit.configure(image=fit.photo)
        fit.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(fit, self.__tips[self.__col], 1000))
        self._set_widget("fit", fit)
        self.__col += 1

        zoom_in = tkinter.Button(
            self, relief=self.__relief, pady=0, command=lambda: self._callback("zoom+"))
        zoom_in.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "zoom+.png"), MAX))
        zoom_in.configure(image=zoom_in.photo)
        zoom_in.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(zoom_in, self.__tips[self.__col], 1000))
        self._set_widget("zoom+", zoom_in)
        self.__col += 1

        zoom_out = tkinter.Button(
            self, relief=self.__relief, pady=0, command=lambda: self._callback("zoom-"))
        zoom_out.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "zoom-.png"), MAX))
        zoom_out.configure(image=zoom_out.photo)
        zoom_out.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(zoom_out, self.__tips[self.__col], 1000))
        self._set_widget("zoom-", zoom_out)
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
            "Vertical Scroll Layout (Webtoon)",
            "Horizontal Scroll Layout",
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

        vertical = tkinter.Button(
            self, relief=self.__relief, command=lambda: self.__on_select(
                vertical, "vertical"))
        vertical.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "vertical.png"), MAX))
        vertical.configure(image=vertical.photo)
        vertical.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(vertical, self.__tips[self.__col], 1000))
        self._set_widget("vertical", vertical)
        self.__col += 1

        horizontal = tkinter.Button(
            self, relief=self.__relief, command=lambda: self.__on_select(
                horizontal, "horizontal"))
        horizontal.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "horizontal.png"), MAX))
        horizontal.configure(image=horizontal.photo)
        horizontal.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(horizontal, self.__tips[self.__col], 1000))
        self._set_widget("horizontal", horizontal)
        self.__col += 1

        manga = tkinter.Button(
            self, relief=self.__relief, command=self.__on_manga)
        manga.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "manga.png"), MAX))
        manga.configure(image=manga.photo)
        manga.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(manga, self.__tips[self.__col], 1000))
        self._set_widget("manga", manga)
        self.__col += 1

        self.__current.configure(relief=tkinter.SUNKEN, state=tkinter.DISABLED)

    @property
    def manga(self) -> bool:
        return self._get_widget("manga").cget("relief") == tkinter.SUNKEN

    def __on_select(self, button_in: tkinter.Button, event_in: str):
        if self.__current is not None:
            self.__current.configure(relief=self.__relief, state=tkinter.NORMAL)
            self._set_states()
        self.__current = button_in
        self.__current.configure(relief=tkinter.SUNKEN, state=tkinter.DISABLED)
        self._callback(event_in)

    def __on_manga(self):
        self._get_widget("manga").configure(
            relief=(self.__relief if self.manga else tkinter.SUNKEN),
            bg=("yellow" if self.manga else "gray"))
        self._callback("manga")


# =============================================================================
# ComicController
# =============================================================================
class ComicController(callbackmanager.CallbackManager, tkinter.Frame):

    def __init__(self, master_in: tkinter.Misc, **args_in):
        callbackmanager.CallbackManager.__init__(
            self, ["opencomic", "prevcomic", "firstpage",
                   "prevpage", "nextpage", "lastpage", "nextcomic"])
        self.__font = args_in.pop("font") if "font" in args_in.keys() else ("Impact", 18)
        tkinter.Frame.__init__(self, master_in, **args_in)
        self.__row, self.__col = 0, 0
        self.__relief = args_in.pop("relief") if "relief" in args_in.keys() else tkinter.FLAT
        self.__total = None

        self.__tips = [
            "Open Comic",
            "Previous Comic",
            "First Page",
            "Previous Page",
            "Current Page(s)",
            "Next Page",
            "Last Page",
            "Next Comic"]
        self.__tooltips = []

        opencomic = tkinter.Label(self, relief=self.__relief)
        opencomic.configure(text="Open", font=(self.__font[0], self.__font[1] + 4))
        opencomic.grid(row=self.__row, column=self.__col, padx=1, sticky=tkinter.NSEW)
        opencomic.bind("<Button-1>", lambda event: self._callback("opencomic"))
        self.__tooltips.append(popup.Tooltip(opencomic, self.__tips[self.__col], 1000))
        self._set_widget("opencomic", opencomic)
        self.__col += 1

        prevcomic = tkinter.Button(
            self, relief=self.__relief, command=lambda: self._callback("prevcomic"))
        prevcomic.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "comicprev.png"), MAX))
        prevcomic.configure(image=prevcomic.photo)
        prevcomic.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(prevcomic, self.__tips[self.__col], 1000))
        self._set_widget("prevcomic", prevcomic)
        self.__col += 1

        firstpage = tkinter.Button(
            self, relief=self.__relief, command=lambda: self._callback("firstpage"))
        firstpage.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "first.png"), MAX))
        firstpage.configure(image=firstpage.photo)
        firstpage.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(firstpage, self.__tips[self.__col], 1000))
        self._set_widget("firstpage", firstpage)
        self.__col += 1

        prevpage = tkinter.Button(
            self, relief=self.__relief, command=lambda: self._callback("prevpage"))
        prevpage.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "pageprev.png"), MAX))
        prevpage.configure(image=prevpage.photo)
        prevpage.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(prevpage, self.__tips[self.__col], 1000))
        self._set_widget("prevpage", prevpage)
        self.__col += 1

        self.__pages = tkinter.StringVar(self, value="-")
        self.__label = tkinter.Label(self, font=self.__font, textvariable=self.__pages,
            pady=0, padx=10, width=10, relief=tkinter.SUNKEN)
        self.__label.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        #self.__tooltips.append(popup.Tooltip(self.__label, self.__tips[self.__col], 1000))
        self.__col += 1

        nextpage = tkinter.Button(
            self, relief=self.__relief, command=lambda: self._callback("nextpage"))
        nextpage.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "pagenext.png"), MAX))
        nextpage.configure(image=nextpage.photo)
        nextpage.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(nextpage, self.__tips[self.__col], 1000))
        self._set_widget("nextpage", nextpage)
        self.__col += 1

        lastpage = tkinter.Button(
            self, relief=self.__relief, command=lambda: self._callback("lastpage"))
        lastpage.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "last.png"), MAX))
        lastpage.configure(image=lastpage.photo)
        lastpage.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(lastpage, self.__tips[self.__col], 1000))
        self._set_widget("lastpage", lastpage)
        self.__col += 1

        nextcomic = tkinter.Button(
            self, relief=self.__relief, command=lambda: self._callback("nextcomic"))
        nextcomic.photo = PIL.ImageTk.PhotoImage(
            PIL.ImageOps.contain(PIL.Image.open(ICONS / "comicnext.png"), MAX))
        nextcomic.configure(image=nextcomic.photo)
        nextcomic.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__tooltips.append(popup.Tooltip(nextcomic, self.__tips[self.__col], 1000))
        self._set_widget("nextcomic", nextcomic)
        self.__col += 1

    @property
    def pages(self) -> list[int]:
        if self.__pages.get() == "-":
            return []
        else:
            return [i-1 for i in ast.literal_eval(
                f"[{self.__pages.get().split("/")[0]}]")]

    @pages.setter
    def pages(self, pages_in: list[int] | None):
        if isinstance(pages_in, (tuple, list, str, int)):
            pages_in = [int(pages_in)] if isinstance(
                pages_in, (str, int)) else [
                int(p) for p in pages_in]
            if pages_in is not None and len(pages_in):
                self.__pages.set(
                    f"{", ".join([f"{p+1}" for p in pages_in])}")
                self.total = self.__total
            else:
                self.__pages.set("-")
        else:
            raise ValueError(
                f"Invalid Type For Pages: {pages_in}")

    @property
    def total(self) -> int | None:
        return self.__total

    @total.setter
    def total(self, total_in: int | None):
        if isinstance(total_in, (int, types.NoneType)):
            if total_in is not None:
                self.__total = total_in
                try:
                    self.__pages.set(
                        f"{self.__pages.get().split(" of ")[0]} of "
                        f"{self.__total}")
                except Exception as error:
                    self.__pages.set(f"{error}")
        else:
            raise ValueError(
                f"Invalid Type For Scale: {total_in}")


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
        self.__comic_control.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__col += 1

        self.__layout_control = LayoutController(
            self, bd=4, bg="gray", font=self.__font, relief=self.__relief)
        self.__layout_control.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__col += 1

        self.__view_control = ViewController(
            self, bd=4, bg="gray", font=self.__font, relief=self.__relief)
        self.__view_control.grid(row=self.__row, column=self.__col, padx=1, pady=0, sticky=tkinter.NSEW)
        self.__col += 1

        self.__insert_gap()

        self.__title_display = tkinter.Label(
            self, textvariable=self.__title, relief=tkinter.FLAT,
            bg="white", bd=0, font=(self.__font[0], 18))
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
