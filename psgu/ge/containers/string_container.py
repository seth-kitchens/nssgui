import PySimpleGUI as sg

from psgu.style import colors
from psgu.gui_element import *
from psgu.ge.containers.list_container import ListContainer
from psgu.event_context import EventContext


# Show the contained list as a string
class StringContainer(GuiElement.iRow, ListContainer):
    
    def __init__(self, 
            text,
            ge:GuiElement,
            folder_browse=False,
            blank_invalid=False,
            has_validity=False) -> None:
        check_if_instances(ge, [GuiElement, GuiElement.iLength, GuiElement.iEdittable, GuiElement.iStringable])
        super().__init__(ge)
        self.text = text
        self.folder_browse = folder_browse
        self.blank_invalid = blank_invalid
        if blank_invalid:
            self.has_validity = True
        else:
            self.has_validity = has_validity
    
    ### GuiElement

    # Layout

    def _get_row(self):
        if 'delim' in dir(self.contained):
            char_names = {
                ';': 'semicolon',
                ',': 'comma'
            }
            s_delim = self.contained.delim
            if s_delim in char_names:
                s_delim = char_names[s_delim]
            else:
                s_delim = '"' + s_delim + '"'
            tooltip = 'Items separated by ' + s_delim
        else:
            tooltip = None
        row = [
            sg.Text(self.text),
            sg.In(self.contained.to_string(), key=self.keys['In'], enable_events=True, tooltip=tooltip),
            sg.Button('Edit', key=self.keys['Edit'])
        ]
        if self.folder_browse:
            row.insert(2, sg.In('', key=self.keys['Add'], visible=False, enable_events=True))
            row.insert(3, sg.FolderBrowse('Add Folder'))
        return row
    
    # Data

    def _pull(self, values):
        s = values[self.keys['In']]
        if s == None:
            return
        self.contained.load_string(s)
    
    def _push(self, window:sg.Window):
        self.push_validity(window)
        window[self.keys['In']](self.contained.to_string())
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('In')
        self.add_key('Add')
    
    def define_events(self):
        super().define_events()
        @self.eventmethod(self.keys['Add'])
        def event_add(event_context:EventContext):
            path = event_context.values[self.keys['Add']]
            if path:
                self.contained.add_item(path)
            self.push(event_context.window)
        
        @self.eventmethod(self.keys['In'])
        def event_in(event_context:EventContext):
            self.pull(event_context.values)
            self.push_validity(event_context.window)

    # Other
    
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
        if self.blank_invalid and not len(self.contained):
            return False
        return True
