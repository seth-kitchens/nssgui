from __future__ import annotations

import textwrap
from collections import namedtuple
from typing import Iterable

import PySimpleGUI as sg
from psgu import sg as psgu_sg
from psgu.gui_element import *
from psgu.popup import *
from psgu.event_handling import EventContext



__all__ = [
    'InfoButton',
    'Info',
    'wjoin',
    'InfoBuilder'
]


class InfoButton(GuiElement.iSge, GuiElement):

    def __init__(self,
            object_id,
            text='Info',
            info_def:InfoBuilder=None,
            title='Info', 
            header=None, 
            subheader=None) -> None:
        super().__init__(object_id)
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
        return sg.Button(self.text, key=self.keys['Info'], **self.sg_kwargs('Info'))

    # Data
    
    # Keys and Events

    def define_keys(self):
        super().define_keys()
        self.add_key('Info')
    
    def define_events(self):
        super().define_events()
        @self.eventmethod(self.keys['Info'])
        def event_info(event_context:EventContext):
            self.info_popup(event_context.window_context)

    # Other

    def sg_kwargs_info(self, **kwargs):
        self._set_sg_kwargs('Info', **kwargs)

    ### InfoButton

    def info_popup(self, window_context):
        pb = self.info_def.prepare_popup_builder()
        pb.title(self.title).header(self.header).subheader(self.subheader).ok().open(window_context)


button_size = psgu_sg.button_size


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


def wjoin(ss:str|Iterable):
    """
    join list of strs with sep=space if no whitespace already at end of line\n
    ['a', 'b', 'c'] -> 'a b c'       \n
    ['a\\n', 'b ', 'c'] -> 'a\\nb c'   \n
    ['a' 'b', 'c' 'd'] -> 'ab cd'
    """
    if not ss:
        return ''
    if isinstance(ss, str):
        return ss
    len_ss = len(ss)
    for i in range(len_ss - 1):
        if not ss[i]:
            ss[i] = '\n'
        elif not ss[i][-1].isspace():
            ss[i] = ss[i] + ' '
    return ''.join(ss)


InfoBuilderItem = namedtuple('InfoBuilderItem', ['format', 'label', 'text'])


class InfoBuilder:

    _TEXT = 'text'
    _HEADER = 'header'
    _FRAME = 'frame'

    def __init__(self, max_text_width=70):
        """
        Build a definition for an info window.
        Text passed as an iterable will have strings joined with whitespace,
        unless prev line ended with whitespace. See wjoin() for example.\n
        
        dict_def: a dict defining the InfoBuilder,
        shoudld be strs or (nested) dicts of strs
        """
        self.format = format
        self.items:list[InfoBuilderItem] = []
        self.texts = []
        self.max_text_width = max_text_width
    
    def get_all_text(self):
        return ''.join(self.texts)
    
    def add(self, item:InfoBuilderItem):
        self.items.append(item)
        self.texts.append(item.text)
    
    def text(self, text:str|Iterable):
        s = wjoin(text)
        self.add(InfoBuilderItem(InfoBuilder._TEXT, None, s))
        return self
    
    def header(self, header:str, subheader:str|Iterable|None=None):
        s = wjoin(subheader)
        self.add(InfoBuilderItem(InfoBuilder._HEADER, header, s))
        return self
    
    def frame(self, label, text=str|Iterable):
        s = wjoin(text)
        self.add(InfoBuilderItem(InfoBuilder._FRAME, label, s))
        return self
    
    def prepare_popup_builder(self, pb=None):
        pb = pb if pb != None else PopupBuilder()

        def tw(text):
            strings = text.split('\n')
            wrapped_strings = []
            for string in strings:
                wrapped_strings.append(textwrap.fill(string, self.max_text_width))
            return '\n'.join(wrapped_strings)

        for item in self.items: # type: InfoBuilderItem
            if item.format == InfoBuilder._TEXT:
                pb.textwrap(item.text, width=self.max_text_width)
            elif item.format == InfoBuilder._HEADER:
                pb.text(item.label, text_color='gold')
                if item.text:
                    pb.textwrap(item.text)
            elif item.format == InfoBuilder._FRAME:
                s = tw(item.text)
                pb.sge(sg.Frame, title=item.label, layout=[[sg.Text(s)]], expand_x=True, expand_y=True).newline()
        return pb
