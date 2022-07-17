import PySimpleGUI as sg

from PsgUnsimplified.gui_element import *


class Header(GuiElement.iSge, GuiElement):

    def __init__(self, object_id, text) -> None:
        super().__init__(object_id)
        self.text = text

    ### GuiElement

    # Layout
    
    def _get_sge(self):
        self.default_sg_kwargs('Text', text_color='gold')
        return sg.Text(self.text, key=self.keys['Text'], **self._sg_kwargs('Text'))
    
    # Data

    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Text')
    
    def define_events(self):
        super().define_events()

    # Other

    def sg_kwargs_text(self, **kwargs):
        return self._set_sg_kwargs('Text', **kwargs)
