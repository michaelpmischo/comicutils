#!/usr/bin/env python3
import tkinter, uuid


class BindEventManager:

    def __init__(self):
        self.__binds = {}

    def bind(self, tag_in: str, sequence_in: str, widget_in: tkinter.Widget,
             callback_in: callable = None, add = False):
        bind = self.__binds
        for k in [tag_in, sequence_in]:
            if k not in bind.keys():
                bind[k] = {} if k != sequence_in else {"func": None, "calls": {}}
            bind = bind[k]
        if bind['func'] is None:
            self.__binds[tag_in][sequence_in]["func"] = (widget_in.tag_bind(
                tag_in, sequence_in, lambda e, s=sequence_in: self.__event(s, e)) if (
                    isinstance(widget_in, tkinter.Canvas)) else
                widget_in.bind(sequence_in, lambda e, s=sequence_in: self.__event(s, e)))
        uid = uuid.uuid4()
        if add:
            self.__binds[tag_in][sequence_in]["calls"][uid] = callback_in
        else:
            self.__binds[tag_in][sequence_in]["calls"] = {uid: callback_in}
        return uid

    def unbind(self, tag_in: str, sequence_in: str,
               widget_in: tkinter.Widget, func_id_in = None):
        try:
            bind = self.__binds[tag_in][sequence_in]
            bind["calls"].pop(func_id_in)
            if not len(bind["calls"]):
                bind = self.__binds[tag_in].pop(sequence_in)
                if isinstance(widget_in, tkinter.Canvas):
                    widget_in.tag_unbind(tag_in, sequence_in, funcid=bind["func"])
                else:
                    widget_in.unbind(sequence_in, funcid=bind["func"])
        except (KeyError, ValueError, tkinter.TclError) as _:
            return

    def __event(self, sequence_in: str, event_in: tkinter.Event):
        # Find ALL items under the mouse pointer (ordered bottom-to-top)
        x, y = ((event_in.widget.canvasx(event_in.x),
                 event_in.widget.canvasy(event_in.y)) if isinstance(
            event_in.widget, tkinter.Canvas) else
                (event_in.x, event_in.y))
        if isinstance(event_in.widget, tkinter.Canvas):
            tags = [t for i in event_in.widget.find_overlapping(
                x-2, y-2, x+2, y+2) for t in event_in.widget.gettags(i)]
            tags = [t for i in event_in.widget.find_closest(x, y)
                    for t in event_in.widget.gettags(i)] if not len(tags) else tags
            for tag in [t for t in tags if t in self.__binds.keys()]:
                if tag in self.__binds.keys() and sequence_in in self.__binds[tag].keys():
                    calls = [c for c in self.__binds[tag][sequence_in]["calls"].values() if c is not None]
                    if any(calls):
                        [_C(event_in) for _C in calls]
                        return
        else:
            pass

