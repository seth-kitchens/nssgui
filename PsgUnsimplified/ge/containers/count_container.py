import PySimpleGUI as sg

from PsgUnsimplified.gui_element import *
from PsgUnsimplified.ge.containers.list_container import ListContainer


# show the count of the contained list
class CountContainer(ListContainer):
    
    def __init__(self, text, ge:GuiElement) -> None:
        check_if_instances(ge, [GuiElement, GuiElement.iLength])
        super().__init__(ge, GuiElement.layout_types.ROW)
        self.text = text
    
    ### GuiElement

    # Layout

    def _get_row(self):
        row = [
            sg.Text(self.text),
            sg.Text('0', key=self.keys['Count']),
            sg.Button('Edit', key=self.keys['Edit'])
        ]
        return row
    
    # Data

    def _pull(self, values):
        pass
    
    def _push(self, window):
        window[self.keys['Count']](str(len(self.contained)))
    
    # Keys and Events

    def define_keys(self):
        super().define_keys()
        self.add_key('Count')
    
    def define_events(self):
        super().define_events()
