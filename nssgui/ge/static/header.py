import PySimpleGUI as sg

from nssgui.ge.gui_element import *

class Header(GuiElement):
    def __init__(self, object_id, text) -> None:
        super().__init__(object_id, GuiElement.layout_types.SGE)
        self.text = text

    ### GuiElement

    # Layout
    
    def _get_sge(self):
        return sg.Text(self.text, key=self.keys['Text'], **self.sg_kwargs['Text'])
    
    # Data

    def _init(self):
        self.init_sg_kwargs('Text', text_color='gold')
    def _save(self, data):
        pass
    def _load(self, data):
        pass
    def _pull(self, values):
        pass
    def _push(self, window):
        pass
    def _init_window(self, window):
        pass

    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Text')
    
    def define_events(self):
        super().define_events()

    # Other

    def sg_kwargs_text(self, **kwargs):
        return self.set_sg_kwargs('Text', **kwargs)
