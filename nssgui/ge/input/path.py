import os

import PySimpleGUI as sg
from nssgui.style import colors
from nssgui.ge.gui_element import *

class Path(GuiElement):
    def __init__(self, object_id, text, blank_invalid=False, has_validity=False) -> None:
        super().__init__(object_id, GuiElement.layout_types.ROW)
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
            sg.In(self.path, key=self.keys['Path'], enable_events=True, **self.sg_kwargs['Path']),
            sg.FolderBrowse('Browse', key=self.keys['Browse'], target=self.keys['Path'], **self.sg_kwargs['Browse'])
        ]
        return row
    
    # Data

    def _init(self):
        self.init_sg_kwargs('Path')
        self.init_sg_kwargs('Browse')
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
    def _push(self, window):
        self.push_validity(window)
        if not self.is_valid():
            path = ''
        else:
            path = self.path
        window[self.keys['Path']](path)
    def _init_window(self, window):
        self.push(window)
    
    # Keys and Events

    def define_keys(self):
        super().define_keys()
        self.add_key('Path')
        self.add_key('Browse')
    
    def define_events(self):
        super().define_events()
        @self.event(self.keys['Path'])
        def event_path(context):
            self.push_validity('Path')

    # Other
    
    def sg_kwargs_path(self, **kwargs):
        return self.set_sg_kwargs('Path', **kwargs)
    def sg_kwargs_browse(self, **kwargs):
        return self.set_sg_kwargs('Browse', **kwargs)
    
    ### iValid
    
    def _push_validity(self, window):
        sg_path = window[self.keys['Path']]
        if self.is_valid():
            sg_path.update(background_color = colors.valid)
        else:
            sg_path.update(background_color = colors.invalid)
    def _is_valid(self):
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
