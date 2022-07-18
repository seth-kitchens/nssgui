import copy
from abc import ABC, abstractmethod
import re

import PySimpleGUI as sg

from psgu.event_handling import WRC, EventContext
from psgu.gui_element import *
from psgu.popup import popups
from psgu.data.ordered_dict import OrderedDict
from psgu import sg as psgu_sg
from psgu.window_context import WindowContext


__all__ = ['DetailList']


def clone_string_unique(s, not_in_strings=None):
    if not_in_strings == None:
        not_in_strings = []
    if (match := re.search('_([0-9]+)$', s)) != None:
        i = int(match.group(1)) + 1
        s = s[:match.start()] + '_'
    else:
        i = 1
        s = s + '_'
    while (s + str(i)) in not_in_strings:
        i += 1
    return s + str(i)


class DetailList(GuiElement.iLayout, GuiElement, GuiElement.iLength, ABC):
    
    def __init__(self, object_id, lstrip=' \n', rstrip=' \n'):
        """
        An abstract class representing an edittable dict: 
            item_dict:dict[item:str, data:Any]
        """
        super().__init__(object_id)
        self.lstrip = lstrip
        self.rstrip = rstrip
        self.item_dict = OrderedDict()
        self.selection = None
    
    ### GuiElement

    # Layout
    
    def _get_layout(self):
        move_button_size = (2, 1)
        column_move_buttons = sg.Column([
            [sg.Button('⇑', key=self.keys['MoveToTop'], size=move_button_size)],
            [sg.Button('↑', key=self.keys['MoveUp'], size=move_button_size)],
            [sg.Button('↓', key=self.keys['MoveDown'], size=move_button_size)],
            [sg.Button('⇓', key=self.keys['MoveToBottom'], size=move_button_size)]
        ])
        column_listbox = sg.Column(expand_x=True, expand_y=True, layout=[
            [
                column_move_buttons,
                lb := psgu_sg.Listbox(values=self.item_dict.keys(),
                    key=self.keys['Listbox'],
                    size=(30, 7),
                    expand_x=True,
                    expand_y=True,
                    enable_events=True,
                    bind_return_key=True,
                    right_click_menu=self.right_click_menus['ListboxNone'].get_def(),
                    right_click_selects=True
                )
            ]
        ])
        self.lb = lb
        row_buttons_main_top = self.get_row_buttons_main_top()
        row_buttons_main_bottom = self.get_row_buttons_main_bottom()
        column_buttons_main = sg.Column(expand_x=True, layout=[
            row_buttons_main_top,
            row_buttons_main_bottom
        ])
        column_right = sg.Column(expand_x=True, layout=[
            [
                sg.Multiline('',
                    key=self.keys['Details'], size=(50, 7), expand_x=True, disabled=True)
            ],
            [
                column_buttons_main,
                sg.Push()
            ]
        ])
        layout = [[
            column_listbox,
            column_right
        ]]
        return layout

    def get_row_buttons_main_top(self):
        size = (8, 1)
        row = [
            sg.Button('Add', key=self.keys['Add'], size=size),
            sg.Button('Edit', key=self.keys['Edit'], size=size),
            sg.Button('Remove', key=self.keys['Remove'], size=size)
        ]
        return row

    def get_row_buttons_main_bottom(self):
        size = (8, 1)
        row = [
            sg.Button('Clone', key=self.keys['Clone'], size=size),
            sg.Button('Rename', key=self.keys['Rename'], size=size),
            sg.Button('Remove All', key=self.keys['RemoveAll'], size=size)
        ]
        return row
    
    # Data
    
    def _save(self, data):
        d = {}
        for k, v in self.item_dict.to_pairs():
            d[k] = self.pack_data(v)
        data[self.object_id] = d
    
    def _load(self, data):
        self.item_dict.clear()
        for k, v in data[self.object_id].items():
            self.item_dict[k] = self.unpack_data(v)
    
    def _push(self, window:sg.Window):
        highlighted = [self.selection] if self.selection else []
        sge_listbox:sg.Listbox = window[self.keys['Listbox']]
        sge_listbox.update(self.item_dict.keys())
        sge_listbox.set_value(highlighted)
        if self.selection:
            sge_listbox.set_right_click_menu(self.right_click_menus['ListboxItem'].get_def())
        else:
            sge_listbox.set_right_click_menu(self.right_click_menus['ListboxNone'].get_def())
        self.update_details(window)
    
    def _init_window_finalized(self, window:sg.Window):
        window[self.keys['Listbox']].Widget.config(activestyle='none')
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Listbox')
        self.add_key('Details')
        self.add_key('Add')
        self.add_key('Edit')
        self.add_key('Rename')
        self.add_key('Remove')
        self.add_key('RemoveAll')
        self.add_key('Clone')
        self.add_key('MoveUp')
        self.add_key('MoveDown')
        self.add_key('MoveToTop')
        self.add_key('MoveToBottom')
    
    def define_menus(self):
        rcms = self.right_click_menus
        rcms.unlock()
        rcms['ListboxNone']['Add']('Add')

        rcms['ListboxItem']['Edit']('Edit')
        rcms['ListboxItem']['Rename']('Rename')
        rcms['ListboxItem']['Remove']('Remove')
        rcms['ListboxItem']['Clone']('Clone')
        rcms['ListboxItem']['Deselect']('Deselect')
        rcms.lock()

    def define_events(self):
        super().define_events()
        
        @self.eventmethod(self.keys['Listbox'])
        def event_listbox(event_context:EventContext):
            window = event_context.window_context.window
            sge_listbox = window[self.keys['Listbox']]
            is_double_click = False
            if not sge_listbox.is_right_click():
                if self.check_double_click('Listbox'):
                    is_double_click = True
            selections = event_context.values[self.keys['Listbox']]
            if not len(selections):
                return
            if is_double_click and (self.selection != None) and (self.selection == selections[0]):
                event_context.event = self.keys['Edit']
                self.handle_event(event_context)
                return
            self.selection = selections[0]
            self.update_details(window)
            self.push(event_context.window_context.window)
        
        @self.eventmethod(self.key_rcm('ListboxItem', 'Deselect'))
        def event_deselect(event_context:EventContext):
            self.selection = None
            window = event_context.window_context.window
            self.update_details(window)
            self.push(window)
        
        @self.eventmethod(self.key_rcm('ListboxItem', 'Edit'))
        @self.eventmethod(self.keys['Edit'])
        def event_edit(event_context:EventContext):
            if not self.selection:
                return
            item = self.selection
            data = self.item_dict[item]
            rv, data = self.edit_data(event_context.window_context, item, data)
            if not rv.success():
                return
            self.item_dict[item] = data
            self.push(event_context.window_context.window)
        
        @self.eventmethod(self.key_rcm('ListboxItem', 'Rename'))
        @self.eventmethod(self.keys['Rename'])
        def event_rename(event_context:EventContext):
            if not self.selection:
                return
            item = popups.edit_string(event_context, '', 
                title='Rename', body_text=['Previous: "' + self.selection + '"'])
            item = item.lstrip(self.lstrip).rstrip(self.rstrip)
            if not item:
                return
            item_data = self.item_dict[self.selection]
            if item in self.item_dict.key_list:
                if not popups.confirm(event_context, 'Overwrite existing entry "' + item + '" ?'):
                    return
            index = self.item_dict.index(self.selection)
            self.item_dict.remove(self.selection)
            self.item_dict.insert(index, item, item_data)
            self.selection = item
            self.push(event_context.window_context.window)
        
        @self.eventmethod(self.key_rcm('ListboxItem', 'Remove'))
        @self.eventmethod(self.keys['Remove'])
        def event_remove(event_context:EventContext):
            if not self.selection:
                return
            self.item_dict.remove(self.selection)
            self.selection = None
            self.push(event_context.window_context.window)
        
        @self.eventmethod(self.key_rcm('ListboxItem', 'Clone'))
        @self.eventmethod(self.keys['Clone'])
        def event_clone(event_context:EventContext):
            if not self.selection:
                return
            item = clone_string_unique(self.selection, self.item_dict.key_list)
            data = copy.deepcopy(self.item_dict[self.selection])
            self.item_dict.insert_after_key(self.selection, item, data)
            self.push(event_context.window_context.window)
        
        @self.eventmethod(self.key_rcm('ListboxNone', 'Add'))
        @self.eventmethod(self.keys['Add'])
        def event_add(event_context:EventContext):
            item = popups.edit_string(event_context, '', label='Name:', title='Add')
            item = item.lstrip(self.lstrip).rstrip(self.rstrip)
            if not item:
                return
            if item in self.item_dict.key_list:
                popups.ok(event_context, 
                    text='Entry of name "{}" already exists.'.format(item),
                    title='Entry Exists')
                return
            rv, data = self.edit_data(event_context.window_context, item, None)
            if not rv.check_success():
                return rv
            self.item_dict[item] = data
            self.selection = item
            self.push(event_context.window_context.window)
            return rv
        
        @self.eventmethod(self.keys['RemoveAll'])
        def event_remove_all(event_context:EventContext):
            if not len(self):
                return
            if not popups.warning(event_context.window_context, 'Remove all entries?'):
                return
            self.item_dict.clear()
            self.selection = None
            self.push(event_context.window_context.window)
        
        @self.eventmethod(self.keys['MoveUp'])
        def event_move_up(event_context:EventContext):
            if not self.selection:
                return
            self.item_dict.move_forward(self.selection)
            self.push(event_context.window_context.window)
        
        @self.eventmethod(self.keys['MoveDown'])
        def event_move_down(event_context:EventContext):
            if not self.selection:
                return
            self.item_dict.move_back(self.selection)
            self.push(event_context.window_context.window)
        
        @self.eventmethod(self.keys['MoveToTop'])
        def event_move_to_top(event_context:EventContext):
            if not self.selection:
                return
            self.item_dict.move_to_front(self.selection)
            self.push(event_context.window_context.window)
        
        @self.eventmethod(self.keys['MoveToBottom'])
        def event_move_to_bottom(event_context:EventContext):
            if not self.selection:
                return
            self.item_dict.move_to_back(self.selection)
            self.push(event_context.window_context.window)

    # Other

    ### DetailList

    @abstractmethod
    def make_details(self, item, data) -> psgu_sg.EmbedText:
        pass

    @abstractmethod
    def edit_data(self, window_context:WindowContext, item, data) -> tuple[WRC, str]:
        """Returns: WRC, data"""
        pass

    @abstractmethod
    def pack_data(self, data):
        pass

    @abstractmethod
    def unpack_data(self, packed_data):
        pass

    # iLength

    def __len__(self):
        return len(self.item_dict)
    
    # Other
    
    def update_details(self, window):
        if not self.selection:
            window[self.keys['Details']]('')
            return
        item = self.selection
        data = self.item_dict[item]
        embed_text = self.make_details(item, data)
        sge_ml = window[self.keys['Details']]
        embed_text.print_to_multiline(sge_ml)

    def get_selection(self):
        if not self.selection:
            return None, None
        return self.selection, self.item_dict[self.selection]
    
    def get_through_selection(self):
        """Get items in list through selection as dict, (i.e. [:selection_index+1])"""
        items = {}
        if not self.selection:
            return items
        index = self.item_dict.index(self.selection)
        for i in range(0, index+1):
            item, data = self.item_dict.get_at(i)
            items[item] = data
        return items
    
    def get_pairs(self):
        return self.item_dict.to_pairs()
    
    def get_dict(self):
        return dict(self.item_dict.to_pairs())

    def remove_through_selection(self):
        """Remove items in list through selection, (i.e. [:selection_index+1])"""
        if not self.selection:
            return
        index = self.item_dict.index(self.selection)
        for i in range(index+1):
            self.item_dict.pop(0)
        self.selection = None

    def remove_all(self):
        self.item_dict.clear()
        self.selection = None
