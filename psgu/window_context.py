from __future__ import annotations

from abc import ABC, abstractmethod

import PySimpleGUI as sg

from psgu import sg as psgu_sg


class WindowContext:
    """
    window: current blocking sg.Window
    _window_stack: stack of all blocking windows
    """

    class iBlockingWindow(ABC):
        @abstractmethod
        def get_window(self) -> sg.Window:
            pass

    class iAsyncWindow(ABC):
        @abstractmethod
        def get_window_id(self):
            pass
        @abstractmethod
        def get_window(self) -> sg.Window:
            pass

    def __init__(self, window:sg.Window|iBlockingWindow|iAsyncWindow|None=None):
        self.window:sg.Window|None = None
        self._window_stack:list[sg.Window|WindowContext.iBlockingWindow] = []
        self.async_windows:dict[str, WindowContext.iAsyncWindow] = {}
        if isinstance(window, WindowContext.iBlockingWindow) or isinstance(window, sg.Window):
            self.push(window)
        elif isinstance(window, WindowContext.iAsyncWindow):
            self.add_async(window)
        elif window is None:
            pass
        else:
            raise TypeError('Not a valid window class')

    @classmethod
    def from_any(cls, w:WindowContext|sg.Window|None):
        if isinstance(w, WindowContext):
            return w
        return cls(w)

    def push(self, window:iBlockingWindow|sg.Window):
        """
        Push a blocking window onto the window stack
        """
        self._window_stack.append(window)
        if isinstance(window, WindowContext.iBlockingWindow):
            self.window = window.get_window()
        else:
            self.window = window
        psgu_sg.center_window(window)

    def pop(self):
        """
        Pop the top blocking window and return it as `sg.Window`.
        Returns `None` if no blocking window.
        Use `get_blocking()` to get a top `iBlocking` window instead of `sg.Window`
        """
        if self.window is None:
            return None
        popped = self.window
        self._window_stack.pop()
        self.window = self.get_window()
        return popped
    
    def get_window(self):
        if not self._window_stack:
            return None
        w = self._window_stack[-1]
        if isinstance(w, WindowContext.iBlockingWindow):
            return w.get_window()
        return w
    
    def get_blocking(self):
        """Returns top blocking window. Does not pop"""
        return self._window_stack[-1]
    
    def add_async(self, asyncwindow:iAsyncWindow):
        window_id = asyncwindow.get_window_id()
        self.async_windows[window_id] = asyncwindow
        window = asyncwindow.get_window()
        if window != None:
            psgu_sg.center_window(window)
    
    def remove_async(self, window_id):
        del self.async_windows[window_id]

    def focus(self):
        if self.window is None:
            return
        self.window.bring_to_front()
        self.window.force_focus()
        for w in self.async_windows.values():
            window = w.get_window()
            window.bring_to_front()
            window.force_focus()

    def disable(self):
        if self.window is None:
            return
        self.window.disable()
        self.window.set_alpha(0.9)

    def enable(self):
        if self.window is None:
            return
        self.window.enable()
        self.window.set_alpha(1.0)

    def hide(self):
        if self.window is None:
            return
        self.window.hide()
    
    def unhide(self):
        if self.window is None:
            return
        self.window.un_hide()