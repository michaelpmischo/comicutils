#!/usr/bin/env python3
import sys, pathlib, PIL.Image, PIL.ImageTk, PIL.ImageOps, tkinter, tkinter.ttk, tkinter.filedialog, typing
# For testing..
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.comics.comic import Comic
    from comicutils.gui import autoscrollbar, menubar, readframe, popup, gifplayer
else:
    from ..comics.comic import Comic
    from . import autoscrollbar, menubar, readframe, popup, gifplayer


# =============================================================================
# CanvasReadFrame
# =============================================================================
class CanvasReadFrame(readframe.ReadFrame):

    __SHADOWS = [
        (PIL.ImageOps.contain, readframe.ReadFrame._ICONS / "bookshadow.png"), #]
        (PIL.Image.Image.resize, readframe.ReadFrame._ICONS / "bookshadow2.png")]

    def __init__(self, master_in: tkinter.Misc, comic_in: str | pathlib.Path | Comic = None,
                 orient_in: tuple = readframe.DOUBLE_PAGES, **args_in):
        super().__init__(master_in, comic_in, orient=orient_in, **args_in)

        # Member Variables
        (self.__pair, self.__grabbed, self.__objects, self.__manga) = (
            0, False, [], False)

        self.__openhand = f"@{self._ICONS / "open-hand.cur"}".replace('\\', '/')
        self.__closehand = f"@{self._ICONS / "close-hand.cur"}".replace('\\', '/')

        self.__reader = tkinter.Frame(self, bg=self._BACKGROUND, bd=0, highlightthickness=0)

        # Create the canvas Widget
        self.__canvas = tkinter.Canvas(self.__reader, bg=self._BACKGROUND, bd=2, highlightthickness=2)
        self.__canvas.drawers, self.__canvas.image_ids, self.__canvas.images = [], [], []
        for tag in ["left", "right"]:
            self.__canvas.drawers.append(
                gifplayer.AnimatedCanvasDrawer(
                    self.__canvas, None,
                    self.__canvas.winfo_width() // 2, 0,
                    anchor=tkinter.NW, tag=tag))
            self.__canvas.tag_bind(tag, "<Enter>", lambda event: self.__page_enter())
            self.__canvas.tag_bind(tag, "<Leave>", lambda event: self.__page_leave())

        self.__shadow = None
        self.__shadow_id = self.__canvas.create_image(
            self.__canvas.winfo_width() // 2, 0,
                anchor=tkinter.NW)

        # Create the vertical scrollbar widget
        self.yscrollbar = autoscrollbar.AutoScrollbar(
            self.__reader, self.__canvas, orient=tkinter.VERTICAL, command=self.__canvas.yview)
        self.__canvas.configure(yscrollcommand=self.yscrollbar.set)

        # Create the horizontal scrollbar widget
        self.xscrollbar = autoscrollbar.AutoScrollbar(
            self.__reader, self.__canvas, orient=tkinter.HORIZONTAL, command=self.__canvas.xview)
        self.__canvas.configure(xscrollcommand=self.xscrollbar.set)
        # Configure the layout manager for the fram.
        self.yscrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.xscrollbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.__canvas.pack(fill=tkinter.BOTH, expand=True)

        # Bond Events
        self.__canvas.bind('<ButtonPress-1>', self.__move_from)
        self.__canvas.bind('<B1-Motion>',     self.__move_to)
        self.__canvas.bind("<ButtonRelease-1>", self.__released)
        self.subscribe("double", self.__set_double)
        self.subscribe("shadow", self.__set_shadow)
        self.subscribe("fit", self.fit)
        self.__reader.pack(side=tkinter.RIGHT, fill=tkinter.BOTH, expand=True)
        self.rebind_tree(self.__reader)

    @typing.override
    @readframe.ReadFrame.comic.setter
    def comic(self, comic_in: Comic):
        readframe.ReadFrame.comic.fset(self, comic_in)
        self.__pair = 0
        self.load()
        self.draw()
        self.__canvas.yview_moveto(0.0)
        if self.orientation == readframe.HORIZONTAL_SCROLL:
            self.__canvas.xview_moveto(0.0)

    @typing.override
    @property
    def size(self) -> tuple[int, int]:
        self.update_idletasks()
        return self.__canvas.winfo_width(), self.__canvas.winfo_height()

    @typing.override
    @property
    def scale(self) -> float:
        return max(d.scale for d in self.__canvas.drawers)

    @typing.override
    @readframe.ReadFrame.scale.setter
    def scale(self, scale_in: float):
        if isinstance(scale_in, (float, int)):
            scale_in = max(self._ZOOM_LIMITS[0], min(scale_in, self._ZOOM_LIMITS[1]))
            [setattr(d, "scale", scale_in) for d in self.__canvas.drawers]
            readframe.ReadFrame.scale.fset(self, scale_in)
            self.draw()
        else:
            raise ValueError(
                f"Invalid Scale: {scale_in}")

    @typing.override
    @readframe.ReadFrame.pages.setter
    def pages(self, pages_in: list):
        pages = [p for p in pages_in if 0 <= p < self.comic.number_of_pages][:(2 if self.context.double else 1)]
        if len(pages):
            reverse = any([True for n, o in zip(self.pages, pages) if n > o])
            readframe.ReadFrame.pages.fset(self, pages_in)
            self.draw(reverse)

    @property
    def double(self) -> bool:
        return self.context.double

    @property
    def shadows(self) -> bool:
        return self.context.shadows

    @property
    def bbox(self) -> tuple:
        return self.__canvas.bbox(tkinter.ALL)

    @property
    def page_bbox(self) -> list[tuple]:
        if self.orientation[1] == "pages":
            return [self.__canvas.bbox(d.image_id) for d in self.__canvas.drawers]
        else:
            return [self.__canvas.bbox(i) for i in self.__canvas.image_ids]

    @property
    def comic_width(self):
        if self.orientation == readframe.VERTICAL_SCROLL:
            return max(i.width() for i in self.__canvas.images)
        elif self.orientation == readframe.HORIZONTAL_SCROLL:
            return sum(i.width() for i in self.__canvas.images)
        else:
            return sum(d.width for d in self.__canvas.drawers)

    @property
    def comic_height(self):
        if self.orientation == readframe.VERTICAL_SCROLL:
            return sum(i.height() for i in self.__canvas.images)
        elif self.orientation == readframe.HORIZONTAL_SCROLL:
            return max(i.height() for i in self.__canvas.images)
        else:
            return max(d.height for d in self.__canvas.drawers)

    @property
    def viewport_width(self) -> int:
        return self.__canvas.winfo_width()

    @property
    def viewport_height(self) -> int:
        return self.__canvas.winfo_height()

    @property
    def narrow(self) -> bool:
        return self.comic_width >= self.viewport_width

    @property
    def short(self) -> bool:
        return self.comic_height >= self.viewport_height

    def which_page(self, location_in: tuple | tkinter.Event) -> int | None:
        x, y = (self.__canvas.canvasx(location_in.x),
                self.__canvas.canvasy(location_in.y)) if (
            isinstance(location_in, tkinter.Event)) else (
                location_in[0], location_in[1])
        try:
            return [p for p, b in zip(self.pages, self.page_bbox) if (
                    b[0] <= x <= b[2] and b[1] <= y <= b[3])][0]
        except IndexError as _:
            return None

    def canvasx(self, x_in: int) -> int:
        try:
            return self.__canvas.canvasx(x_in)
        except Exception as _:
            return x_in

    def canvasy(self, y_in: int) -> int:
        try:
            return self.__canvas.canvasy(y_in)
        except Exception as _:
            return y_in

    def fit(self):
        self.scale = 1.0
        self.__center_viewport()

    def clear_scroll(self):
        [self.__canvas.delete(i) for i in self.__canvas.image_ids]
        self.__canvas.images, self.__canvas.image_ids = [], []

    def clear_pages(self):
        [setattr(d, "image", None) for d in self.__canvas.drawers]

    def set_manga(self, manga_in: bool):
        self.__manga = manga_in
        self.draw()

    @typing.override
    def _beginning(self):
        if not self._page_turning:
            self._page_turning = True
            try:
                self.__pair = 0
                self.pages = [0]
            finally:
                self._page_turning = False

    @typing.override
    def _previous(self):
        self._page_turning = True
        try:
            if self.context.double:
                self.__pair = min(max(0, self.__pair - 1),
                                  len(self.comic.pairs) - 1)
                self.pages = list(self.comic.pairs[self.__pair])
            else:
                self.pages = [min(
                    max(0, min(self.pages) - 1),
                    self.comic.number_of_pages - 1)]
        finally:
            self._page_turning = False

    @typing.override
    def _next(self):
        self._page_turning = True
        try:
            if self.context.double:
                self.__pair = min(max(0, self.__pair + 1),
                                  len(self.comic.pairs) - 1)
                self.pages = list(self.comic.pairs[self.__pair])
            else:
                self.pages = [min(
                    max(0, max(self.pages) + 1),
                    self.comic.number_of_pages - 1)]
        finally:
            self._page_turning = False

    @typing.override
    def _end(self):
        if not self._page_turning:
            try:
                self._page_turning = True
                if self.context.double:
                    self.__pair = len(self.comic.pairs) - 1
                    self.pages = list(self.comic.pairs[self.__pair])
                else:
                    self.pages = [self.comic.number_of_pages - 1]
            finally:
                self._page_turning = False

    @typing.override
    def zoom_in(self, x_in: int = None, y_in: int = None):
        """ Zoom in with button """
        self.zoom(
            (self.__canvas.winfo_width() // 2) if x_in is None else x_in,
            (self.__canvas.winfo_height() // 2) if y_in is None else y_in,
            True)

    @typing.override
    def zoom_out(self, x_in: int = None, y_in: int = None):
        """ Zoom out with button """
        self.zoom(
            (self.__canvas.winfo_width() // 2) if x_in is None else x_in,
            (self.__canvas.winfo_height() // 2) if y_in is None else y_in,
            False)

    @typing.override
    def _resize(self, event_in: tkinter.Event):
        self.draw()

    def __move_from(self, event_in: tkinter.Event):
        """ Remember previous coordinates for scrolling with the mouse """
        try:
            if (self.bbox[0] <= self.__canvas.canvasx(event_in.x) <= self.bbox[2] and
                    self.bbox[1] <= self.__canvas.canvasy(event_in.y) <= self.bbox[3]):
                self.__grabbed = True
                self.__canvas.configure(cursor=self.__closehand)
                self.__canvas.scan_mark(event_in.x, event_in.y)
        except (TypeError, AttributeError) as _:
            pass

    def __move_to(self, event_in: tkinter.Event):
        """ Drag (move) canvas to the new position """
        if self.__grabbed:
            self.__canvas.scan_dragto(
                event_in.x,
                event_in.y,
                gain=1)

    def __released(self, event_in: tkinter.Event):
        if self.__grabbed:
            self.__canvas.configure(cursor=self.__openhand)
            self.__grabbed = False

    @typing.override
    def __zoom(self, event_in: tkinter.Event):
        """ Zoom with mouse wheel """
        self.zoom(
            int(self.__canvas.canvasx(event_in.x)),
            int(self.__canvas.canvasy(event_in.y)),
            event_in.num == 4 or event_in.delta > 0)

    @typing.override
    def _scroll(self, event_in: tkinter.Event):
        """ Zoom with mouse wheel """
        if self.comic is not None:
            if self.orientation == readframe.VERTICAL_SCROLL:
                self.__canvas.yview_scroll(
                    int(-1 * (event_in.delta / 120)), "units")
            elif self.orientation == readframe.HORIZONTAL_SCROLL:
                self.__canvas.xview_scroll(
                    int(-1 * (event_in.delta / 120)), "units")
            elif self.scale <= 1.0 and self.orientation[1] == "pages":
                self.turn_page(event_in)
            else:
                if event_in.num == 5 or event_in.delta < 0:  # scroll down
                    if self.__manga:
                        self.__zoomed_scroll_up(event_in)
                    else:
                        self.__zoomed_scroll_down(event_in)

                elif event_in.num == 4 or event_in.delta > 0:  # scroll up
                    if self.__manga:
                        self.__zoomed_scroll_down(event_in)
                    else:
                        self.__zoomed_scroll_up(event_in)

    def __zoomed_scroll_up(self, event_in: tkinter.Event):
        (top, bottom), (left, right) = self.__canvas.yview(), self.__canvas.xview()
        if ((self.__manga and bottom == 1.0) or
                (not self.__manga and top == 0.0)):
            if left <= 0.1:
                pages = self.pages
                self.turn_page(event_in)
                if pages != self.pages:
                    if self.context.double and self.narrow:
                        self.__canvas.xview_moveto(1.0)
                    else:
                        self.__center_viewport()
                    self.__canvas.yview_moveto(0.0 if self.__manga else 1.0)
            else:
                if self.narrow:
                    self.__canvas.xview_moveto(0.0)
                self.__canvas.yview_moveto(0.0 if self.__manga else 1.0)
        else:
            self.__canvas.yview_scroll(
                int(-1 * (event_in.delta / 120)), "units")

    def __zoomed_scroll_down(self, event_in: tkinter.Event):
        (top, bottom), (left, right) = self.__canvas.yview(), self.__canvas.xview()
        if ((self.__manga and top == 0.0) or
                (not self.__manga and bottom == 1.0)):
            if 0.5 <= left or 0.9 <= right or len(self.pages) < 2:
                pages = self.pages
                self.turn_page(event_in)
                if pages != self.pages:
                    if self.context.double and self.narrow:
                        self.__canvas.xview_moveto(0.0)
                    else:
                        self.__center_viewport()
                    self.__canvas.yview_moveto(1.0 if self.__manga else 0.0)
            else:
                if self.narrow:
                    self.__canvas.xview_moveto(0.5)
                self.__canvas.yview_moveto(1.0 if self.__manga else 0.0)
        else:
            self.__canvas.yview_scroll(
                int(-1 * (event_in.delta / 120)), "units")

    @typing.override
    def turn_page(self, event_in: tkinter.Event):
        if self.orientation[1] == "pages":
            super().turn_page(event_in)

    def __render_shadows(self):
        try:
            size = (sum(d.width for d in self.__canvas.drawers),
                    max(d.height for d in self.__canvas.drawers))
            self.__shadow = PIL.Image.new("RGBA", size)
            center = self.__canvas.drawers[0].width
            for resize, shadow in self.__SHADOWS:
                overlay = resize(PIL.Image.open(shadow), size, PIL.Image.LANCZOS)
                self.__shadow.paste(overlay, (center - (overlay.width // 2), 0), overlay)
            self.__shadow = PIL.ImageTk.PhotoImage(self.__shadow)
            self.__canvas.coords(self.__shadow_id, self.page_bbox[0][0], 0)
        except (ZeroDivisionError, IndexError) as error:
            pass
        finally:
            self.__set_shadow()

    def __set_shadow(self):
        if self.context.shadows and len(self.pages) > 1:
            self.__canvas.itemconfig(self.__shadow_id, image=self.__shadow)
            self.__canvas.tag_raise(self.__shadow_id, tkinter.ALL)
        else:
            self.__canvas.itemconfig(self.__shadow_id, image=None)
            self.__canvas.tag_lower(self.__shadow_id, tkinter.ALL)

    def __set_double(self):
        self.clear_scroll()
        if self.context.double:
            self.orientation = readframe.DOUBLE_PAGES
            self.pages = [p for p in self.comic.pairs if min(self.pages) in p][0]
        else:
            self.orientation = readframe.SINGLE_PAGES
            self.pages = [min(self.pages)]
        self.draw()

    def __page_enter(self):
        self.__canvas.config(cursor=self.__openhand)

    def __page_leave(self):
        self.__canvas.config(cursor="")

    def __draw_test_params(self):
        # self.__canvas.update_idletasks()
        [self.__canvas.delete(id) for id in self.__objects]
        self.__objects = []
        colors = ["red", "blue", "green"]
        for bbox, color in zip(self.page_bbox, colors):
            if bbox is not None:
                self.__objects.append(
                    self.__canvas.create_rectangle(
                        bbox[0], bbox[1], bbox[2], bbox[3],
                        width=5, outline=color))
        self.__objects.append(
            self.__canvas.create_rectangle(
                self.bbox[0], self.bbox[1], self.bbox[2], self.bbox[3],
                width=5, outline="black"))

    @typing.override
    def _draw(self, pages_in: list[int] = None,
               reverse_in: bool = False,
               progress_in: popup.ProgressBar = None):
        if self.orientation[1] == "pages":
            self.__pages_draw(pages_in, reverse_in, progress_in)
        elif self.orientation[1] == "scroll":
            self.__scroll_draw(None, progress_in) # (pages_in)

        # Allow waiting threads to continue.
        self._page_drawing = False
        self._draw_id = None

    # <--- AI Generated solutions ---> #
    def __pages_draw(self, pages_in: list[PIL.Image.Image] = None, reverse_in: bool = False,
                     progress_in: popup.ProgressBar = None):
        """Calculates layouts and perfectly centers single or double page spreads."""
        pages = [(self.comic[p] if p is not None else None) for p in (
            pages_in if pages_in is not None else self.pages)]
        pages = list(reversed(pages)) if (
            self.__manga) else pages
        if progress_in is not None:
            progress_in.max = len(pages_in) + 1

        if self.__canvas.drawers[0].image is None:
            # Move the center image right.
            pass
        elif self.__canvas.drawers[1].image is None:
            # Move the center image left
            pass

        # Draw the page images on the canvas
        items = list(enumerate(zip(self.__canvas.drawers, pages, pages_in)))
        reverse = not reverse_in if self.__manga else reverse_in
        total_width, max_width, total_height, max_height = 0, 0, 0, 0
        for i, (drawer, page, number) in (items if reverse else reversed(items)):
            if progress_in is not None:
                progress_in.text = f"Drawing: {page.filename}..."
            if len(pages) > 1 and self.context.animate:
                drawer.change(page, reverse, i)
            else:
                drawer.image = page

            total_width, max_width, total_height, max_height = (
                total_width + drawer.width, max(max_width, drawer.width),
                total_height + drawer.height, max(max_height, drawer.height))
            if progress_in is not None:
                progress_in.progress()

        # Arrange the images on the canvas
        if self.__pair_len(pages) > 1:
            self.__canvas.drawers[0].coords(-self.__canvas.drawers[0].width, 0)
            self.__canvas.drawers[1].coords(0, 0)
        else:
            self.__canvas.drawers[1].image = None
            self.__canvas.drawers[0].coords(-(self.__canvas.drawers[0].width // 2), 0)

        self.__canvas.update_idletasks()
        self.__canvas.config(
            scrollregion=(
                -(total_width // 2), 0,
                 (total_width // 2), max_height))

        self.__render_shadows()

        # # Force the canvas view to center itself over coordinate (0, 0) smoothly
        # self.update_idletasks()
        self.__center_viewport()

        if progress_in is not None:
            progress_in.progress()

        if self._DEBUG:
            self.__draw_test_params()

    def __scroll_draw(self, pages_in: list[PIL.Image.Image] = None,
                      progress_in: popup.ProgressBar = None):
        self.__canvas.drawers[0].image, self.__canvas.drawers[1].image = None, None
        pages_in = pages_in if pages_in is not None else (
            self.comic.pages if self.comic is not None else [])
        if progress_in is not None:
            progress_in.max = len(pages_in)
        self.__canvas.images, self.__canvas.image_ids, x, y, width, height = [], [], 0, 0, 0, 0
        size = (
            300000 if self.orientation == readframe.HORIZONTAL_SCROLL else int(self.size[0] * self.scale),
            300000 if self.orientation == readframe.VERTICAL_SCROLL else int(self.size[1] * self.scale))
        for page in pages_in:
            if progress_in is not None:
                progress_in.text = f"Drawing: {pathlib.Path(page.filename).name}..."
            self.__canvas.images.append(
                PIL.ImageTk.PhotoImage(
                    PIL.ImageOps.contain(
                        page, size)))
            self.__canvas.image_ids.append(
                self.__canvas.create_image(
                    x, y, image=self.__canvas.images[-1],
                    anchor=tkinter.NW, tag="scroll"))
            if self.orientation == readframe.VERTICAL_SCROLL:
                y += self.__canvas.images[-1].height()
                width, height = max(width, self.__canvas.images[-1].width()), y
            elif self.orientation == readframe.HORIZONTAL_SCROLL:
                x += self.__canvas.images[-1].width()
                width, height = x, max(height, self.__canvas.images[-1].height())
            else:
                raise ValueError(
                    f"Invalid Orientation: {self.orientation}")

            if progress_in is not None:
                progress_in.progress()
        self.__canvas.config(
            scrollregion=(0, 0, width, height))

    def __center_viewport(self):
        """Keeps the viewport locked to the center when content is smaller than window."""
        # Avoid running calculation calculations before window draws
        width = self.comic_width

        if self.__canvas.winfo_width() > 1 and self.__canvas.winfo_height() > 1:
            # Horizontally center if the book spread width is narrower than the canvas window
            if 0 < width < self.__canvas.winfo_width():
                x_view = 0.5 - (self.__canvas.winfo_width() / 2) / width
                self.__canvas.xview_moveto(x_view)

    @staticmethod
    def __pair_len(pair_in: tuple | list) -> int:
        return len([p for p in pair_in if p is not None])


if __name__ == '__main__':
    root = tkinter.Tk()
    root.geometry("1200x1200")

    file = pathlib.Path(__file__).parent.parent / "test" / "Watchmen.cbr"
    book = Comic(file, root)
    book.load()
    canvasframe = CanvasReadFrame(root, book)
    canvasframe.pack(fill=tkinter.BOTH, expand=True)
    root.after(50, canvasframe.load)
    root.mainloop()
