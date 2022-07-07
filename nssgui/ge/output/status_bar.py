import PySimpleGUI as sg

from nssgui.ge.gui_element import GuiElement

class StatusBar(GuiElement):
    def __init__(self, object_id, text='') -> None:
        super().__init__(object_id, GuiElement.layout_types.ROW)
        self.text = text
    
    ### GuiElement

    # Layout
    
    def _get_row(self): 
        row = []
        row.append(sg.Text(self.text, key=self.keys['MainBar'], relief=sg.RELIEF_SUNKEN, pad=0, expand_x=True))
        return row
    
    # Data

    def _init(self):
        pass
    def _save(self, data):
        data[self.object_id] = self.text
    def _load(self, data):
        self.text = data[self.object_id]
    def _pull(self, values):
        pass
    def _push(self, window):
        window[self.keys['MainBar']](self.text)
    def _init_window(self, window):
        self.push(window)

    # Keys and Events

    def define_keys(self):
        super().define_keys()
        self.add_keys(['MainBar'])
    
    def define_events(self):
        super().define_events()
    
    # Other
    
    ### OutText

    def update_status(self, window, text:str):
        self.text = text
        self.push(window)

