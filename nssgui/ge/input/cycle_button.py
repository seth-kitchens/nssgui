from typing import Iterable
import PySimpleGUI as sg

from nssgui.ge.gui_element import *

__all__ = ['CycleButton']

class CycleButton(GuiElement):
    class display_modes:
        BEFORE_BUTTON_TEXT = 'before_button_text'
        AFTER_BUTTON_TEXT = 'after_button_text'
        BEFORE_LABEL = 'before_label'
        AFTER_LABEL = 'after_label'

    def __init__(self, object_id, options:list[str]|list[str,str]|dict[str,str], label=None, indicator=False, button_text=None, option_display_mode='after_button_text') -> None:
        super().__init__(object_id, GuiElement.layout_types.ROW)
        self.label = label if label != None else ''
        self.button_text = button_text if button_text != None else ''
        self.option_display_mode = option_display_mode
        self.indicator = indicator
        self.indicator_border_l = ''
        self.indicator_border_r = ''
        self.indicator_char_off = '☐'
        self.indicator_char_on = '☒'

        self.values = []
        self.v_to_t = {} # value -> text

        self.current_index = 0

        if isinstance(options[0], str):
            for option in options:
                self.values.append(option)
                self.v_to_t[option] = option
        else:
            for value, text in options:
                self.values.append(value)
                self.v_to_t[value] = text
    
    ### GuiElement

    # Layout
    
    def _get_row(self):
        row = []
        pre_text = self.get_pre_text()
        if pre_text:
            row.append(sg.Text(pre_text, key=self.keys['Label']))
        row.append(self.get_sge_button())
        return row

    def get_sge_button(self):
        text = self.get_button_text()
        sge = sg.Button(text, key=self.keys['Button'], **self.sg_kwargs['Button'])
        return sge

    # Data

    def _init(self):
        self.init_sg_kwargs('Button')
    def _save(self, data):
        pass
    def _load(self, data):
        value = data[self.object_id]
        self.set_current_value(value)
    def _pull(self, values):
        pass
    def _push(self, window):
        sge_button = window[self.keys['Button']]
        sge_button.update(self.get_button_text())
        pre_text = self.get_pre_text()
        if pre_text:
            sge_label = window[self.keys['Label']]
            sge_label.update(pre_text)
    def _init_window(self, window):
        pass
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Label')
        self.add_key('Button')
    
    def define_events(self):
        super().define_events()
        @self.eventmethod(self.keys['Button'])
        def event_button(context):
            self.cycle()
            self.push(context.window)

    # Other
    
    def sg_kwargs_button(self, **kwargs):
        self.set_sg_kwargs('Button', **kwargs)
        return self
    
    ### CycleButton

    # Other

    def get_indicator(self):
        i = self.current_index
        l = self.current_index
        r = len(self.values) - l - 1
        s = self.indicator_border_l
        s += self.indicator_char_off * l
        s += self.indicator_char_on
        s += self.indicator_char_off * r
        s += self.indicator_border_r
        return s

    def set_current_value(self, value):
        index = self.values.index(value)
        self.current_index = index
    def get_current_value(self):
        return self.values[self.current_index]
    def get_current_text(self):
        return self.v_to_t[self.get_current_value()]
    def get_pre_text(self):
        s = ''
        if self.indicator:
            s += self.get_indicator()
        if self.option_display_mode == CycleButton.display_modes.BEFORE_LABEL:
            if s:
                s += ' '
            s += self.get_current_text()
        if self.label:
            if s:
                s += ' '
            s += self.label
        if self.option_display_mode == CycleButton.display_modes.AFTER_LABEL:
            if s:
                s += ' '
            s += self.get_current_text()
        return s
    def get_button_text(self):
        s = ''
        if self.option_display_mode == CycleButton.display_modes.BEFORE_BUTTON_TEXT:
            s += self.get_current_text()
        s += self.button_text
        if self.option_display_mode == CycleButton.display_modes.AFTER_BUTTON_TEXT:
            s += self.get_current_text()
        return s
    def get_imminent_value(self):
        i_imminent = (self.current_index + 1) % len(self.values)
        return self.values[i_imminent]

    def cycle(self):
        self.current_index = (self.current_index + 1) % len(self.values)