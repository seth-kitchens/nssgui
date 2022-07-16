import PySimpleGUI as sg

from nssgui.gui_element import GuiElement

class StatusBar(GuiElement.iRow, GuiElement):

    def __init__(self, object_id, text='', text_color='white', remove_padding=True) -> None:
        super().__init__(object_id)
        self.text = text
        self.text_color = text_color
        self.remove_padding = remove_padding
    
    ### GuiElement

    # Layout
    
    def _get_row(self): 
        row = []
        status_kwargs = {}
        if self.remove_padding:
            status_kwargs['pad'] = 0
        row.append(sg.Text(self.text,
            key=self.keys['Status'], text_color=self.text_color,
            relief=sg.RELIEF_SUNKEN, expand_x=True, **status_kwargs))
        return row
    
    # Data

    def _save(self, data):
        data[self.object_id] = self.text

    def _load(self, data):
        self.text = data[self.object_id]

    def _push(self, window):
        window[self.keys['Status']](self.text, text_color=self.text_color)

    def _init_window_finalized(self, window):
        self.push(window)

    # Keys and Events

    def define_keys(self):
        super().define_keys()
        self.add_key('Status')
    
    def define_events(self):
        super().define_events()
    
    # Other
    
    ### OutText

    def update_status(self, window, text:str, text_color=None):
        self.text = text
        if text_color != None:
            self.text_color = text_color
        self.push(window)
