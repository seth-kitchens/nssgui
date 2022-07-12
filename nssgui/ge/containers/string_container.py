import PySimpleGUI as sg

from nssgui.style import colors
from nssgui.gui_element import *
from nssgui.ge.containers.list_container import ListContainer


# Show the contained list as a string
class StringContainer(ListContainer):
    
    def __init__(self, 
            text,
            ge:GuiElement,
            folder_browse=False,
            blank_invalid=False,
            has_validity=False) -> None:
        check_if_instances(ge, [GuiElement, iLength, iEdittable, iStringable])
        super().__init__(ge, GuiElement.layout_types.ROW)
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
        if 'delim' in dir(self.ge):
            char_names = {
                ';': 'semicolon',
                ',': 'comma'
            }
            s_delim = self.ge.delim
            if s_delim in char_names:
                s_delim = char_names[s_delim]
            else:
                s_delim = '"' + s_delim + '"'
            tooltip = 'Items separated by ' + s_delim
        else:
            tooltip = None
        row = [
            sg.Text(self.text),
            sg.In(self.ge.to_string(), key=self.keys['In'], enable_events=True, tooltip=tooltip),
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
        self.ge.load_string(s)
    
    def _push(self, window):
        self.push_validity(window)
        window[self.keys['In']](self.ge.to_string())
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('In')
        self.add_key('Add')
    
    def define_events(self):
        super().define_events()
        @self.eventmethod(self.keys['Add'])
        def event_add(context):
            path = context.values[self.keys['Add']]
            if path:
                self.ge.add_item(path)
            self.push(context.window)
        
        @self.eventmethod(self.keys['In'])
        def event_in(context):
            self.pull(context.values)
            self.push_validity(context.window)

    # Other
    
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
        if self.blank_invalid and not len(self.ge):
            return False
        return True
