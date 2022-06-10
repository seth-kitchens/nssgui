import PySimpleGUI as sg
import tkinter as tk
import copy

# Wrapped 

__all__ = [
    'FrameColumn',
    'Listbox'
]


def FrameColumn(title, layout, frame_kwargs=None, column_kwargs=None, **kwargs):
    """A frame with its layout wrapped in a column, which provides inner padding.\n
    kwargs are passed to both, <cls>_kwargs
    are passed to their respective classes"""
    if layout == None:
        raise ValueError("Layout must be given")
    if frame_kwargs == None:
        frame_kwargs = {}
    if column_kwargs == None:
        column_kwargs = {}
    column_kwargs['layout'] = layout
    frame_kwargs['title'] = title
    column = sg.Column(**kwargs, **column_kwargs)
    frame_kwargs['layout'] = [[column]]
    return sg.Frame(**kwargs, **frame_kwargs)


class Listbox(sg.Listbox):
    def __init__(self, *args, right_click_selects=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.right_click_selects = right_click_selects
        self.right_click_in_progress = False
    def _RightClickMenuCallback(self, event):
        """Note: No way to utilize this alongside set_right_click_menu(None) in a select event,
        since this won't be called for right clicks afterwards and the select won't happen. An empty
        listbox or rows with no intended right-click menu must be given something for now."""
        self.right_click_in_progress = True
        if self.right_click_selects:
            item_to_select = self.Widget.nearest(event.y)
            self.Widget.selection_clear(0, len(self.Values))
            self.Widget.selection_set(item_to_select)
            self._ListboxSelectHandler(event)
        def func():
            sg.Listbox._RightClickMenuCallback(self, event)
            self.right_click_in_progress = False
        self.Widget.after(10, func) # calls after select event returns from sg.Window.read()
    def is_right_click(self):
        """Returns True if a right-click is in progress. Use this
        to exclude right-clicks from double-clicks."""
        return self.right_click_in_progress
    # No way to do this as far as I saw
    # def _WidgetCreatedCallback(self)
    #     super()._WidgetCreatedCallback(self)
    #     self.Widget.configure(activestyle=self.activestyle)