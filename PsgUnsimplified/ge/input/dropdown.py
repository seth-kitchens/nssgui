import PySimpleGUI as sg

from PsgUnsimplified.gui_element import *


class Dropdown(GuiElement.iRow, GuiElement):
    
    def __init__(self, object_id, text, options, enable_events=True) -> None:
        super().__init__(object_id)
        self.text = text
        self.options = options
        self.enable_events = enable_events
        self.selection = None
    
    ### GuiElement

    # Layout
    
    def _get_row(self):
        row = [sg.Text(self.text)]
        row.append(self.get_sge_dropdown())
        return row
    
    # Data
    
    def _save(self, data):
        data[self.object_id] = self.selection
    
    def _load(self, data):
        self.selection = data[self.object_id]
    
    def _pull(self, values):
        selection = values[self.keys['Dropdown']]
        if selection in self.options:
            self.selection = selection
    
    def _push(self, window):
        window[self.keys['Dropdown']](self.selection)
    
    def _init_window_finalized(self, window):
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Dropdown')
    
    def define_events(self):
        super().define_events()
    
    # Others

    def sg_kwargs_dropdown(self, **kwargs):
        self._set_sg_kwargs('Dropdown', **kwargs)

    def get_sge_dropdown(self):
        if not self.selection:
            self.selection = self.options[0]
        return sg.Combo(self.options, self.selection,
            key=self.keys['Dropdown'], enable_events=self.enable_events,
            **self.sg_kwargs('Dropdown'))
    
    ### Dropdown

    def update(self, window, value):
        self.selection = value
        self.push(window)
    
    def get_selection(self, values=None):
        if values:
            self.pull(values)
        return self.selection
