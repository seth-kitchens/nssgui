import PySimpleGUI as sg

from psgu import sg as psgu_sg

__all__ = [
    'WindowContext'
]

NULL_EVENT = 'NULL_EVENT'

class WindowContext:

    def __init__(self, window:sg.Window|None=None):
        self.window:sg.Window|None = window
        self.window_stack:list[sg.Window] = []
        self.async_windows:dict = {}
        self.asyncs = self.async_windows

    def push(self, window:sg.Window):
        if self.window is not None:
            self.window_stack.append(self.window)
        self.window = window
        psgu_sg.center_window(window)

    def pop(self):
        w = self.window
        if self.window_stack:
            self.window = self.window_stack.pop()
        else:
            self.window = None
        return w
    
    def add_async(self, asyncwindow):
        self.async_windows[asyncwindow.window_id] = asyncwindow
        if asyncwindow.window != None:
            psgu_sg.center_window(asyncwindow.window)
    
    def remove_async(self, window_id):
        del self.async_windows[window_id]

    def focus(self):
        if self.window == None:
            return
        self.window.bring_to_front()
        self.window.force_focus()
        for w in self.async_windows.values():
            w.window.bring_to_front()
            w.window.force_focus()

    def disable(self):
        if self.window == None:
            return
        self.window.disable()
        self.window.set_alpha(0.9)

    def enable(self):
        if self.window == None:
            return
        self.window.enable()
        self.window.set_alpha(1.0)

    def hide(self):
        if self.window == None:
            return
        self.window.hide()
    
    def unhide(self):
        if self.window == None:
            return
        self.window.un_hide()