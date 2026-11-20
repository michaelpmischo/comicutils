#!/usr/bin/env python3
import sys, pathlib, types, tkinter, tkinter.ttk, tkinter.filedialog, abc

# For testing..
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.comics.comic import Comic
    from comicutils.gui import callbackmanager, menubar, popup, navigationframe
    from comicutils.utils import resolver
else:
    from ..comics.comic import Comic
    from . import callbackmanager, menubar, popup, navigationframe
    from ..utils import resolver

# Constants
VERTICAL_SCROLL = (tkinter.VERTICAL, "scroll")
HORIZONTAL_SCROLL = (tkinter.HORIZONTAL, "scroll")
DOUBLE_PAGES = (tkinter.HORIZONTAL, "pages")
SINGLE_PAGES = (tkinter.HORIZONTAL, "pages")
ORIENTATIONS = [VERTICAL_SCROLL, HORIZONTAL_SCROLL, DOUBLE_PAGES, SINGLE_PAGES]


# =============================================================================
# ReadFrame
# =============================================================================
class ReadFrame(abc.ABC, callbackmanager.CallbackManager, tkinter.ttk.Frame):
    # Navigation Constants
    BEGINNING, PREVIOUS, NEXT, END, PAGE = 0, 1, 2, 3, 4

    _DEBUG = False
    _BACKGROUND = "gray"
    _ICONS = resolver.icon_root()

    _ZOOM_STEP = 1.1
    _ZOOM_LIMITS = (0.2, 4.0)

    def __init__(self, master_in: tkinter.Misc, comic_in: str | pathlib.Path | Comic = None, **args_in):
        # Member Variables
        (self.__comic, self.__pages, self.__last_pages, self.__scale, self.__xscrollbar, self.__yscrollbar,
         self.__draw_id, self.__orientation) = None, [], [], 1.0, None, None, None, None
        abc.ABC()
        callbackmanager.CallbackManager.__init__(self, ["page", "scale", "double", "shadow", "fit"])
        self.__font = args_in.pop("font") if "font" in args_in.keys() else ("Impact", 12)
        self.orientation = args_in.pop("orient") if "orient" in args_in.keys() else DOUBLE_PAGES
        tkinter.Frame.__init__(self, master_in, **args_in)

        # The Current Comic
        self.__comic = Comic(comic_in, self.master) if (
            isinstance(comic_in, (str, pathlib.Path))) else comic_in

        # Control Variables
        self.__page_drawing, self.__page_turning = (
            tkinter.BooleanVar(self, value=False),
            tkinter.BooleanVar(self, value=False))

        self.__navigation = navigationframe.NavigationFrame(self, "Pages", 300)
        self.__navigation.subscribe("selected", self.__navigate)

        self.__context = menubar.ViewerContextMenu(self, tearoff=False, font=self.__font)
        self.__context.subscribe("double", lambda: self._callback("double"))
        self.__context.subscribe("shadow", lambda: self._callback("shadow"))
        self.__context.subscribe("fit", lambda: self._callback("fit"))
        self.__context.subscribe("nav", self.__show_navigation)
        self.__context_event = None

        self.bind("<Configure>", self._resize, add="+")
        # self.rowconfigure(0, weight=1)

    def rebind_tree(self, widget_in: tkinter.Widget = None):
        widget_in = widget_in if widget_in is not None else self
        for widget in widget_in.winfo_children():
            if widget not in [self.__context, self.__navigation]:
                # Bind Events
                widget.bind("<MouseWheel>", self._scroll)
                widget.bind("<Button-4>", self._scroll)
                widget.bind("<Button-5>", self._scroll)
                widget.bind("<Control-MouseWheel>", self.__zoom)
                widget.bind("<Control-Button-4>", self.__zoom)
                widget.bind("<Control-Button-5>", self.__zoom)
                widget.bind("<Button-3>", self.__show_context)
                self.rebind_tree(widget)

    @property
    def comic(self) -> Comic:
        return self.__comic

    @comic.setter
    def comic(self, comic_in: Comic):
        if isinstance(comic_in, (Comic, types.NoneType)):
            self.__comic = comic_in
            self.__navigation.load(comic_in)
            self.__scale = 1.0
            self.__pages = [0]
        else:
            raise ValueError(
                f"Invalid Comic: {type(comic_in).__name__}")

    @property
    def file(self) -> pathlib.Path:
        if self.__comic is not None:
            return self.__comic.file
        else:
            return pathlib.Path("~").resolve()

    @file.setter
    def file(self, file_in: pathlib.Path):
        if isinstance(file_in, (str, pathlib.Path)):
            self.comic = Comic(file_in, self.master)
        else:
            raise VaileError(
                f"Invalid File: {type(file_in).__name__}.")

    @property
    def size(self) -> tuple[int, int]:
        self.update_idletasks()
        return self.winfo_width(), self.winfo_height()

    @property
    def scale(self) -> float:
        return self.__scale

    @scale.setter
    def scale(self, scale_in: float):
        if isinstance(scale_in, (int, float)):
            self.__scale = scale_in
            self._callback("scale")
        else:
            raise ValueError(
                f"Invalid Scale: {type(scale_in).__name__}")

    @property
    def pages(self) -> list[int]:
        return self.__pages

    @pages.setter
    def pages(self, pages_in: list[int]):
        if isinstance(pages_in, (list, tuple, int)):
            self.__last_pages = self.__pages
            self.__pages = [pages_in] if isinstance(
                pages_in, int) else pages_in
            self._callback("page")
        else:
            raise ValueError(
                f"Invalid Pages: {type(pages_in).__name__}")

    @property
    def changed(self) -> bool:
        return self.__last_pages != self.__pages

    @property
    def names(self) -> list[str]:
        if self.__comic is not None:
            return [self.__comic.files[p] for p in self.__pages]
        else:
            return []

    @property
    def context(self) -> tkinter.Menu:
        return self.__context
        
    @context.setter
    def context(self, context_in: tkinter.Menu):
        if isinstance(context_in, tkinter.Menu):
            self.__context = context_in
        else:
            raise ValueError(
                f"Invalid Context Menu: {type(context_in).__name__}")

    @property
    def context_event(self) -> tkinter.Event:
        return self.__context_event

    @property
    def font(self) -> tuple:
        return self.__font
        
    @font.setter
    def font(self, font_in: tuple):
        if isinstance(font_in, tuple):
            self.__font = font_in
        else:
            raise ValueError(
                f"Invalid Font: {type(font_in).__name__}")

    @property
    def _page_turning(self) -> bool:
        return self.__page_turning.get()

    @_page_turning.setter
    def _page_turning(self, page_turning_in: bool):
        if isinstance(page_turning_in, bool):
            self.__page_turning.set(page_turning_in)
        else:
            raise ValueError(
                f"Invalid Argument: {type(page_turning_in).__name__}")

    @property
    def _page_drawing(self) -> bool:
        return self.__page_drawing.get()
        
    @_page_drawing.setter
    def _page_drawing(self, page_drawing_in: bool):
        if isinstance(page_drawing_in, bool):
            self.__page_drawing.set(page_drawing_in)
        else:
            raise ValueError(
                f"Invalid Argument: {type(page_drawing_in).__name__}")

    @property
    def _draw_id(self) -> str:
        return self.__draw_id

    @_draw_id.setter
    def _draw_id(self, id_in: int | str):
        if isinstance(id_in, (int, str, types.NoneType)):
            if self.__draw_id is not None:
                self.after_cancel(self.__draw_id)
            self.__draw_id = id_in
        else:
            raise ValueError(
                f"Invalid ID: {type(id_in).__name__}")
                
    @property
    def xscrollbar(self) -> tkinter.ttk.Scrollbar:
        return self.__xscrollbar
        
    @xscrollbar.setter
    def xscrollbar(self, scrollbar_in: tkinter.ttk.Scrollbar):
        if isinstance(scrollbar_in, tkinter.ttk.Scrollbar):
            self.__xscrollbar = scrollbar_in
        else:
            raise ValueError(
                f"Invalid Horizontal Scrollbar: {type(scrollbar_in).__name__}")

    @property
    def yscrollbar(self) -> tkinter.ttk.Scrollbar:
        return self.__yscrollbar
        
    @yscrollbar.setter
    def yscrollbar(self, scrollbar_in: tkinter.ttk.Scrollbar):
        if isinstance(scrollbar_in, tkinter.ttk.Scrollbar):
            self.__yscrollbar = scrollbar_in
        else:
            raise ValueError(
                f"Invalid Horizontal Scrollbar: {type(scrollbar_in).__name__}")

    def draw(self, reverse_in: bool = False):
        if self.__comic is not None:
            self.__page_drawing.set(True)
            bar = popup.ProgressBar(self, "Drawing...", "Drawing...") if (
                    self.__orientation[1] == "scroll") else None
            # Cancel the previous draw call before starting a new one.
            self._draw_id = self.after(
                25, self._draw, self.__pages, reverse_in, bar)

            # Pend without blocking mainloop until the draw is complete.
            self.wait_variable(self.__page_drawing)
            if bar is not None:
                bar.stop()
            
    @abc.abstractmethod
    def _draw(self, pages_in: list[int] = None,
               reverse_in: bool = False,
               progress_in: popup.ProgressBar = None):
        pass

    def load(self):
        if self.__comic is not None:
            self.__comic.load()
            self.pages = [0]
            self.draw()

    def wait_on_page_drawing(self):
        if self.__page_drawing.get():
            self.wait_variable(self.__page_drawing)

    def wait_on_page_turn(self):
        if self.__page_turning.get():
            self.wait_variable(self.__page_turning)

    def goto(self, where_in: int, page_in: int = None):
        if where_in == self.BEGINNING:
            self._beginning()
        elif where_in == self.PREVIOUS:
            self._previous()
        elif where_in == self.NEXT:
            self._next()
        elif where_in == self.END:
            self._end()
        elif where_in == self.PAGE and page_in is not None:
            self._go(page_in)

    @abc.abstractmethod
    def _beginning(self):
        pass

    @abc.abstractmethod
    def _previous(self):
        pass

    @abc.abstractmethod
    def _next(self):
        pass

    @abc.abstractmethod
    def _end(self):
        pass

    def _go(self, page_in: int = None):
        self._page_turning = True
        try:
            if self.context.double:
                self.pages = list([p for p in self.comic.pairs if page_in in p][0])
            else:
                self.pages = [page_in]
        except IndexError as _:
            pass
        finally:
            self._page_turning = False

    @property
    def orientation(self):
        return self.__orientation

    @orientation.setter
    def orientation(self, orientation_in: tuple):
        if orientation_in in ORIENTATIONS:
            self.__orientation = orientation_in
            self.draw()
        else:
            raise ValueError(
                f"Invalid Orientation: {self.__orientation}")

    def zoom(self, x_in: int, y_in: int, zoom_in: bool):
        """ Set the scale factor based on if we we are zooming in or out """
        scale = (1.0 * self._ZOOM_STEP) if zoom_in else (1.0 / self._ZOOM_STEP)
        if self._ZOOM_LIMITS[0] <= self.scale * scale <= self._ZOOM_LIMITS[1]:
            self.scale *= scale

    @abc.abstractmethod
    def zoom_in(self, x_in: int = None, y_in: int = None):
        """ Zoom in with button """
        pass

    @abc.abstractmethod
    def zoom_out(self, x_in: int = None, y_in: int = None):
        """ Zoom out with button """
        pass

    @abc.abstractmethod
    def _resize(self, event_in: tkinter.Event):
        pass

    def __zoom(self, event_in: tkinter.Event):
        """ Zoom with mouse wheel """
        self.zoom(event_in.x, event_in.y, 
            event_in.num == 4 or event_in.delta > 0)

    @abc.abstractmethod
    def _scroll(self, event_in: tkinter.Event):
        """ Zoom with mouse wheel """
        pass

    def turn_page(self, event_in: tkinter.Event):
        if not self.__page_turning.get():
            self.__page_turning.set(True)
            try:
                if event_in.num == 5 or event_in.delta < 0:  # scroll down
                    self._next()
                elif event_in.num == 4 or event_in.delta > 0:  # scroll up
                    self._previous()
            finally:
                self.__page_turning.set(False)

    def __show_context(self, event_in: tkinter.Event):
        try:
            self.__context_event = event_in
            self.context.tk_popup(
                event_in.x_root, event_in.y_root)
        finally:
            self.context.grab_release()

    def __navigate(self, event_in: tkinter.Event):
        page = self.__navigation.selected_info
        if page is not None and 0 <= page < self.comic.number_of_pages:
            self.goto(self.PAGE, page)

    def __show_navigation(self):
        if self.context.navigation:
            self.__navigation.pack(side=tkinter.LEFT, fill=tkinter.Y)
            self.__navigation.load(self.comic, min(self.pages))
        else:
            self.__navigation.pack_forget()
            self.__navigation.clear()
