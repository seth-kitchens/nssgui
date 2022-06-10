import PySimpleGUI as sg

from nssgui.ge import *
from nssgui.popup import PopupBuilder
from nssgui import sg as nss_sg

__all__ = ['Header', 'InfoButton', 'Info']

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

class InfoButton(GuiElement):
    def __init__(self, object_id, text='Info', info_text=None, title='Info', header=None, subheader=None) -> None:
        super().__init__(object_id, GuiElement.layout_types.SGE)
        self.text = text
        self.info_text = info_text
        self.title = title
        self.header = header
        self.subheader = subheader
    
    ### GuiElement

    # Layout

    def _get_sge(self):
        if len(self.text) < 2:
            self.sg_kwargs_info(size=(2, 1))
        return sg.Button(self.text, key=self.keys['Info'], **self.sg_kwargs['Info'])

    # Data

    def _init(self):
        self.init_sg_kwargs('Info')
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
        self.add_keys(['Info'])
    
    def define_events(self):
        super().define_events()
        @self.event(self.keys['Info'])
        def event_info(context):
            self.info_popup(context)

    # Other

    def sg_kwargs_info(self, **kwargs):
        self.set_sg_kwargs('Info', **kwargs)

    ### InfoButton

    def info_popup(self, context):
        PopupBuilder().textwrap(self.info_text).title(self.title).header(self.header).subheader(self.subheader).ok().open(context)


button_size = nss_sg.button_size

def Info(gem, info_text, button_text=None, header=None, subheader=None, bt=None, sg_kwargs=None):
    if button_text == None:
        if bt:
            button_text = bt
        else:
            button_text = '?'
    
    key = gem.gem_key(info_text)
    ge = InfoButton(object_id=key, text=button_text, info_text=info_text, header=header, subheader=subheader)
    if not sg_kwargs:
        sg_kwargs = {}
    if not 'size' in sg_kwargs:
        sg_kwargs['size'] = 6
    ge.sg_kwargs_info(**sg_kwargs)
    return gem.sge(ge)