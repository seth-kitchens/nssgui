from abc import ABC, abstractmethod

import PySimpleGUI as sg
from nssgui.window import AbstractBlockingWindow
from nssgui.style import colors
from nssgui.ge import *

__all__ = ['ListContainer', 'CountContainer', 'StringContainer']

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

    def _init(self):
        pass
    def _save(self, data):
        pass
    def _load(self, data):
        pass
    @abstractmethod
    def _pull(self, values):
        pass
    @abstractmethod
    def _push(self, window):
        pass
    def _init_window(self, window):
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Edit')
    
    class WindowEditContained(AbstractBlockingWindow):
        def __init__(self, title, contained) -> None:
            check_if_instances(contained, [iEdittable])
            self.contained = contained
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
            self.em.handle_event_function(self.contained.handle_event)
            self.em.true_event('Ok')
            self.em.false_event(sg.WIN_CLOSED)
    
    def define_events(self):
        super().define_events()
        @self.event(self.keys['Edit'])
        def event_edit(context):
            window_edit = ListContainer.WindowEditContained('Edit', self.ge)
            rv = window_edit.open(context)
            if not rv:
                return
            self.load(window_edit.get_data())
            self.push(context.window)
    
    # Other
    ###

# show the count of the contained list
class CountContainer(ListContainer):
    def __init__(self, text, ge:GuiElement) -> None:
        check_if_instances(ge, [GuiElement, iLength])
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
        window[self.keys['Count']](str(len(self.ge)))
    
    # Keys and Events

    def define_keys(self):
        super().define_keys()
        self.add_key('Count')
    
    def define_events(self):
        super().define_events()

    # Other
    ###

# Show the contained list as a string
class StringContainer(ListContainer):
    def __init__(self, text, ge:GuiElement, folder_browse=False, blank_invalid=False, has_validity=False) -> None:
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
        @self.event(self.keys['Add'])
        def event_add(context):
            path = context.values[self.keys['Add']]
            if path:
                self.ge.add_item(path)
            self.push(context.window)
        
        @self.event(self.keys['In'])
        def event_in(context):
            self.pull(context.values)
            self.push_validity(context.window)

    # Other
    
    ### iValid
    
    def _push_validity(self, window):
        sg_in = window[self.keys['In']]
        if self.is_valid():
            sg_in.update(background_color = colors.valid)
        else:
            sg_in.update(background_color = colors.invalid)
    def _is_valid(self):
        if self.blank_invalid and not len(self.ge):
            return False
        return True
