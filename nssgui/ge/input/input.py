import PySimpleGUI as sg

from nssgui.style import colors
from nssgui.gui_element import *


class Input(GuiElement.iRow, GuiElement):

    TYPE_SMALL = 'small'
    TYPE_INT = 'int'
    TYPE_NUMBER = 'number'

    def __init__(self,
            object_id,
            text,
            type=None,
            negative_invalid=False,
            blank_invalid=False,
            has_validity=False) -> None:
        super().__init__(object_id)
        self.text = text
        self.type = type
        self.negative_invalid = negative_invalid
        if negative_invalid:
            self.blank_invalid = blank_invalid
            self.has_validity = True
        elif blank_invalid:
            self.has_validity = True
        else:
            self.has_validity = has_validity
        self.value = ''
    
    ### GuiElement

    # Layout
    
    def _get_row(self):
        row = []
        if self.text:
            row.append(sg.Text(self.text))
        row.append(sg.In(
            self.value, key=self.keys['In'], enable_events=True, **self.sg_kwargs['In']))
        return row
    
    # Data

    def _init_before_layout(self):
        if self.type == Input.TYPE_SMALL or self.type == Input.TYPE_INT:
            self.init_sg_kwargs('In', size=(5, 1))
        else:
            self.init_sg_kwargs('In')

    def _save(self, data):
        if not self.is_valid():
            data[self.object_id] = None
            return
        data[self.object_id] = self.value

    def _load(self, data):
        self.value = data[self.object_id]
        self.refresh_value()

    def _pull(self, values):
        self.value = values[self.keys['In']]
        self.refresh_value()

    def _push(self, window):
        sg_in = window[self.keys['In']]
        sg_in.update(disabled=self.disabled)
        if not self.is_valid():
            sg_in.update('')
        else:
            sg_in.update(self.value)
        self.push_validity(window)

    def _init_window_finalized(self, window):
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('In')
    
    def define_events(self):
        super().define_events()
        @self.eventmethod(self.keys['In'])
        def event_in(context):
            self.pull(context.values)
            self.push_validity(context.window)
    
    # Other

    def sg_kwargs_in(self, **kwargs):
        return self.set_sg_kwargs('In', **kwargs)
    
    ### iValid
    
    def push_validity(self, window):
        if not self.has_validity:
            return
        sg_in = window[self.keys['In']]
        if self.is_valid():
            sg_in.update(background_color = colors.valid)
        else:
            sg_in.update(background_color = colors.invalid)

    def is_valid(self):
        if not self.has_validity:
            return True
        if self.value == None:
            return False
        self.refresh_value()
        if self.type == self.TYPE_INT:
            if self.negative_invalid and self.value < 0:
                return False
        if self.blank_invalid and self.value == '':
            return False
        return True

    def set_value(self, value, force=False):
        self.value = value
        if (not self.is_valid()) and not force:
            self.reset()

    def reset(self):
        if self.type == self.TYPE_INT:
            if self.negative_invalid:
                value = -1
            else:
                value = 0
        else:
            value = ''
        self.set_value(value, force=True)
    
    ### Input

    def refresh_value(self):
        if self.value == None:
            self.reset()
            return
        if self.type == self.TYPE_INT:
            try:
                self.value = int(self.value)
            except ValueError as e:
                self.reset()
                return

    def update(self, window, value):
        self.value = value
        self.push(window)
