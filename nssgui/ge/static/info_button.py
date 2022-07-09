import PySimpleGUI as sg

from nssgui.data.info_def import InfoBuilder
from nssgui.ge.gui_element import *
from nssgui import sg as nss_sg


class InfoButton(GuiElement):

    def __init__(self,
            object_id,
            text='Info',
            info_def:InfoBuilder=None,
            title='Info', 
            header=None, 
            subheader=None) -> None:
        super().__init__(object_id, GuiElement.layout_types.SGE)
        self.text = text
        self.info_def = info_def
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
        @self.eventmethod(self.keys['Info'])
        def event_info(context):
            self.info_popup(context)

    # Other

    def sg_kwargs_info(self, **kwargs):
        self.set_sg_kwargs('Info', **kwargs)

    ### InfoButton

    def info_popup(self, context):
        pb = self.info_def.prepare_popup_builder()
        pb.title(self.title).header(self.header).subheader(self.subheader).ok().open(context)


button_size = nss_sg.button_size


def Info(gem, info_def:str|InfoBuilder, button_text=None, header=None, subheader=None, bt=None, sg_kwargs=None):
    if isinstance(info_def, str):
        info_def = InfoBuilder().text(info_def)
    if not isinstance(info_def, InfoBuilder):
        raise TypeError('Expected InfoBuilder, got ' + str(type(info_def)))
    if button_text == None:
        if bt:
            button_text = bt
        else:
            button_text = '?'    
    key = gem.gem_key(info_def.get_all_text())
    ge = InfoButton(object_id=key, text=button_text, info_def=info_def, header=header, subheader=subheader)
    if not sg_kwargs:
        sg_kwargs = {}
    if not 'size' in sg_kwargs:
        sg_kwargs['size'] = 6
    ge.sg_kwargs_info(**sg_kwargs)
    return gem.sge(ge)
