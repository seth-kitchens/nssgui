from abc import ABC, abstractmethod

import PySimpleGUI as sg
from nssgui.event_handling import WRC
from nssgui.window import AbstractBlockingWindow
from nssgui.gui_element import *

class ListContainer(GuiElement, ABC):
    
    def __init__(self, ge:GuiElement, layout_type) -> None:
        check_if_instances(ge, [GuiElement, iLength])
        self.ge = ge
        self.contained_object_id = ge.object_id
        object_id = 'ListContainer(' + self.contained_object_id + ')'
        super().__init__(object_id, layout_type)
        self.gem.add_ge(ge)
    
    ### GuiElement

    # Layout
    # Data
    
    def _init_window(self, window):
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Edit')
    
    class WindowEditContained(AbstractBlockingWindow):
        
        def __init__(self, title, contained) -> None:
            check_if_instances(contained, [iEdittable])
            self.contained:GuiElement = contained
            super().__init__(title)
        
        def get_layout(self):
            layout = [*self.contained.get_edit_layout()]
            layout.extend([
                [sg.HSeparator()],
                [sg.Push(), sg.Ok(size=12), sg.Push()]
            ])
            return layout
        
        def define_events(self):
            super().define_events()
            self.event_handler(self.contained.handle_event)
            self.event_value_close_success('Ok')
            self.event_value_close(sg.WIN_CLOSED)
    
    def define_events(self):
        super().define_events()
        @self.eventmethod(self.keys['Edit'])
        def event_edit(context):
            window_edit = ListContainer.WindowEditContained('Edit', self.ge)
            rv = window_edit.open(context)
            if not rv.check_success():
                return
            self.load(window_edit.get_data())
            self.push(context.window)
