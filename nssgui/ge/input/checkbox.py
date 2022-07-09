import PySimpleGUI as sg

from nssgui.ge.gui_element import *


class Checkbox(GuiElement):
    
    def __init__(self, object_id, text) -> None:
        super().__init__(object_id, GuiElement.layout_types.SGE)
        self.text = text
        self.value = False
    
    ### GuiElement

    # Layout
    
    def _get_sge(self):
        return sg.Checkbox(self.text,
            key=self.keys['Checkbox'], default=self.value, **self.sg_kwargs['Checkbox'])
    
    # Data

    def _init(self):
        self.init_sg_kwargs('Checkbox')
    
    def _save(self, data):
        data[self.object_id] = self.value
    
    def _load(self, data):
        value = data[self.object_id]
        if value == None:
            value = False
        self.value = value
    
    def _pull(self, values):
        self.value = values[self.keys['Checkbox']]
    
    def _push(self, window):
        sge_checkbox = window[self.keys['Checkbox']]
        sge_checkbox.update(self.value)
        sge_checkbox.update(disabled=self.disabled)
    
    def _init_window(self, window):
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Checkbox')
    
    def define_events(self):
        super().define_events()
    
    # Other
    
    def sg_kwargs_checkbox(self, **kwargs):
        return self.set_sg_kwargs('Checkbox', **kwargs)
    
    ### Checkbox

    def update(self, window, value):
        self.value = value
        self.push(window)
