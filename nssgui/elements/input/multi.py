import os

import PySimpleGUI as sg
from nssgui.data import units as unit
from nssgui.style import colors
from nssgui.ge import *
from nssgui import g as nss_g
from nssgui import elements as nss_el

__all__ = ['Filename', 'Path', 'InputUnits']

class Filename(GuiElement):
    def __init__(self, object_id, text) -> None:
        super().__init__(object_id, GuiElement.layout_types.ROW)
        self.text = text
        self.name = ''
        self.extension = ''
    
    ### GuiElement

    # Layout
    
    def _get_row(self):
        row = [
            sg.Text(self.text),
            sg.In(self.name, key=self.keys['Name'], **self.sg_kwargs['Name']),
            sg.In(self.extension, key=self.keys['Extension'], **self.sg_kwargs['Extension'])
        ]
        return row

    # Data

    def _init(self):
        self.init_sg_kwargs('Name')
        self.init_sg_kwargs('Extension', size=(6, 1))
    def _save(self, data):
        data[self.object_id] = [self.name, self.extension]
    def _load(self, data):
        self.name = data[self.object_id][0]
        self.extension = data[self.object_id][1]
    def _pull(self, values):
        self.name = values[self.keys['Name']]
        self.extension = values[self.keys['Extension']]
    def _push(self, window):
        window[self.keys['Name']](self.name)
        window[self.keys['Extension']](self.extension)
    def _init_window(self, window):
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Name')
        self.add_key('Extension')
    
    def define_events(self):
        super().define_events()
    
    # Other
    
    def sg_kwargs_name(self, **kwargs):
        return self.set_sg_kwargs('Name', **kwargs)
    def sg_kwargs_extension(self, **kwargs):
        return self.set_sg_kwargs('Extension', **kwargs)
    
    ### Filename

    def get_filename(self, values):
        return values[self.keys['Name']] + values[self.keys['Name']]
    def update(self, window, name=None, extension=None):
        if name != None:
            self.name = name
        if extension != None:
            self.extension = extension
        self.push(window)

class Path(GuiElement):
    def __init__(self, object_id, text, blank_invalid=False, has_validity=False) -> None:
        super().__init__(object_id, GuiElement.layout_types.ROW)
        self.text = text
        self.path = ''
        self.blank_invalid = blank_invalid
        if blank_invalid:
            self.has_validity = True
        else:
            self.has_validity = has_validity
    
    ### GuiElement

    # Layout
    
    def _get_row(self):
        row = [
            sg.Text(self.text),
            sg.In(self.path, key=self.keys['Path'], enable_events=True, **self.sg_kwargs['Path']),
            sg.FolderBrowse('Browse', key=self.keys['Browse'], target=self.keys['Path'], **self.sg_kwargs['Browse'])
        ]
        return row
    
    # Data

    def _init(self):
        self.init_sg_kwargs('Path')
        self.init_sg_kwargs('Browse')
    def _save(self, data):
        if not self.is_valid():
            data[self.object_id] = None
            return
        data[self.object_id] = self.path
    def _pull(self, values):
        path = values[self.keys['Path']]
        if path:
            path = os.path.normpath(path)
        else:
            path = ''
        self.path = path
    def _load(self, data):
        path = data[self.object_id]
        if path:
            path = os.path.normpath(path)
        else:
            path = ''
        self.path = path
    def _push(self, window):
        self.push_validity(window)
        if not self.is_valid():
            path = ''
        else:
            path = self.path
        window[self.keys['Path']](path)
    def _init_window(self, window):
        self.push(window)
    
    # Keys and Events

    def define_keys(self):
        super().define_keys()
        self.add_key('Path')
        self.add_key('Browse')
    
    def define_events(self):
        super().define_events()
        @self.event(self.keys['Path'])
        def event_path(context):
            self.push_validity('Path')

    # Other
    
    def sg_kwargs_path(self, **kwargs):
        return self.set_sg_kwargs('Path', **kwargs)
    def sg_kwargs_browse(self, **kwargs):
        return self.set_sg_kwargs('Browse', **kwargs)
    
    ### iValid
    
    def _push_validity(self, window):
        sg_path = window[self.keys['Path']]
        if self.is_valid():
            sg_path.update(background_color = colors.valid)
        else:
            sg_path.update(background_color = colors.invalid)
    def _is_valid(self):
        path = self.path
        if path == None:
            return False
        if self.blank_invalid and path == '':
            return False
        return True
    
    ### Path

    def update(self, window, path):
        self.path = path
        self.push(window)

class InputUnits(GuiElement):
    def __init__(self, object_id, text, units, default_degree, store_as_degree=None, negative_invalid=False, has_validity=False, auto_scale_units=None) -> None:
        check_if_subclasses(units, [unit.Unit])
        super().__init__(object_id, GuiElement.layout_types.ROW)
        self.text = text
        self.default_text_in = text
        self.unit_value = None
        self.units = units
        self.default_degree = default_degree
        self.store_as_degree = store_as_degree if store_as_degree else default_degree
        self.negative_invalid = negative_invalid
        if negative_invalid:
            self.has_validity = True
        else:
            self.has_validity = has_validity
        self.auto_scale_units = auto_scale_units if auto_scale_units != None else nss_g.auto_scale_units
        self.set_value(0, default_degree)
    
    ### GuiElement

    # Layout
    
    def _get_row(self):
        self.init()
        self.gem.add_ge(nss_el.Dropdown(self.keys['Unit'], '', self.unit_value.get_symbols(), self.unit_value.get_degree_symbol()))
        row = [
            sg.Text(self.text),
            sg.In(self.unit_value.get_value(), key=self.keys['In'], enable_events=True, **self.sg_kwargs['In']),
            self.ges('Unit').get_sge_dropdown()
        ]
        return row
    
    # Data

    def _init(self):
        self.init_sg_kwargs('In', size=(7, 1))
        self.init_sg_kwargs('Unit')
    def _save(self, data):
        if not self.is_valid():
            data[self.object_id] = None
            return
        value = self.unit_value.get_as_name(self.store_as_degree)
        data[self.object_id] = value
    def _load(self, data):
        value = data[self.object_id]
        if self.set_value(value, self.store_as_degree):
            self.unit_value.convert_to_best_accurate(accuracy=5)
        else:
            self.unit_value.set_degree(self.default_degree)
    def _pull(self, values):
        value = values[self.keys['In']]
        degree_symbol = self.ges('Unit').get_selection(values)
        degree_name = self.unit_value.unit_scale.get_name_by_symbol(degree_symbol)
        self.set_value(value, degree_name)
    def _push(self, window):
        sg_in = window[self.keys['In']]
        sg_dropdown = window[self.ges('Unit').keys['Dropdown']]
        sg_in.update(disabled=self.disabled)
        sg_dropdown.update(disabled=self.disabled)
        if not self.is_valid():
            sg_in.update('')
        else:
            sg_in.update(self.unit_value.get_value())
        self.push_validity(window)
        self.ges('Unit').update(window, self.unit_value.get_degree_symbol())
    def _init_window(self, window):
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('In')
        self.add_key('Unit')
    
    def define_events(self):
        super().define_events()
        @self.event(self.ges('Unit').keys['Dropdown'])
        def event_dropdown(context):
            if not self.auto_scale_units:
                return
            self.pull(context.values)
            degree_symbol = context.values[self.ges('Unit').keys['Dropdown']]
            degree_name = self.units.unit_scale.get_name_by_symbol(degree_symbol)
            if self.is_valid():
                self.unit_value.convert_to_degree(degree_name)
            else:
                self.reset(degree_name)
            self.push(context.window)
        
        @self.event(self.keys['In'])
        def event_in(context):
            self.pull(context.values)
            self.push_validity(context.window)

    # Other

    def sg_kwargs_in(self, **kwargs):
        self.set_sg_kwargs('In', **kwargs)
    def sg_kwargs_unit(self, **kwargs):
        self.set_sg_kwargs('Unit', **kwargs)
    
    ### iValid
    
    def _push_validity(self, window):
        sg_in = window[self.keys['In']]
        if self.is_valid():
            sg_in.update(background_color = colors.valid)
        else:
            sg_in.update(background_color = colors.invalid)
    def _is_valid(self):
        value = self.unit_value.get_value()
        if value == None:
            return False
        if self.negative_invalid and value < 0:
            return False
        return True

    ### InputUnits

    def set_value(self, value, degree_name, force=False):
        if value == None:
            self.reset(degree_name)
            return False
        try:
            value = float(value)
        except ValueError as e:
            self.reset(degree_name)
            return False
        self.unit_value = self.units(value, degree_name=degree_name)
        if not self.is_valid() and not force:
            self.reset(degree_name)
            return False
        return True
    def reset(self, degree_name=None):
        if not degree_name:
            degree_name=self.default_degree
        if self.negative_invalid:
            value = -1
        else:
            value = 0
        self.set_value(value, degree_name, force=True)
    def update(self, window, value, degree_name):
        self.set_value(value, degree_name)
        self.push(window, value)
