import os

import PySimpleGUI as sg

from psgu.style import colors
from psgu.gui_element import *
from psgu.event_context import EventContext


class Path(GuiElement.iRow, GuiElement):

    def __init__(self, object_id, text, blank_invalid=False, has_validity=False) -> None:
        super().__init__(object_id)
        self.text = text
        self.path = ''
        self.blank_invalid = blank_invalid
        if blank_invalid:
            self.has_validity = True
        else:
            self.has_validity = has_validity
    
    ### GuiElement

    # Layout
    
    def _get_row(self):
        row = [
            sg.Text(self.text),
            sg.In(self.path, key=self.keys['Path'], enable_events=True, **self.sg_kwargs('Path')),
            sg.FolderBrowse('Browse',
                key=self.keys['Browse'], target=self.keys['Path'], **self.sg_kwargs('Browse'))
        ]
        return row
    
    # Data

    def _save(self, data):
        if not self.is_valid():
            data[self.object_id] = None
            return
        data[self.object_id] = self.path

    def _pull(self, values):
        path = values[self.keys['Path']]
        if path:
            path = os.path.normpath(path)
        else:
            path = ''
        self.path = path

    def _load(self, data):
        path = data[self.object_id]
        if path:
            path = os.path.normpath(path)
        else:
            path = ''
        self.path = path

    def _push(self, window:sg.Window):
        self.push_validity(window)
        if not self.is_valid():
            path = ''
        else:
            path = self.path
        window[self.keys['Path']](path)

    def _init_window_finalized(self, window:sg.Window):
        self.push(window)
    
    # Keys and Events

    def define_keys(self):
        super().define_keys()
        self.add_key('Path')
        self.add_key('Browse')
    
    def define_events(self):
        super().define_events()
        @self.eventmethod(self.keys['Path'])
        def event_path(event_context:EventContext):
            self.push_validity('Path')

    # Other
    
    def sg_kwargs_path(self, **kwargs):
        return self._set_sg_kwargs('Path', **kwargs)

    def sg_kwargs_browse(self, **kwargs):
        return self._set_sg_kwargs('Browse', **kwargs)
    
    ### iValid
    
    def push_validity(self, window:sg.Window):
        if not self.has_validity:
            return
        sg_path = window[self.keys['Path']]
        if self.is_valid():
            sg_path.update(background_color = colors.valid)
        else:
            sg_path.update(background_color = colors.invalid)

    def is_valid(self):
        if not self.has_validity:
            return True
        path = self.path
        if path == None:
            return False
        if self.blank_invalid and path == '':
            return False
        return True
    
    ### Path

    def update(self, window, path):
        self.path = path
        self.push(window)
