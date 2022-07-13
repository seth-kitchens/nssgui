import PySimpleGUI as sg

from nssgui.gui_element import *


class Filename(GuiElement.iRow, GuiElement):

    def __init__(self, object_id, text) -> None:
        super().__init__(object_id)
        self.text = text
        self.name = ''
        self.extension = ''
    
    ### GuiElement

    # Layout
    
    def _get_row(self):
        row = [
            sg.Text(self.text),
            sg.In(self.name, key=self.keys['Name'], **self.sg_kwargs['Name']),
            sg.In(self.extension, key=self.keys['Extension'], **self.sg_kwargs['Extension'])
        ]
        return row

    # Data

    def _init_before_layout(self):
        self.init_sg_kwargs('Name')
        self.init_sg_kwargs('Extension', size=(6, 1))

    def _save(self, data):
        data[self.object_id] = [self.name, self.extension]

    def _load(self, data):
        self.name = data[self.object_id][0]
        self.extension = data[self.object_id][1]

    def _pull(self, values):
        self.name = values[self.keys['Name']]
        self.extension = values[self.keys['Extension']]

    def _push(self, window):
        window[self.keys['Name']](self.name)
        window[self.keys['Extension']](self.extension)

    def _init_window_finalized(self, window):
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Name')
        self.add_key('Extension')
    
    def define_events(self):
        super().define_events()
    
    # Other
    
    def sg_kwargs_name(self, **kwargs):
        return self.set_sg_kwargs('Name', **kwargs)

    def sg_kwargs_extension(self, **kwargs):
        return self.set_sg_kwargs('Extension', **kwargs)
    
    ### Filename

    def get_filename(self, values):
        return values[self.keys['Name']] + values[self.keys['Name']]

    def update(self, window, name=None, extension=None):
        if name != None:
            self.name = name
        if extension != None:
            self.extension = extension
        self.push(window)
