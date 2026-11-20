#!/usr/bin/env python3
import pathlib, tkinter, tkinter.font, tkinter.ttk, tkinter.filedialog
# For testing..
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.gui2 import callbackmanager
    from comicutils.utils import resolver
else:
    from . import callbackmanager
    from ..utils import resolver


class ViewerContextMenu(callbackmanager.CallbackManager, tkinter.Menu):
    ICONS = resolver.icon_root()

    def __init__(self, master_in: tkinter.Misc, **args_in):
        callbackmanager.CallbackManager.__init__(
            self, ["open", "fit", "double", "shadow", "animate", "nav",
                   "extract", "add", "delete", "convert", "from-dir", "from-files",
                   "exit"])
        tkinter.Menu.__init__(self, master_in, **args_in)

        self.__font = args_in["font"] if "font" in args_in.keys() else ("Arial", 12)
        self.__italic = self.__font + ("italic",)
        self.__bold = self.__font + ("bold",)

        # Variables
        self.__shadow = tkinter.BooleanVar(self)
        self.__shadow.set(True)
        self.__double = tkinter.BooleanVar(self)
        self.__double.set(True)
        self.__animate = tkinter.BooleanVar(self)
        self.__animate.set(True)
        self.__animate.set(True)
        self.__animate.set(True)
        self.__navigation = tkinter.BooleanVar(self)
        self.__navigation.set(False)

        self.add_command(
            label="Open", font=self.__font, command=lambda: self._callback("open"))

        self.add_separator()
        self.add_command(
            label="Fit", font=self.__font, command=lambda: self._callback("fit"))

        self.add_separator()
        self.add_checkbutton(
            label='Double Pages', font=self.__italic, variable=self.__double,
            onvalue=True, offvalue=False,
            command=lambda: self._callback("double"))
        self.add_checkbutton(
            label='Page Shadows', font=self.__italic, variable=self.__shadow,
            onvalue=True, offvalue=False,
            command=lambda: self._callback("shadow"))
        self.add_checkbutton(
            label='Animate Page Turns', font=self.__italic, variable=self.__animate,
            onvalue=True, offvalue=False,
            command=lambda: self._callback("animate"))
        self.add_checkbutton(
            label='Page Previews', font=self.__italic, variable=self.__navigation,
            onvalue=True, offvalue=False,
            command=lambda: self._callback("nav"))

        self.add_separator()
        self.add_command(
            label="Add Page", font=self.__font, command=lambda: self._callback("add"))
        self.add_command(
            label="Delete Page", font=self.__font, command=lambda: self._callback("delete"))
        self.add_command(
            label="Convert Comic", font=self.__font, command=lambda: self._callback("convert"))
        self.add_command(
            label="Make Comic from Directory", font=self.__font, command=lambda: self._callback("from-dir"))
        self.add_command(
            label="Make Comic from Files", font=self.__font, command=lambda: self._callback("from-files"))
        self.add_command(
            label="Extract Comic", font=self.__font, command=lambda: self._callback("extract"))

        self.add_separator()
        self.add_command(
            label="Exit", font=self.__font, command=lambda: self._callback("exit"))

    @property
    def double(self) -> bool:
        return self.__double.get()

    @double.setter
    def double(self, double_in: bool):
        if isinstance(double_in, bool):
            self.__double.set(double_in)
            self._callback("double")
        else:
            raise ValueError(
                f"Invalid Double: {double_in}")

    @property
    def shadows(self) -> bool:
        return self.__shadow.get()

    @property
    def animate(self) -> bool:
        return self.__animate.get()

    @animate.setter
    def animate(self, animate_in: bool):
        if isinstance(animate_in, bool):
            self.__animate.set(animate_in)
            self._callback("animate")
        else:
            raise ValueError(
                f"Invalid Animate: {animate_in}")

    @property
    def navigation(self) -> bool:
        return self.__navigation.get()


class ViewerMenu(callbackmanager.CallbackManager, tkinter.Menu):
    def __init__(self, master_in: tkinter.Misc, **args_in):
        callbackmanager.CallbackManager.__init__(self, ["open", "exit", "double", "shadow", "fit"])
        tkinter.Menu.__init__(self, master_in, **args_in)

        self.__font = args_in["font"] if "font" in args_in else ("Arial", 14, "bold")
        self.__italic = self.__font + ("italic",)
        self.__bold = self.__font + ("bold",)

        # 1. Fetch the exact global font container used by Windows menubars
        font = tkinter.font.nametofont("TkMenuFont")

        # 2. Modify its properties in-place
        # This scales the top-level horizontal items AND the drop-downs simultaneously!
        font.configure(family=self.__font[0], size=self.__font[1], weight="bold")

        self.__path = pathlib.Path.cwd()

        # Variables
        self.__shadow = tkinter.BooleanVar(self, value=True)
        self.__double = tkinter.BooleanVar(self, value=True)

        # Menu Items
        self.__file = tkinter.Menu(self, tearoff=False, font=self.__font)
        self.__file.add_command(
            label="Open", command=lambda: self._callback("open"))
        self.__file.add_separator()
        self.__file.add_command(
            label="Exit", command=lambda: self._callback("exit"))
        self.add_cascade(label="File", menu=self.__file, font=self.__bold)
        self.__view = tkinter.Menu(self, tearoff=False,  font=self.__font)
        self.__view.add_checkbutton(
            label='Double Pages', font=self.__italic, variable=self.__double,
            onvalue=True, offvalue=False,
            command=lambda: self._callback("double"))
        self.__view.add_checkbutton(
            label='Page Shadows', font=self.__italic, variable=self.__shadow,
            onvalue=True, offvalue=False,
            command=lambda: self._callback("shadow"))
        self.__view.add_separator()
        self.__view.add_command(
            label="Fit View", font=self.__italic, command=lambda: self._callback("fit"))
        self.add_cascade(label="View", menu=self.__view, font=self.__bold)

    @property
    def double_pages(self) -> bool:
        return self.__double.get()

    @property
    def page_shadows(self) -> bool:
        return self.__shadow.get()