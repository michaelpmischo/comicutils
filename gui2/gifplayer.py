#!/usr/bin/env python3
import tkinter, pathlib, types, typing
import PIL, PIL.Image, PIL.ImageTk, PIL.ImageOps, PIL.ImageSequence


# =============================================================================
# AnimatedDrawer
# =============================================================================
class AnimatedDrawer:
    def __init__(self, master_in: tkinter.Misc, image_in: PIL.Image.Image = None):
        (self.__master, self.__image, self.__scale, self.__frames, self.__id,
         self.__resize_id, self._photo, self.__auto_resize) = (
            master_in, image_in, 1.0, [], None, None, None, False)
        self.__size = (self.__master.winfo_width(), self.__master.winfo_height())
        self.__master.bind('<Configure>', self.__resize)

    @property
    def image(self) -> PIL.Image.Image:
        return self.__image

    @image.setter
    def image(self, image_in: PIL.Image.Image):
        if isinstance(image_in, (PIL.Image.Image, types.NoneType)):
            self.__image = image_in
            self.contain()
            self.draw()
        else:
            raise TypeError(
                f"Invalid Image: {type(
                    image_in).__name__}")

    @property
    def scale(self) -> float:
        return self.__scale

    @scale.setter
    def scale(self, scale_in: float):
        if isinstance(scale_in, float):
            self.__scale = scale_in
        else:
            raise ValueError(f"Invalid Scale: {scale_in}")

    @property
    def frames(self) -> list[PIL.Image.Image]:
        return self.__frames

    @property
    def size(self) -> tuple:
        return self.width, self.height

    @property
    def width(self) -> int:
        try:
            return self.__frames[0][0].width
        except (IndexError, AttributeError) as _:
            return 0

    @property
    def height(self) -> int:
        try:
            return self.__frames[0][0].height
        except (IndexError, AttributeError) as _:
            return 0

    @property
    def auto_resize(self) -> bool:
        return self.__auto_resize

    @auto_resize.setter
    def auto_resize(self, resize_in: bool):
        self.__auto_resize = resize_in

    def draw(self, frame_in: int = 0):
        if len(self.__frames) > 1:
            duration = self.__frames[frame_in][1]
            self.__id = self.__master.after(
                duration, self.draw, (frame_in + 1) % len(self.__frames))

    def stop(self):
        if self.__id is not None:
            self.__master.after_cancel(self.__id)
            self.__id = None

    def __resize(self, event_in: tkinter.Event):
        if self.__auto_resize:
            if self.__resize_id is not None:
                self.__master.after_cancel(self.__resize_id)
            self.__resize_id = self.__master.after(
                20, self.resize, (event_in.width, event_in.height))

    def resize(self, size_in: tuple[int, int]):
        self.contain()
        self.draw()
        self.__resize_id = None

    def contain(self, size_in: tuple = None):
        self.__frames = []
        size_in = size_in if size_in is not None else tuple(
            round(s * self.__scale) for s in [
                self.__master.winfo_width(),
                self.__master.winfo_height()])
        while self.__image is not None:
            try:
                self.__image.seek(len(self.__frames))
                self.__frames.append((
                    PIL.ImageOps.contain(
                        self.__image.copy(),
                        size_in, PIL.Image.LANCZOS),
                    self.__image.info.get('duration', 100)))
            except EOFError as _:
                return
            finally:
                self.__image.seek(0)
                # self.draw()
        self.__frames = []

    def __del__(self):
        self.stop()


# =============================================================================
# AnimatedLabelDrawer
# =============================================================================
class AnimatedLabelDrawer(AnimatedDrawer, tkinter.Label):
    def __init__(self, master_in: tkinter.Misc, image_in: PIL.Image.Image = None, **args_in):
        tkinter.Label.__init__(self, master_in, **args_in)
        AnimatedDrawer.__init__(self, self, image_in)
        self.image = image_in

    def draw(self, frame_in: int = 0):
        if len(self.frames) > 0:
            self._photo = PIL.ImageTk.PhotoImage(
                self.frames[frame_in][0])
        else:
            self._photo = None
        self.config(image=self._photo)
        super().draw(frame_in)


# =============================================================================
# AnimatedCanvasDrawer
# =============================================================================
class AnimatedCanvasDrawer(AnimatedDrawer):
    def __init__(self, canvas_in: tkinter.Canvas, image_in: PIL.Image.Image = None, x_in: int = 0, y_in: int = 0, **args_in):
        super().__init__(canvas_in, image_in)
        self.__page_change, self.__change_id = tkinter.BooleanVar(canvas_in, value=False), None
        self.__canvas, self.__x, self.__y = canvas_in, x_in, y_in
        self.__image_id = self.__canvas.create_image(
                self.__x, self.__y, **args_in)
        self.image = image_in

    @property
    def image_id(self) -> int:
        return self.__image_id

    def wait_page_change(self):
        self.__canvas.wait_variable(self.__page_change)

    def change(self, image_in: PIL.Image.Image, reverse_in: bool = False, page_in: int = 0):
        self.__page_change.set(True)
        if self.__change_id is not None:
            self.__canvas.after_cancel(self.__change_id)
        self.__change_id = self.__canvas.after(50, self.__change, image_in, reverse_in, page_in)
        self.wait_page_change()

    def __change(self, image_in: PIL.Image.Image, reverse_in: bool = False, page_in: int = 0,
                 value_in: int = 1, max_in: int = 5, delay_in: int = 250):
        if isinstance(image_in, (PIL.Image.Image, types.NoneType)):
            if (value_in < max_in and page_in >= 0 and self.image is not None and
                    self.image.filename != image_in.filename):
                return self.___change(
                    image_in, reverse_in, page_in,
                    value_in, max_in, delay_in)

            self.__page_change.set(False)
            self.image = image_in
            self.__canvas.tag_raise("links")

        else:
            raise ValueError(
                f"Invalid Image: {type(image_in).__name__}")

    def ___change(self, image_in: PIL.Image.Image, reverse_in: bool = False, page_in: int = 0,
                  value_in: int = 1, max_in: int = 5, delay_in: int = 250):
        size = tuple(round(s * self.scale) for s in [
            self.__canvas.winfo_width(),
            self.__canvas.winfo_height()])
        ratio1, ratio2 = (
            max(1 / max_in, value_in / max_in),
            min((max_in - 1) / max_in, 1 - value_in / max_in))

        # pages[0] is bottom pages[1] is top
        pages = [PIL.ImageOps.contain(i, size, PIL.Image.LANCZOS) for i in ([
            image_in.copy(), self.image.copy()] if (reverse_in ^ page_in & 0x1) else [
                self.image.copy(), image_in.copy()])]
        width1, width2 = round(pages[0].width * ratio2), round(pages[0].width * ratio1)

        # Resize the top page.
        top_width, bottom_width = (width1, width2) if (
                reverse_in ^ page_in & 0x1) else (width2, width1)

        # Paste the top image onto the bottom image.
        pages[1] = pages[1].resize(
            (top_width, pages[1].height),
            PIL.Image.LANCZOS)
        pages[0].paste(pages[1], ((0, 0) if page_in & 0x1 else (bottom_width, 0)))
        self.draw(pages[0])
        self.__id = self.__canvas.after(
            round(delay_in / max_in), self.__change, image_in, reverse_in, page_in, value_in + 1)

    def draw(self, frame_in: int | PIL.Image.Image = 0):
        try:
            self._photo = PIL.ImageTk.PhotoImage(
                (frame_in if isinstance(frame_in, PIL.Image.Image) else
                 self.frames[frame_in][0]))
            self.__canvas.itemconfig(
                self.__image_id,
                image=self._photo)
            self.__canvas.tag_raise("links")
            super().draw(frame_in)
        except IndexError as _:
            self._photo = None
            self.__canvas.itemconfig(
                self.image_id,
                image=self._photo)
            self.__canvas.tag_raise("links")

    def itemconfig(self, **kwargs_io):
        if self.image is not None:
            self.__canvas.itemconfig(
                self.__image_id, **kwargs_io)
            self.__canvas.tag_raise("links")

    def coords(self, x_in: int, y_in: int, **kwargs_in):
        self.__canvas.coords(
            self.image_id, x_in, y_in, **kwargs_in)

    def cget(self, item_in: str) -> any:
        return  self.__canvas.itemcget(self.__image_id, item_in)


# --- Application Setup ---
if __name__ == "__main__":
    root = tkinter.Tk()
    root.title("Tkinter Canvas GIF Player")
    root.geometry("1200x1200")
    root.update_idletasks()
    canvas = tkinter.Canvas(root)
    canvas.pack(fill=tkinter.BOTH, expand=True)
    player = AnimatedCanvasDrawer(canvas, None, 0, 0, anchor=tkinter.NW)
    #player.auto_resize = True
    player.image = PIL.Image.open(pathlib.Path(__file__).parent / "icons" / "comic1.png")
    if not player.auto_resize:
        root.after(50, player.contain)
        root.after(100, player.draw)
    root.mainloop()
    
# --- Application Setup ---
if __name__ == "__main__":
    root = tkinter.Tk()
    root.title("Tkinter GIF Player")
    root.geometry("1200x1200")
    player = AnimatedLabelDrawer(root)
    player.pack(fill=tkinter.BOTH, expand=True)
    #player.auto_resize = True
    player.image = PIL.Image.open(pathlib.Path(__file__).parent / "icons" / "test.gif")
    if not player.auto_resize:
        root.after(50, player.contain)
    root.mainloop()
