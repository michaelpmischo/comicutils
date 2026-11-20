#!/usr/bin/env python3
import pathlib, PIL.Image, PIL.ImageTk, PIL.ImageOps, tkinter, tkinter.ttk, tkinter.filedialog
from typing import overload
from ..comics.comic import Comic
from . import progress, autoscrollbar, callbackmanager, menubar, resolver


class ScrollZoomCanvas(callbackmanager.CallbackManager, tkinter.Frame):
    DEBUG = False
    BACKGROUND = "gray"
    DELTA = 1.1
    ICONS = resolver.icon_root()
    SHADOWS = [
        (PIL.ImageOps.contain, ICONS / "bookshadow.png")]
        # (PIL.Image.Image.resize, ICONS / "bookshadow2.png")]

    def __init__(self, master_in: tkinter.Misc, comic_in: str | pathlib.Path | Comic = None, **args_in):
        callbackmanager.CallbackManager.__init__(self, ["page", "scale"])
        self.__font = args_in.pop("font") if "font" in args_in.keys() else ("Impact", 18)
        tkinter.ttk.Frame.__init__(self, master_in)
        self.__objects = []
        self.__page_bounds = []
        self.__page_turning = False
        self.__comic = Comic(comic_in) if (
            isinstance(comic_in, (str, pathlib.Path))) else comic_in
        self.__scale, self.__pages = 1.0, []
        self.__wait = tkinter.BooleanVar(self, value=False)
        self.__draw_id = None

        self.__grabbed = False
        self.__openhand = f"@{self.ICONS / "open-hand.cur"}".replace('\\', '/')
        self.__closehand = f"@{self.ICONS / "close-hand.cur"}".replace('\\', '/')

        self.__context = menubar.ViewerContextMenu(self, tearoff=False, font=self.__font)
        self.__context.subscribe("double", self.__set_double)
        self.__context.subscribe("shadow", self.__set_shadow)
        self.__context.subscribe("fit", self.fit)
        self.__context_event = None

        # Create the canvas Widget
        self.__canvas = tkinter.Canvas(self, bg=self.BACKGROUND, bd=2, highlightthickness=2)
        self.__canvas.image_id = self.__canvas.create_image(0, 0, anchor=tkinter.N, tag="page")
        self.__canvas.tag_bind("page", "<Enter>", lambda event: self.__page_enter())
        self.__canvas.tag_bind("page", "<Leave>", lambda event: self.__page_leave())

        # Create the vertical scrollbar
        self.__yscrollbar = autoscrollbar.AutoScrollbar(
            self, self.__canvas, orient=tkinter.VERTICAL, command=self.__canvas.yview)
        self.__canvas.configure(yscrollcommand=self.__yscrollbar.set)

        # Create the horizontal scrollbar
        self.__xscrollbar = autoscrollbar.AutoScrollbar(
            self, self.__canvas, orient=tkinter.HORIZONTAL, command=self.__canvas.xview)
        self.__canvas.configure(xscrollcommand=self.__xscrollbar.set)

        # Configure the layout manager for the fram.
        self.__yscrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.__xscrollbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.__canvas.pack(fill=tkinter.BOTH, expand=True)

        # Bond Events
        self.bind("<Configure>", self.__resize)
        self.bind_all("<MouseWheel>", self.__scroll)
        self.bind_all("<Button-4>", self.__scroll)
        self.bind_all("<Button-5>", self.__scroll)
        self.bind_all("<Control-MouseWheel>", self.__zoom)
        self.bind_all("<Control-Button-4>", self.__zoom)
        self.bind_all("<Control-Button-5>", self.__zoom)
        self.__canvas.bind('<ButtonPress-1>', self.__move_from)
        self.__canvas.bind('<B1-Motion>',     self.__move_to)
        self.__canvas.bind("<ButtonRelease-1>", self.__released)
        self.__canvas.bind("<Button-3>", self.__show_context)

        if self.__comic is not None:
            self.comic = self.__comic

    @property
    def comic(self) -> Comic:
        return self.__comic

    @comic.setter
    def comic(self, comic_in: Comic):
        self.__comic = comic_in
        self.pages = [0]
        self.fit()

    @property
    def file(self) -> pathlib.Path:
        if self.__comic is not None:
            return self.__comic.file
        else:
            return pathlib.Path("~").resolve()

    @file.setter
    def file(self, file_in: pathlib.Path):
        self.comic = Comic(file_in)

    @property
    def scale(self) -> float:
        return self.__scale

    @scale.setter
    def scale(self, scale_in: float):
        self.__scale = max(0.1, min(scale_in, 10.0))
        self._callback("scale")
        self.draw()

    @property
    def pages(self) -> list:
        return self.__pages

    @pages.setter
    def pages(self, pages_in: list):
        pages = [p for p in pages_in if 0 <= p < self.__comic.number_of_pages][:(2 if self.__context.double else 1)]
        if len(pages):
            self.__pages = pages
            self.draw()
            self._callback("page")

    @property
    def names(self) -> list[str]:
        if self.__comic is not None:
            return [self.__comic.pages[p] for p in self.__pages]
        else:
            return []

    @property
    def double(self) -> bool:
        return self.__context.double

    @property
    def shadows(self) -> bool:
        return self.__context.shadows

    @property
    def context(self) -> menubar.ViewerContextMenu:
        return self.__context

    @property
    def context_event(self) -> tkinter.Event:
        return self.__context_event

    def which_page(self, location_in: tuple | tkinter.Event) -> int | None:
        if isinstance(location_in, tkinter.Event):
            x, y = location_in.x, location_in.y
        else:
            x, y = location_in[0], location_in[1]
        for page, bbox in zip(self.__pages, self.__page_bounds):
            if bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]:
                return page
        return None

    def wait(self):
        self.wait_variable(self.__wait)
        pass

    def fit(self):
        self.__scale = 1.0
        self.draw()
        self.__center_x()

    def draw(self):
        if self.__comic is not None:
            if self.__draw_id is not None:
                self.after_cancel(self.__draw_id)
            self.__draw_id = self.after(50, self.__draw, self.__pages)
            self.wait()

    def first_page(self):
        self.pages = [0]

    def next_page(self) -> list:
        try:
            self.pages = [max(self.__pages) + 1, max(self.__pages) + 2] if (
                self.__context.double) else [max(self.__pages) + 1]
        except ValueError as _:
            self.__pages = [0]
        return self.__pages

    def prev_page(self) -> list:
        try:
            self.pages = [min(self.__pages) - 2, min(self.__pages) - 1] if (
                self.__context.double) else [min(self.__pages) - 1]
        except ValueError as _:
            self.__pages = [0]
        return self.__pages

    def last_page(self) -> list:
        self.__pages = [self.comic.number_of_pages | (0x1 if self.__context.double else 0x0)]
        return self.prev_page()

    def zoom_in(self, x_in: int = None, y_in: int = None):
        """ Zoom in with button """
        self.zoom(
            (self.__canvas.winfo_width() // 2) if x_in is None else x_in,
            (self.__canvas.winfo_height() // 2) if y_in is None else y_in,
            True)

    def zoom_out(self, x_in: int = None, y_in: int = None):
        """ Zoom out with button """
        self.zoom(
            (self.__canvas.winfo_width() // 2) if x_in is None else x_in,
            (self.__canvas.winfo_height() // 2) if y_in is None else y_in,
            False)

    def zoom(self, x_in: int, y_in: int, zoom_in: bool):
        """ Zoom with position """
        self.__scale, scale = (
            self.__scale * self.DELTA, 1.0 * self.DELTA) if (
            zoom_in) else (
            self.__scale / self.DELTA, 1.0 / self.DELTA)
        self.__canvas.scale('all', x_in * scale, y_in * scale, scale, scale)
        self.scale = self.__scale

    def __resize(self, event_in: tkinter.Event):
        self.update_idletasks()
        self.draw()

    def __move_from(self, event_in: tkinter.Event):
        """ Remember previous coordinates for scrolling with the mouse """
        try:
            if (self.__bbox[0] <= event_in.x <= self.__bbox[2] and
                    self.__bbox[1] <= event_in.y <= self.__bbox[3]):
                self.__grabbed = True
                self.__canvas.configure(cursor=self.__closehand)
                self.__canvas.scan_mark(
                    event_in.x, event_in.y)
        except AttributeError as _:
            pass

    def __move_to(self, event_in: tkinter.Event):
        """ Drag (move) canvas to the new position """
        if self.__grabbed:
            self.__canvas.scan_dragto(
                event_in.x, event_in.y, gain=1)

    def __released(self, event_in: tkinter.Event):
        if self.__grabbed:
            self.__canvas.configure(cursor=self.__openhand)
            self.__grabbed = False

    def __zoom(self, event_in: tkinter.Event):
        """ Zoom with mouse wheel """
        self.zoom(
            event_in.x,
            event_in.y,
            event_in.num == 4 or event_in.delta > 0)

    def __scroll(self, event_in: tkinter.Event):
        """ Zoom with mouse wheel """
        if self.__comic is not None and not self.__page_turning:
            if self.__scale <= 1.0:
                self.__turn_page(event_in)
            else:
                self.__zoomed_scroll(event_in)

    def __zoomed_scroll(self, event_in: tkinter.Event):
        top, bottom = self.__canvas.yview()
        left, right = self.__canvas.xview()
        if event_in.num == 5 or event_in.delta < 0:  # scroll down
            if bottom == 1.0:
                if 0.5 <= left or 0.9 <= right or len(self.__pages) < 2:
                    pages = self.__pages
                    self.__turn_page(event_in)
                    if pages != self.__pages:
                        if len(self.__pages) > 1:
                            self.__canvas.xview_moveto(0.0)
                        else:
                            self.__center_x()
                        self.__canvas.yview_moveto(0.0)
                else:
                    self.__canvas.xview_moveto(0.5)
                    self.__canvas.yview_moveto(0.0)
            else:
                self.__canvas.yview_scroll(int(-1 * (event_in.delta / 120)), "units")
        elif event_in.num == 4 or event_in.delta > 0:  # scroll up
            if top == 0.0:
                if left <=  0.1:
                    pages = self.__pages
                    self.__turn_page(event_in)
                    if pages != self.__pages:
                        if len(self.__pages) > 1:
                            self.__canvas.xview_moveto(1.0)
                        else:
                            self.__center_x()
                        self.__canvas.yview_moveto(1.0)
                else:
                    self.__canvas.xview_moveto(0.0)
                    self.__canvas.yview_moveto(1.0)
            else:
                self.__canvas.yview_scroll(int(-1 * (event_in.delta / 120)), "units")

    def __turn_page(self, event_in: tkinter.Event):
        if self.__page_turning:
            return
        self.__page_turning = True
        if event_in.num == 5 or event_in.delta < 0:  # scroll down
            self.next_page()
        elif event_in.num == 4 or event_in.delta > 0:  # scroll up
            self.prev_page()
        self.after(250, setattr, self, f"_{self.__class__.__name__}__page_turning", False)

    def __draw(self, pages_in: list[int]):
        try:
            size = (round(max(self.__canvas.winfo_width(), 100) / 2 * self.__scale),
                    round(max(self.__canvas.winfo_height(), 100) * self.__scale))
            self.__canvas.scaled = self.__scale_pages(
                [self.__comic[p] for p in pages_in], size[1])
            self.__canvas.photo = PIL.ImageTk.PhotoImage(self.__join_pages(self.__canvas.scaled))
            working_w = max(max(self.__canvas.winfo_width(), 100), self.__canvas.photo.width())
            self.__canvas.coords(self.__canvas.image_id, working_w // 2, 0)
            self.__canvas.itemconfig(self.__canvas.image_id, image=self.__canvas.photo, anchor=tkinter.N)

            # CRITICAL FIX: Only change the scrollregion layout frame if it actually shifted.
            # Wiping this variable string per frame forces a graphics rendering flush loop.
            current_scroll = [int(x) for x in self.__canvas.cget("scrollregion").split()] if (
                self.__canvas.cget("scrollregion")) else []
            target_scroll = [0, 0, working_w, self.__canvas.photo.height()]
            if current_scroll != target_scroll:
                self.__canvas.configure(
                    scrollregion=(0, 0, working_w, self.__canvas.photo.height()))

            self.__bbox = self.__canvas.bbox(self.__canvas.image_id)

            # Set the page bounds so that we can use them for click actions.
            self.__page_bounds = []
            sizes = [i.size for i in self.__canvas.scaled]
            shift_x, shift_y = self.__bbox[0], self.__bbox[1]
            for size in sizes:
                self.__page_bounds.append(
                    (shift_x,
                     shift_y,
                     shift_x + size[0],
                     shift_y + size[1]))
                shift_x += size[0]

            if self.DEBUG:
                self.__draw_test_params()

        finally:
            # Signal Completion
            self.__wait.set(not self.__wait.get())
            self.__draw_id = None

    def __scale_pages(self, images_in: list[PIL.Image.Image], height_in: int) -> list[PIL.Image.Image]:
        return [PIL.ImageOps.contain(i, (round(i.width / i.height * height_in), height_in)) for i in images_in]

    def __join_pages(self, images_in: list[PIL.Image.Image]) -> PIL.Image.Image:
        image, (x,y) = PIL.Image.new('RGBA',
            (sum(i.width for i in images_in),
             max(i.height for i in images_in))), (0, 0)
        for i in images_in:
            image.paste(i, (x, y))
            x += i.width
        return self.__add_shadows(image, images_in[0].width) if len(images_in) > 1 else image

    def __add_shadows(self, image_in: PIL.Image.Image, center_in: int = None, brightness_in: int = 0) -> PIL.Image.Image:
        if self.__context.shadows:
            for resize, shadow in self.SHADOWS:
                center_in = center_in if center_in is not None else image_in.width / 2
                overlay = resize(
                    PIL.Image.open(shadow),
                    (image_in.width, image_in.height),
                    PIL.Image.LANCZOS)
                image_in.paste(overlay, (round(center_in - overlay.width / 2), 0), overlay)
        return image_in

    def __set_shadow(self):
        self.draw()

    def __set_double(self):
        pages = [p for p in self.__pages if (self.__context.double or p & 0x1 or p == 0)]
        if self.__context.double and len(pages) == 1:
            if pages[0] & 0x1:
                pages.append(pages[0] + 1)
            else:
                pages.insert(0, pages[0] - 1)
        self.pages = pages

    def __show_context(self, event_in: tkinter.Event):
        try:
            self.__context_event = event_in
            self.context.tk_popup(event_in.x_root, event_in.y_root)
        finally:
            self.context.grab_release()

    def __center_x(self, y_in: float = None):
        try:
            # self.__canvas.update_idletasks()
            if not hasattr(self.__canvas, "image_id"):
                return
            try:
                scroll_bbox = self.__canvas.cget("scrollregion").split()
                canter_x = (float(scroll_bbox[2]) - float(scroll_bbox[0])) * sum(self.__canvas.xview()) / 2
            except IndexError as _:
                canter_x = self.__canvas.winfo_width() / 2
            try:
                current_x, current_y = self.__canvas.coords(
                    self.__canvas.image_id)[:2]
            except Exception as error:
                current_x, current_y = 0, 0
                print(f"{error}")
            if y_in is not None:
                current_y = current_y + (y_in * self.__canvas.photo.height())

            self.__canvas.coords(self.__canvas.image_id, canter_x, current_y)
            self.__canvas.itemconfig(self.__canvas.image_id, anchor=tkinter.N)

        except (AttributeError, TypeError) as _:
            if self.DEBUG:
                print(f"Centering Error: {error}")

    def __page_enter(self):
        self.__canvas.config(cursor=self.__openhand)

    def __page_leave(self):
        self.__canvas.config(cursor="")

    def __draw_test_params(self):
        # self.__canvas.update_idletasks()
        [self.__canvas.delete(id) for id in self.__objects]
        self.__objects = []
        colors = ["red", "blue", "green"]
        for i, bbox in enumerate(self.__page_bounds):
            self.__objects.append(
                self.__canvas.create_rectangle(
                    bbox[0], bbox[1], bbox[2], bbox[3],
                    width=5, outline=colors[i]))


if __name__ == '__main__':
    root = tkinter.Tk()
    root.geometry("1200x1200")
    scrollzoom = ScrollZoomCanvas(root)
    scrollzoom.pack(fill=tkinter.BOTH, expand=True)