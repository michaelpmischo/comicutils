#!/usr/bin/env python3
import sys, pathlib
import PIL.Image, PIL.ImageTk, PIL.ImageOps, tkinter, tkinter.ttk

# For testing..
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.gui import callbackmanager
    from comicutils.comics import comic
else:
    from . import callbackmanager
    from ..comics import comic


# =============================================================================
# ScrollWebFrame
# =============================================================================
class NavigationFrame(callbackmanager.CallbackManager, tkinter.Frame):
    ITEM_PAD = 25
    def __init__(self, master_in: tkinter.Misc, title_in: str = "Navigation", max_width_in: int = None, columns_in: tuple=(), **args_in):
        callbackmanager.CallbackManager.__init__(self, ["selected"])
        tkinter.Frame.__init__(self, master_in, **args_in)
        (self.__comic, self.__locations, self.__photos, self.__ignore_select,
         self.__load_id, self.__resize_id, self.__last_width, self.__max_width,
         self.__loading) = (
            None, {}, [], False, None, None,
            0, max_width_in if max_width_in is not None else 40000,
            tkinter.BooleanVar(self, False))
        self.__navigation = tkinter.ttk.Treeview(
            self, show="tree headings", columns=columns_in)
        self.__navigation.heading("#0", text=title_in)
        self.__navigation.bind("<<TreeviewSelect>>", self.__selected)
        self.bind("<Configure>", self.__resize)
        self.__navigation.pack(padx=0, pady=0, fill=tkinter.BOTH, expand=True)
        self.pack_propagate(False)

    @property
    def selected(self) -> str:
        try:
            return self.__navigation.selection()[0]
        except IndexError as _:
            return None

    @selected.setter
    def selected(self, selected_in: str | int):
        self.__ignore_select = True
        try:
            selected_in = list(self.__locations.keys())[selected_in] if (
                isinstance(selected_in, int)) else selected_in if (
                    isinstance(selected_in, str)) else None
            if selected_in is not None:
                self.__navigation.selection_set(selected_in)
        except IndexError as _:
            return
        finally:
            self.__ignore_select = False

    @property
    def selected_page(self) -> int:
        try:
            return self.__locations[self.__navigation.selection()[0]]
        except (IndexError, KeyError) as _:
            return None

    @selected_page.setter
    def selected_page(self, page_in: int):
        try:
            # Reverse lookup the item by page.
            self.selected = self.__locations[
                list(self.__locations.keys())[page_in]]
        except (IndexError, KeyError) as _:
            raise ValueError(
                f"Invalid Page: {page_in}")

    def load(self, comic_in: comic.Comic = None, page_in: int = None):
        if comic_in is not None:
            self.selected = None
            self.__comic = comic_in
        # Create a progress bar here.
        self.__loading.set(True)
        if self.__load_id is not None:
            self.after_cancel(self.__load_id)
        self.__load_id = self.after(100, self.__load, page_in)

    def __load(self, page_in: int = None):
        if self.__comic is not None:
            self.clear()
            self.__photos, self.__locations = [], {}
            font, style = (tkinter.font.Font(
                family="Helvetica", size=16, weight="bold"),
                           tkinter.ttk.Style())
            width = min(self.__max_width, self.__navigation.winfo_width()) - self.ITEM_PAD
            if width <= 1:
                return
            for i, page in enumerate(self.__comic.pages):
                self.__photos.append(
                    PIL.ImageTk.PhotoImage(
                        PIL.ImageOps.contain(
                            page,
                            (width,
                             round(page.height * width / page.width)),
                            PIL.Image.LANCZOS)))
                self.__locations[self.__navigation.insert(
                    '', tkinter.END, image=self.__photos[-1],
                    open=False)] = i
                self.__navigation.column("#0",
                    width=max(p.width() + self.ITEM_PAD for p in self.__photos))
                style.configure("Treeview", font=font,
                    rowheight=max(p.height() for p in self.__photos))
                self.configure(width=max(p.width() + self.ITEM_PAD for p in self.__photos))

            if page_in:
                self.selected_page = page_in

        # Start at the beginning
        self.__load_id = None
        self.__loading.set(False)

    def clear(self):
        for item in self.__navigation.get_children():
            self.__navigation.delete(item)

    def __selected(self, event_in: tkinter.Event):
        if not self.__ignore_select:
            self._callback("selected", event_in)

    def __resize(self, event_in: tkinter.Event):
        # Only Respond to width changes.
        width = min(self.__max_width, round(event_in.height * 0.3))
        if width != self.__last_width:
            # Debounce The Resizes
            if self.__resize_id is not None:
                self.after_cancel(self.__resize_id)
            self.configure(width=min(self.__max_width, width))
            self.__resize_id = self.after(50, self.___resize, event_in)
            self.__last_width = width

    def ___resize(self, event_in: tkinter.Event):
        self.load()
        self.__resize_id = None


