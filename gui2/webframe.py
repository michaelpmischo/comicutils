#!/usr/bin/env python3
import http, sys, io, pathlib, copy, urllib, typing, html
import PIL.Image, PIL.ImageTk, PIL.ImageOps, tkinter, tkinter.ttk, tkinter.filedialog
# For testing..
if __name__ == '__main__':
    sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent.parent}")
    from comicutils.comics2 import book
    from comicutils.gui2 import readframe, menubar, popup, navigationframe
    from comicutils.utils import packages
else:
    from ..comics2 import book
    from . import readframe, menubar, popup, navigationframe
    from ..utils import packages
packages.require({
    "tkinterweb": ("tkinterweb", "tkinterweb[html,images,svg]"),
    "tkextrafont": ("tkextrafont", "tkextrafont")},
    __name__)


# =============================================================================
# WebReadFrame
# =============================================================================
class WebReadFrame(readframe.ReadFrame): #, tkinterweb.HtmlFrame):
    __SCALE = 1.5

    __FORMAT_PRE = '''<style>
    h1, h2, h3, h4 {{ text-align: center !important; }}
    p {{ text-align: left !important; }}
    img {{ display: block !important; margin: 0 auto !important; max-width: 100%; }}
</style>
<div style="padding: 40px 60px; max-width: 800px; margin: 0 auto;">
'''
    __FORMAT_POST = '''</div>'''

    def __init__(self, master_in: tkinter.Misc,
                 comic_in: typing.Union[str, pathlib, book.Book], **args_in):
        super().__init__(master_in, comic_in, orient=readframe.VERTICAL_SCROLL, bg=self._BACKGROUND, **args_in)
        pathlib.Path("message.log").resolve().write_text("")
        self.__locations , self.__images= {}, []
        row, col = 0, 0
        self.rowconfigure(row, weight=1)
        self.columnconfigure(col, weight=1)
        self.__navigation = navigationframe.NavigationFrame(self, (), **args_in)
        self.__navigation.subscribe("selected", self.__navigate)

        # self.__navigation = tkinter.ttk.Treeview(
        #     self, show="headings", columns=())
        # self.__navigation.bind("<<TreeviewSelect>>", self.__navigate)
        self.__navigation.grid(column=col, row=row, padx=0, pady=0, sticky=tkinter.NSEW)

        col += 1
        self.columnconfigure(col, weight=5)
        self.__frame = tkinterweb.HtmlFrame(
            self,
            fontscale=self.__SCALE,
            messages_enabled=True,
            selection_enabled=True,
            image_alternate_text_enabled=False,
            ignore_invalid_images=False,
            javascript_enabled=True,
            javascript_backend="python",
            on_navigate_fail=self.__nav_fail,
            on_link_click=self.__link,
            on_form_submit=self.__form,
            on_script=self.__script,
            on_element_script=self.__element_script,
            on_resource_setup=self.__resource,
            message_func=self.__message,
            request_func=self.__request,
            parsemode="xml")
        self.__frame.grid(column=col, row=row, padx=0, pady=0, sticky=tkinter.NSEW)
        self.__text = tkinter.Text(
            self, font=("Consolas", 11), padx=10, pady=10)

        self.unbind("<MouseWheel>")
        self.unbind("<Button-4>")
        self.unbind("<Button-5>")
        self.__frame.bind_all("<MouseWheel>", self._scroll, add="+")
        self.__frame.bind_all("<Button-4>", self._scroll, add="+")
        self.__frame.bind_all("<Button-5>", self._scroll, add="+")

        # Get the scrollbars since they are hard to access from the HTMLFrame API
        self.yscrollbar, self.xscrollbar = (
            s for (n, s) in self.__frame.children.items() if "scrollbar" in n)

    @typing.override
    @readframe.ReadFrame.comic.setter
    def comic(self, comic_in: book.Book):
        readframe.ReadFrame.comic.fset(self, comic_in)
        self.load()

    def zoom(self, x_in: int, y_in: int, zoom_in: bool):
        """ Set the scale factor based on if we we are zooming in or out """
        super().zoom(x_in, y_in, zoom_in)
        self.__frame.configure(zoom=self.scale)

    @typing.override
    def _draw(self, page_in: list[int] = None,
              reverse_in: bool = False,
              progress_in: popup.ProgressBar = None):
        page_in = self.pages[0] if page_in is None else page_in[0] if (
                isinstance(page_in, (list, tuple))) else page_in
        if isinstance(page_in, int):
            self.pages = page_in
            page_in = self.comic[page_in]
        try:
            if isinstance(page_in, pathlib.Path):
                self.__frame.load_file(f"{page}", decode="utf-8", force=True)
            elif isinstance(page_in, str):
                if self.__is_url(page_in):
                    self.__frame.load_url(page_in)
                else:
                    formatted = f'{self.__FORMAT_PRE}\n{page_in}\n{self.__FORMAT_POST}'
                    self.__source_text = formatted
                    self.__frame.load_html(formatted)

        except Exception as error:
            self.__error(error)

        finally:
            # Allow waiting threads to continue.
            #self.__resolve_xlink_images()
            self._page_drawing = False
            self._draw_id = None

    @typing.override
    def load(self):
        super().load()
        self.__navigation.load(self.comic)

    def __navigate(self, event_in: tkinter.Event) -> None:
        try:
            self.__link(self.__navigation.selected_info.filename)
        except AttributeError as _:
            pass

    @staticmethod
    def __is_url(path_in: str) -> bool:
        try:
            result = urllib.parse.urlparse(path_in)
            return all([result.scheme, result.netloc])
        except (ValueError, AttributeError):
            return False

    def __load_css(self) -> None:
        """
        Send all CSS stylesheets to the html parser. This can be used to alter
        the appearance of already-loaded documents.
        :return: None
        """
        for item in [i for i in self.comic.archive().infolist() if (
                i.type == epub.ITEM_STYLE)]:
            self.__frame.add_css(item.text, priority="author")

    def __script(self, node_in: any, attribute_in: any, components_in: any):
        """
        The function to be called when a <script> element is encountered. 
        This can be used to connect a script handler, such as a JavaScript 
        engine. The script element’s attributes and contents will be passed 
        as arguments.
        """
        pass

    def __element_script(self, node_in: any, attribute_in: any, components_in: any):
        """
        The function to be called when a JavaScript event attribute on an 
        element is encountered. This can be used to connect a script handler, 
        such as a JavaScript engine, or even to run your own Python code. 
        The element’s corresponding Tkhtml3 node, relevant attribute, and 
        attribute contents will be passed as arguments. New in version 4.1.
        """
        pass
        
    def __message(self, message_in: str):
        """
        The function to be called when a debug message is issued. Prior to
        version 4.25 this only works if messages are enabled. The message will
        be passed as an argument. If unset and enabled, by default the message
        is printed.
        """
        with pathlib.Path("message.log").resolve().open("a") as f:
            try:
                f.write(f"{message_in}\n")
            finally:
                f.close()
        
    def __resource(self, url_in: str, type_in: str, success_in: bool):
        """
        The function to be called when an image, stylesheet, or script load 
        finishes. The resource’s url, type (“image”, “stylesheet”, or “script”),
        and whether setup was successful or not (True or False) will be passed
        as arguments.
        """
        if not success_in:
            item = self.comic.archive().getinfo(url_in)
            if type_in == "image":
                pass
            elif type_in == "stylesheet":
                pass
            else:
                pass

    def __link(self, url_in: str):
        """
        The function to be called when a hyperlink is clicked. The target url 
        will be passed as an argument. By default the url is navigated to.
        """
        if self.__is_url(url_in):
            self.__frame.load_url(url_in)
        elif self.comic.archive().getinfo(url_in) is not None:
            self.__frame.load_html(
                self.comic.archive().getinfo(url_in).text)
        else:
            self.__frame.load_html(
                self.comic.archive().get_item_with_href(
                    utl_in))

    def __form(self, url_in: str, data_in: any = "",
               method_in: str = "GET", encoding_in: str = None):
        """
        The function to be called when a form is submitted. The target url, 
        data, and method (“GET” or “POST”) will be passed as arguments. By 
        default the response is loaded.
        :return: 
        """
        pass

    def __nav_fail(self, url_in: str, error_in: Exception, code_in: int):
        """
        The function to be called when a url cannot be loaded. The target url,
        error, and code will be passed as arguments. By default the TkinterWeb
        error page is shown.
        """
        self.__link(url_in)

    def __request(self, url_in: str, data_in: any = "",
                  method_in: str = "GET", encoding_in: str = None) -> tuple[str, bytes, str, int]:
        """
        The function to be called when a resource is requested. This overrides
        all other download settings. The callback must accept the following
        arguments: the resource’s url, data, method (“GET” or “POST”), and
        encoding. The callback must return the following: url, data, file type,
        and HTTP code.
        """
        item = self.comic.archive().getinfo(url_in)
        if item is not None:
            if item.type in [epub.ITEM_IMAGE, epub.ITEM_COVER]:
                data = io.BytesIO()
                if item.object.size[0] > self.__frame.winfo_width():
                    PIL.ImageOps.contain(
                        item.object,
                        (self.__frame.winfo_width(), self.__frame.winfo_height())
                    ).save(data, format="PNG")
                else:
                    item.object.save(data, format="PNG")
                data = data.getvalue()
            else:
                data = item.data
            return (
                url_in, copy.deepcopy(data),
                ("image" if item.type in [epub.ITEM_IMAGE, epub.ITEM_COVER] else (
                    "stylesheet" if item.type in [epub.ITEM_STYLE] else (
                        "script" if item.type in [epub.ITEM_SCRIPT] else "unknown"))),
                 http.HTTPStatus.OK)
        return tkinterweb.utilities.download(url_in, data_in, method_in, decode_in)

    @typing.override
    def _beginning(self):
        if not self._page_turning:
            try:
                self._page_turning = True
                self.pages = [0]
                if self.changed:
                    self.__navigation.selected = min(self.pages)
                    self.draw()
            finally:
                self._page_turning = False

    @typing.override
    def _previous(self):
        if self.pages:
            self.pages = [min(self.pages) - 1] if 0 <= min(self.pages) - 1 else [0]
            if self.changed:
                self.__navigation.selected = min(self.pages)
                self.draw()

    @typing.override
    def _next(self):
        if self.pages:
            self.pages = [max(self.pages) + 1] if max(
                self.pages) + 1 < self.comic.number_of_pages else self.pages
            if self.changed:
                self.__navigation.selected = max(self.pages)
                self.draw()

    @typing.override
    def _end(self):
        if not self._page_turning:
            try:
                self._page_turning = True
                self.pages = [self.comic.number_of_pages - 1]
                if self.changed:
                    self.__navigation.selected = max(self.pages)
                    self.draw()
            finally:
                self.__page_turning = False

    @typing.override
    def zoom_in(self, x_in: int = None, y_in: int = None):
        """ Zoom in with button """
        self.zoom(
            (self.winfo_width() // 2) if x_in is None else x_in,
            (self.winfo_height() // 2) if y_in is None else y_in,
            True)

    @typing.override
    def zoom_out(self, x_in: int = None, y_in: int = None):
        """ Zoom out with button """
        self.zoom(
            (self.winfo_width() // 2) if x_in is None else x_in,
            (self.winfo_height() // 2) if y_in is None else y_in,
            False)

    @typing.override
    def _scroll(self, event_in: tkinter.Event):
        top, bottom = self.xscrollbar.get()
        if event_in.num == 4 or event_in.delta > 0:
            if top <= 0.01:
                self.goto(self.PREVIOUS)
                #self.html.yview_moveto(1.0)
                self.__frame.html.yview_moveto(1.0)
        elif event_in.num == 5 or event_in.delta < 0:
            if bottom >= 0.99:
                self.goto(self.NEXT)
                #self.html.yview_moveto(1.0)
                self.__frame.html.yview_moveto(1.0)

    @typing.override
    def _resize(self, event_in: tkinter.Event):
        #print(f"Resize: {self.winfo_width()}x{self.winfo_height()}")
        pass

    @property
    def __source_text(self) -> str:
        return self.__text.get("1.0", tkinter.END)

    @__source_text.setter
    def __source_text(self, text_in: str):
        self.__text.config(state=tkinter.NORMAL)
        self.__text.delete(1.0, tkinter.END)
        self.__text.insert("1.0", text_in)
        self.__text.config(state=tkinter.DISABLED)

    def __source(self):
        if self.context.source:
            self.__frame.grid_forget()
            self.__text.grid(row=0, column=1, sticky=tkinter.NSEW)
        else:
            self.__text.grid_forget()
            self.__frame.grid(row=0, column=1, sticky=tkinter.NSEW)

    def __error(self, error_in: Exception):
        try:
            raise error_in

        except FileNotFoundError:
            #self.load_html(
            self.__fraem.load_html(
                f"<h1>File Error</h1><p>Could not find file at: <b>{page_in}</b>. "
                f"Check server name and share names.</p>")
        except PermissionError:
            #self.load_html(
            self.__frame.load_html(
                f"<h1>Access Denied</h1><p>Your Windows account does not have "
                f"access permissions to: <b>{page_in}</b></p>")
        except Exception as error:
            #self.load_html(
            self.__frame.load_html(
                f"<h1>Error Loading Document</h1><p>{str(error)}</p>")


def load(frame_in: WebReadFrame):
    try:
        file = pathlib.Path(
            tkinter.filedialog.askopenfilename(
                title="Select a File",
                filetypes=[
                    ("Comic", " ".join(book.Bo.EXTENSIONS)),
                    ("All Files", "*.*")])).resolve()
        if file.is_file() and file.suffix in book.Bo.EXTENSIONS:
            frame_in.file = file
            frame_in.draw()

    except (TypeError, ValueError) as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    # Replace with the path to your DRM-free EPUB file
    root = tkinter.Tk()
    root.geometry("900x800")
    file = pathlib.Path(__file__).parent.parent / "test" / "Masou Gakuen HxH vol.01.epub"
    #comic = epub.EPubFile(file, mode='r')
    webframe = WebReadFrame(root, file)

    col, row = 0, 0
    frame1 = tkinter.Frame(root, padx=0, pady=0)
    frame1.rowconfigure(row, weight=1)
    frame1.columnconfigure(col, weight=1)
    col += 1

    prev = tkinter.Button(
        frame1, text="<- Prev", command=lambda: webframe.goto(readframe.ReadFrame.PREVIOUS),
        padx=0,pady=0, font=("Impact", 16, "bold"))
    prev.grid(row=row, column=col, sticky=tkinter.NSEW)
    col += 1

    open = tkinter.Button(
        frame1, text="Open", command=lambda: load(webframe),
        padx=0, pady=0, font=("Impact", 16, "bold"))
    open.grid(row=row, column=col, sticky=tkinter.NSEW)
    col += 1

    next = tkinter.Button(
        frame1, text="Next ->", command=lambda: webframe.goto(readframe.ReadFrame.NEXT),
        padx=0, pady=0, font=("Impact", 16, "bold"))
    next.grid(row=row, column=col, sticky=tkinter.NSEW)
    col += 1

    extr = tkinter.Button(
        frame1, text="Extract", command=book.extract,
        padx=0, pady=0, font=("Impact", 16, "bold"))
    extr.grid(row=row, column=col, sticky=tkinter.NSEW)
    col += 1

    frame1.columnconfigure(col, weight=1)

    frame1.pack(side=tkinter.TOP, fill=tkinter.X, expand=False)
    webframe.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH, expand=True)

    root.after(50, webframe.load)
    root.mainloop()
