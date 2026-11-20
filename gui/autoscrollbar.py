#!/usr/bin/env python3
import tkinter, tkinter.ttk
# For testing..
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.utils import resolver
else:
    from ..utils import resolver


class AutoScrollbar(tkinter.ttk.Scrollbar):
    ICONS = resolver.icon_root()

    """ A scrollbar that hides itself if it's not needed."""
    def __init__(self, master_io, target_in, **kw):
        super().__init__(master_io, **kw)
        self.__taget = target_in
        self.__info = [None, None, None]

    def set(self, low_in, hi_in):
        try:
            manage, info, forget = self.__info
            if float(low_in) <= 0.05 and float(hi_in) >= 0.95:
                if self.winfo_viewable():
                    forget() # Hies the scrollbar
            else:
                if not self.winfo_viewable():
                    manage(**info)
                    if self.__info[0] == self.pack and self.cget('command'):
                        manage, info, forget = self.__get_manager_info(self.__taget)
                        forget()
                        manage(**info)

        except (AttributeError, TypeError) as error:
            print(f"Error: {error}")
        finally:
            super().set(low_in, hi_in)

    def pack(self, **kwargs):
        super().pack(**kwargs)
        self.__info = self.__get_manager_info(self)

    def grid(self, **kwargs):
        super().grid(**kwargs)
        self.__info = self.__get_manager_info(self)

    def place(self, **kwargs):
        super().place(**kwargs)
        self.__info = self.__get_manager_info(self)

    def __get_manager_info(self, widget_in: tkinter.Misc):
        try:
            info = [widget_in.pack, widget_in.pack_info(), widget_in.pack_forget]
            info[1]['in_'] = info[1].pop("in")
        except tkinter.TclError:
            try:
                info = [widget_in.grid, widget_in.grid_info(), widget_in.grid_forget]
            except tkinter.TclError:
                # Allow this to raise an error.
                info = [widget_in.place, widget_in.place_info(), widget_in.place_forget]

        # Place the underscore at the end allows the internal layout
        # wrapper to read the parent container window cleanly.
        if "in" in info[1].keys():
            info[1]['in_'] = info[1].pop("in")
        return info


class Test:
    def __init__(self, root_in):
        self.root = root_in
        self.frame = tkinter.Frame(self.root)
        self.frame.pack(fill=tkinter.BOTH, expand=True)

        # Create the canvas Widget
        self.canvas = tkinter.Canvas(self.frame, bg="gray", bd=2, highlightthickness=2)

        # Create the vertical scrollbar
        self.scrollbary = AutoScrollbar(
            self.frame, self.canvas, orient=tkinter.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbary.set)

        # Create the horizontal scrollbar
        self.scrollbarx = AutoScrollbar(
            self.frame, self.canvas, orient=tkinter.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.scrollbarx.set)

        # Configure the layout manager for thefram.
        self.scrollbary.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.scrollbarx.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.canvas.pack(fill=tkinter.BOTH, expand=True)

        self.canvas.config(scrollregion=(0, 0, 1200, 1200))
        self.text_id = self.canvas.create_text(600, 600, text="", font=("MS Comic Sans", 16))
        self.root.after(1000, self.hide)

    def hide(self):
        self.canvas.itemconfig(self.text_id, text="Hiding Scrollbars!", font=("MS Comic Sans", 16))
        self.canvas.config(scrollregion=(0, 0, 600, 600))
        self.root.after(1000, self.show)

    def show(self):
        self.canvas.itemconfig(self.text_id, text="Showing Scrollbars!", font=("MS Comic Sans", 16))
        self.canvas.config(scrollregion=(0, 0, 3000, 3000))
        self.root.after(1000, self.hide)

if __name__ == '__main__':
    root = tkinter.Tk()
    root.geometry("1200x1200")
    test = Test(root)
    root.mainloop()