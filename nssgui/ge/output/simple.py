import PySimpleGUI as sg

from nssgui.ge.gui_element import GuiElement

__all__ = [
    'OutText',
    'StatusBar'
]

class OutText(GuiElement):
    def __init__(self, object_id, label=None) -> None:
        super().__init__(object_id, GuiElement.layout_types.ROW)
        self.label = label
        self.value = ''
    
    ### GuiElement

    # Layout
    
    def _get_row(self): 
        row = []
        if self.label:
            row.append(sg.Text(self.label))
        row.append(sg.Text(self.value, key=self.keys['Out'], **self.sg_kwargs['Out']))
        return row
    
    # Data

    def _init(self):
        self.init_sg_kwargs('Out')
    def _save(self, data):
        data[self.object_id] = self.value
    def _load(self, data):
        self.value = data[self.object_id]
    def _pull(self, values):
        pass
    def _push(self, window):
        window[self.keys['Out']](self.value)
    def _init_window(self, window):
        self.push(window)

    # Keys and Events

    def define_keys(self):
        super().define_keys()
        self.add_keys(['Out'])
    
    def define_events(self):
        super().define_events()
    
    # Other

    def sg_kwargs_out(self, **kwargs):
        return self.set_sg_kwargs(self, **kwargs)
    
    ### OutText

    def update(self, window, value):
        self.value = value
        self.push(window)

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

    def update(self, window, text):
        self.text = text
        self.push(window)