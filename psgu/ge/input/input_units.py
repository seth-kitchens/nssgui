import PySimpleGUI as sg

from psgu.data import units as unit
from psgu.style import colors
from psgu.gui_element import *
from psgu import g as psgu_g
from psgu import ge as psgu_el
from psgu.event_context import EventContext


class InputUnits(GuiElement.iRow, GuiElement):

    def __init__(self,
            object_id,
            text,
            units,
            default_degree,
            store_as_degree=None,
            negative_invalid=False,
            has_validity=False,
            auto_scale_units=None) -> None:
        check_if_subclasses(units, [unit.Unit])
        super().__init__(object_id)
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
        self.auto_scale_units = auto_scale_units if auto_scale_units != None else psgu_g.auto_scale_units
        self.set_value(0, default_degree)
    
    ### GuiElement

    # Layout
    
    def _get_row(self):
        self.default_sg_kwargs('In', size=(7, 1))
        self.gem.add_ge(psgu_el.Dropdown(self.keys['Unit'], '', self.unit_value.get_symbols(), self.unit_value.get_degree_symbol()))
        row = [
            sg.Text(self.text),
            sg.In(self.unit_value.get_value(), key=self.keys['In'], enable_events=True, **self.sg_kwargs('In')),
            self.ges('Unit').get_sge_dropdown()
        ]
        return row
    
    # Data

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

    def _push(self, window:sg.Window):
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

    def _init_window_finalized(self, window:sg.Window):
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('In')
        self.add_key('Unit')
    
    def define_events(self):
        super().define_events()

        @self.eventmethod(self.ges('Unit').keys['Dropdown'])
        def event_dropdown(event_context:EventContext):
            if not self.auto_scale_units:
                return
            self.pull(event_context.values)
            degree_symbol = event_context.values[self.ges('Unit').keys['Dropdown']]
            degree_name = self.units.unit_scale.get_name_by_symbol(degree_symbol)
            if self.is_valid():
                self.unit_value.convert_to_degree(degree_name)
            else:
                self.reset(degree_name)
            self.push(event_context.window)
        
        @self.eventmethod(self.keys['In'])
        def event_in(event_context:EventContext):
            self.pull(event_context.values)
            self.push_validity(event_context.window)

    # Other

    def sg_kwargs_in(self, **kwargs):
        self._set_sg_kwargs('In', **kwargs)

    def sg_kwargs_unit(self, **kwargs):
        self._set_sg_kwargs('Unit', **kwargs)
    
    ### iValid
    
    def push_validity(self, window:sg.Window):
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
