from __future__ import annotations

from collections import namedtuple
import textwrap
from typing import Iterable

import PySimpleGUI as sg

from nssgui.popup import *


__all__ = [
    'wjoin',
    'InfoBuilder'
]


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
