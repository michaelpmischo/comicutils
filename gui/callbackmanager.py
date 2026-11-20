#!/usr/bin/env python3
import tkinter


class CallbackManager:
    def __init__(self, events_in: list[str]):
        self.__callbacks = {e: {"callbacks": [], "widget": None} for e in events_in}

    def subscribe(self, event_in: str, callback: callable, **args_in):
        if event_in in self.__callbacks.keys():
            self.__callbacks[event_in]["callbacks"].append(
                (callback, args_in))
            self._set_states()
        else:
            raise ValueError(
                f"Invalid Callback Subscribe Event: {event_in}\n"
                f"\tValues: {list(self.__callbacks.keys())}")

    def unsubscribe(self, event_in: str, callback: callable, **args_in):
        if event_in in self.__callbacks.keys():
            if (callback, args_in) in self.__callbacks[event_in]["callbacks"]:
                self.__callbacks[event_in]["callbacks"].remove(
                    (callback, args_in))
                self._set_states()
        else:
            raise ValueError(
                f"Invalid Callback Unsubscribe Event: {event_in}\n"
                f"\tValues: {self.events}")

    def _callback(self, call_in: str, event_in: tkinter.Event = None):
        if call_in in self.__callbacks.keys():
            if event_in is None:
                [call(**args) for call, args in self.__callbacks[call_in]["callbacks"]]
            else:
                [call(event_in, **args) for call, args in self.__callbacks[call_in]["callbacks"]]
        else:
            raise ValueError(
                f"Invalid Callback Event: {event_in}\n"
                f"\tValues: {self.events}")

    @property
    def events(self) -> list:
        return list(self.__callbacks.keys())

    def _get_widget(self, event_in: str) -> tkinter.Widget:
        try:
            return self.__callbacks[event_in]["widget"]
        except KeyError as _:
            return None

    def _set_widget(self, event_in: str, widget_in: tkinter.Widget):
        if isinstance(widget_in, tkinter.Widget):
            try:
                self.__callbacks[event_in]["widget"] = widget_in
                return self._set_states()
            except KeyError as _:
                pass
        raise ValueError(
            f"Invalid Event or Widget: {event_in}, {type(
                widget_in).__name__}")

    def _set_states(self):
        for event, item in self.__callbacks.items():
            if item["widget"]:
                try:
                    if any(item["callbacks"]):
                        item["widget"].configure(state=tkinter.NORMAL)
                    else:
                        item["widget"].configure(state=tkinter.DISABLED)
                except tkinter.TclError as _:
                    pass
