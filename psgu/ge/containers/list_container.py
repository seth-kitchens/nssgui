from abc import ABC, abstractmethod

import PySimpleGUI as sg
from psgu.event_handling import WRC
from psgu.window import AbstractBlockingWindow
from psgu.gui_element import *


class ListContainer(GuiElementContainer, ABC):
    
    def __init__(self, ge:GuiElement) -> None:
        check_if_instances(ge, [GuiElement, GuiElement.iLength])
        super().__init__(ge)
    
    ### GuiElement

    # Layout
    # Data
    
    def _init_window_finalized(self, window):
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Edit')
    
    class WindowEditContained(AbstractBlockingWindow):
        
        def __init__(self, title, contained) -> None:
            check_if_instances(contained, [GuiElement.iEdittable])
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
            window_edit = ListContainer.WindowEditContained('Edit', self.contained)
            rv = window_edit.open(context)
            if not rv.check_success():
                return
            self.load(window_edit.get_data())
            self.push(context.window)
