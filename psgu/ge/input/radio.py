import PySimpleGUI as sg

from psgu.gui_element import *


__all__ = ['Radio']


class Radio(GuiElement.iRow, GuiElement):

    def __init__(self, object_id, text, options:list[str]|dict[str,str]):
        """
        If options is a dict, then format is value->text,
        e.g. {'item1': 'Item 1', 'item2': 'Item 2'}
        """
        self.num_options = len(options)
        self.button_keys = [] # index -> key
        super().__init__(object_id)
        self.groupid = GuiElement.make_key('RadioGroup', object_id)
        self.text = text if text != None else ''
        self.k_to_v = {}  # key   -> value
        self.v_to_k = {}  # value -> key
        self.v_to_t = {}  # value -> text, only if given as dict
        self.prev_selected_key = None
        self.selected_key = None
        if isinstance(options, dict):
            for value, text in options.items():
                self.v_to_t[value] = text
        else:
            for value in options:
                self.v_to_t[value] = value
        i = 0
        for value in self.v_to_t.keys():
            key = self.get_button_key(i)
            self.k_to_v[key] = value
            self.v_to_k[value] = key
            i += 1
    
    def get_button_key_name(self, index):
        return 'RadioButton' + str(index)

    def get_button_key(self, index):
        return self.keys['RadioButton' + str(index)]

    ### GuiElement

    # Layout

    def _get_row(self):
        row = []
        if self.text:
            row.append(sg.Text(self.text))
        if not self.selected_key:
            self.selected_key = self.button_keys[0]
        for key in self.button_keys:
            value = self.k_to_v[key]
            default = (key == self.selected_key)
            text = self.v_to_t[value]
            row.append(sg.Radio(text, self.groupid,
                key=key, default=default, enable_events=True, **self.sg_kwargs('Radio')))
        return row
    
    # Data

    def _save(self, data):
        data[self.object_id] = self.get_selected_value()

    def _load(self, data):
        self.set_selected_value(data[self.object_id])
        self.prev_selected_key = None

    def _pull(self, values):
        for key in self.button_keys:
            if values[key]:
                self.set_selected_key(key)

    def _push(self, window:sg.Window):
        for key in self.button_keys:
            window[key](False)
        window[self.selected_key](True)

    def _init_window_finalized(self, window:sg.Window):
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Radio')
        for i in range(self.num_options):
            self.add_key(self.get_button_key_name(i))
            self.button_keys.append(self.get_button_key(i))
    
    def define_events(self):
        super().define_events()
    
    # Other

    def sg_kwargs_radio(self, **kwargs):
        return self._set_sg_kwargs('Radio', **kwargs)
    
    ### Radio

    def get_button_keys(self):
        return self.button_keys.copy()

    def cancel_selection(self, window):
        window[self.selected_key](value=True)

    def get_groupid(self):
        return self.object_id

    def get_selected_value(self):
        return self.k_to_v[self.selected_key]

    def get_selected_key(self):
        return self.selected_key

    def get_selected_index(self):
        return self.button_keys.index(self.selected_key)

    def set_selected_value(self, value):
        key = self.v_to_k[value]
        self.set_selected_key(key)

    def set_selected_key(self, key):
        if key == self.selected_key:
            return
        self.prev_selected_key = self.selected_key
        self.selected_key = key

    def set_selected_index(self, index):
        self.set_selected_key(self.button_keys[index])

    def is_selected(self, value):
        return (value == self.get_selected_value())

    def update(self, window, value=None, key=None, index=None):
        if value:
            self.set_selected_value(value)
        elif key:
            self.set_selected_key(key)
        elif index:
            self.set_selected_value(index)
        else:
            return
        self.push(window)

    def reset(self):
        self.set_selected_index(0)

    def disable_button(self, window, value):
        key = self.v_to_k[value]
        window[key].update(disabled=True)

    def enable_button(self, window, value):
        key = self.v_to_k[value]
        window[key].update(disabled=False)

