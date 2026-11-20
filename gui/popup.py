#!/usr/bin/env python3
import time, tkinter, tkinter.ttk, tkinter.filedialog


# =============================================================================
# Tooltip
# =============================================================================
class Tooltip(tkinter.Frame):
    """
    Add a tooltip to a tkinter widget.
    """

    def __init__(self, widget_in: tkinter.Misc, tip_in: str, delay_in: int = 400,
                 length_in: int = 250, **args_in):
        self.__widget, self.__font, self.__bg, self.__delay, self.__length, self.__id = (
            widget_in,
            (args_in.op("font") if "font" in args_in.keys() else ("Arial", 11, "bold italic")),
            (args_in.op("bg") if "bg" in args_in.keys() else "#FFFF00"),
            delay_in, length_in, None)
        super().__init__(tkinter.Toplevel(self.__widget), background=self.__bg, borderwidth=0, **args_in)
        self.__tip = tkinter.StringVar(self, value=tip_in)
        self.master.wm_overrideredirect(True)
        self.__id = None

        self.__label = tkinter.Label(
            self, textvariable=self.__tip, font=self.__font, justify=tkinter.LEFT,
            background=self.__bg, relief=tkinter.SOLID, borderwidth=0,
            wraplength=self.__length)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.__label.grid(row=0, column=0, sticky=tkinter.NSEW)

        self.__widget.bind("<Enter>", self.__enter)
        self.__widget.bind("<Leave>", self.__leave)
        self.__widget.bind("<ButtonPress>", self.__leave)
        self.hide()
        self.grid()

    @property
    def tip(self) -> str:
        return self.__tip.get()

    @tip.setter
    def tip(self, tip_in: str):
        if isinstance(tip_in, str):
            self.__tip.set(tip_in)
        else:
            raise ValueError(
                f"Invalid Tip: {tip_in}")

    def show(self):
        x, y = self.__get_position()
        self.master.wm_geometry("+%d+%d" % (x, y))
        self.master.deiconify()
        self.__id = None

    def hide(self):
        self.master.withdraw()

    def __enter(self, event_in: tkinter.Event = None):
        self.__schedule()

    def __leave(self, event_in: tkinter.Event = None):
        self.__unschedule()
        self.hide()

    def __schedule(self):
        self.__unschedule()
        self.__id = self.master.after(self.__delay, self.show)

    def __unschedule(self):
        if self.__id is not None:
            self.master.after_cancel(self.__id)
        self.__id = None

    def __get_position(self, tip_delta=(10, 5), pad=(5, 3, 5, 3)):
        screen = self.__widget.winfo_screenwidth(), self.__widget.winfo_screenheight()
        label = (pad[0] + self.__label.winfo_reqwidth() + pad[2],
                 pad[1] + self.__label.winfo_reqheight() + pad[3])

        mouse_x, mouse_y = self.__widget.winfo_pointerxy()
        x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
        x1 = max(0, mouse_x - tip_delta[0] - label[0] if max(0, x1 + label[0] - screen[0]) else x1)
        y1 = max(0, mouse_y - tip_delta[1] - label[1] if max(0, y1 + label[1] - screen[1]) else y1)
        return x1, y1


# =============================================================================
# PopupWindow
# =============================================================================
class PopupWindow(tkinter.Toplevel):

    def __init__(self, title_in: str, master_in=None):
        super().__init__(master_in)
        self.title(title_in)
        self.transient(self.master)  # Keeps popup on top of main window
        self.grab_set()  # Redirects all keyboard/mouse events to this window

    def center(self):
        self.update_idletasks()
        self.geometry(
            f"{self.winfo_width()}x{self.winfo_height()}"
            f"+{self.master.winfo_x() + (self.master.winfo_width() // 2 - self.winfo_width() // 2)}"
            f"+{self.master.winfo_y() + (self.master.winfo_height() // 2 - self.winfo_height() // 2)}")


# =============================================================================
# ProgressBar
# =============================================================================
class ProgressBar(PopupWindow):
    def __init__(self, master_in: tkinter.Misc = None,
                 title_in: str = "Processing...",
                 text_in: str = "Processing...",
                 max_in: int = None):
        super().__init__(title_in, master_in)
        self.__padx, self.__pady = 50, 10
        self.geometry("400x150")
        self.center()
        self.__determinate_progress, self.__indeterminate_progress, self.__active = None, None, None
        self.__text = tkinter.StringVar(self, value=text_in)
        self.__label = tkinter.ttk.Label(
            self, textvariable=self.__text, font=("MS Comic Sans", 13),
            justify=tkinter.LEFT,  wraplength=self.winfo_width() - (1.5 * self.__padx))
        self.__label.pack(
            side=tkinter.TOP, fill=tkinter.BOTH, padx=self.__padx,
            pady=self.__pady, expand=True)

        self.__frame = tkinter.Frame(self)
        self.__determinate_progress = tkinter.ttk.Progressbar(
            self.__frame, orient=tkinter.HORIZONTAL,
            maximum=max_in, mode="determinate")
        self.__indeterminate_progress = tkinter.ttk.Progressbar(
            self.__frame, orient=tkinter.HORIZONTAL,
            mode="indeterminate")
        self.__frame.pack(side=tkinter.BOTTOM, fill=tkinter.X, expand=True)
        if max_in is not None:
            self.max = max_in

    @property
    def text(self) -> str:
        return self.__text.get()

    @text.setter
    def text(self, text_in: str):
        self.__text.set(text_in)

    @property
    def max(self) -> int | None:
        return self.__max

    @max.setter
    def max(self, max_in: int | None):
        if self.__active is not None:
            self.__active.pack_forget()
        if max_in is not None:
            self.__determinate_progress.configure(maximum=max_in)
            self.__determinate_progress.pack(padx=self.__padx, pady=self.__pady, fill=tkinter.BOTH, expand=True)
            self.__active = self.__determinate_progress
        else:
            self.__indeterminate_progress.pack(padx=self.__padx, pady=self.__pady, fill=tkinter.BOTH, expand=True)
            self.__active = self.__indeterminate_progress
        self.update_idletasks()

    def start(self):
        if self.__active is not None:
            self.max = None
            self.__active.start(50)

    def stop(self):
        self.destroy()

    def progress(self, value_in: int = None):
        self.__active["value"] = value_in if (
                value_in is not None) else (
                self.__active["value"] + 1)
        if self.__active["value"] < self.__active["maximum"]:
            self.update_idletasks()
        else:
            self.destroy()


# =============================================================================
# OptionsDialog
# =============================================================================
class OptionsDialog(PopupWindow):

    def __init__(self, title_in: str, prompt_in: str, options_in: list, master_in: tkinter.Misc = None,):
        super().__init__(title_in)
        self.__selected = None

        self.geometry("300x150")
        self.resizable(False, False)

        # 2. Add UI Elements
        self.__label = tkinter.Label(self, text=prompt_in, padx=10, pady=5)
        self.__label.pack()

        self.__combo = tkinter.ttk.Combobox(
            self, values=[f"{o}" for o in options_in], state="readonly", width=25)
        self.__combo.current(0)  # Default to the first option
        self.__combo.pack(pady=5)

        # Bind the window closing X button to the cancel action
        self.protocol("WM_DELETE_WINDOW", self.__cancel)

        # Button Frame for OK and Cancel side-by-side
        self.__btn_frame = tkinter.Frame(self)
        self.__btn_frame.pack(pady=15)

        self.__ok_btn = tkinter.Button(self.__btn_frame, text="OK", width=10, command=self.__okay)
        self.__ok_btn.pack(side="left", padx=5)

        self.__cancel_btn = tkinter.Button(self.__btn_frame, text="Cancel", width=10, command=self.__cancel)
        self.__cancel_btn.pack(side="left", padx=5)

    def choice(self) -> any:
        # 3. Halt the main code execution until this specific window is closed
        self.wait_window(self)
        return self.__selected

    def __okay(self):
        self.__selected = self.__combo.get()  # Save the selection
        self.destroy()  # Close the popup

    def __cancel(self):
        self.destroy()  # Close without saving (returns None)


def run(progress, max_in):
    for i in range(max_in if max_in is not None else 5):
        time.sleep(1.0)
        if max_in is not None:
            progress.progress(i)
    progress.stop()


def show_progress(root, max_in: int = None):
    progress = ProgressBar("Test", "Running..", max_in)
    progress.start()
    run(progress, max_in)


def show_combo(root):
    combo = OptionsDialog("Options", "Select an Extension", [".cbr", ".cbz", ".cbt", ".cb7"])
    value = combo.choice()
    print(f"{value}")
    show_progress(root, 5)
    root.after(500, show_progress, root)


if __name__ == '__main__':
    root = tkinter.Tk()
    root.after(50, show_combo, root)
    root.mainloop()
