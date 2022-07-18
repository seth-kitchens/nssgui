import json
from typing import Any, Iterable

import PySimpleGUI as sg

from psgu.gui_element import *
from psgu.popup import popups
from psgu.sg import wrapped as sg_wrapped


__all__ = ['TextList']


class TextList(GuiElement.iLayout, GuiElement, GuiElement.iLength, GuiElement.iStringable, GuiElement.iEdittable):
    
    def __init__(self,
            object_id,
            delim=None,
            border:str|Iterable='', 
            strip:str|Iterable='',
            empty_text='',
            allow_duplicates=False):
        super().__init__(object_id)
        self.delim = delim
        if isinstance(border, str):
            self.lborder = border
            self.rborder = border
        else:
            self.lborder = border[0]
            self.rborder = border[1]
        if isinstance(strip, str):
            self.lstrip = strip
            self.rstrip = strip
        else:
            self.lstrip = strip[0]
            self.rstrip = strip[1]
        self.items = []
        self.selected_index = None
        self.empty_text = empty_text if empty_text else ''
        self.allow_duplicates = allow_duplicates
    
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
        main_button_kwargs = {
            'size': (8, 1)
        }
        row_buttons_main_top = [
            sg.Button('Add', key=self.keys['Add'], **main_button_kwargs),
            sg.Button('Edit', key=self.keys['Edit'], **main_button_kwargs),
            sg.Button('Clone', key=self.keys['Clone'], **main_button_kwargs)
        ]
        row_buttons_main_bottom = [
            sg.Button('Remove', key=self.keys['Remove'], expand_x=True, **main_button_kwargs),
            sg.Button('Remove All',
                key=self.keys['RemoveAll'], expand_x=True, **main_button_kwargs)
        ]
        column_buttons_main = sg.Column(justification='center', layout=[
            row_buttons_main_top,
            row_buttons_main_bottom
        ])
        layout = [
            [column_move_buttons, self.get_sge_listbox()],
            [column_buttons_main]
        ]
        return layout
    
    def get_sge_listbox(self, keys=None):
        keys = keys if keys else self.keys
        listbox_height = len(self.items)
        if listbox_height < 3: listbox_height = 5
        elif listbox_height > 10: listbox_height = 10
        if self.selected_index == None:
            rcm_listbox = self.right_click_menus['ListboxNone']
        else:
            rcm_listbox = self.right_click_menus['ListboxItem']
        return sg_wrapped.Listbox(self.get_display_list(),
            key=keys['Listbox'], size=(30, listbox_height), expand_x=True, expand_y=True,
            enable_events=True, bind_return_key=True, right_click_menu=rcm_listbox.get_def(),
            right_click_selects=True)    
    
    # Data
    
    def _save(self, data):
        if not self.allow_duplicates:
            self.items = list(set(self.items))
        data[self.object_id] = self.items.copy()
    
    def _load(self, data):
        self.items.clear()
        self.items.extend(data[self.object_id])
    
    def _pull(self, values):
        pass
    
    def _push(self, window):
        sge_listbox:sg_wrapped.Listbox = window[self.keys['Listbox']]
        sge_listbox.update(self.get_display_list())
        if self.selected_index != None:
            sge_listbox.set_value([self.get_selected_display_item()])
            sge_listbox.set_right_click_menu(self.right_click_menus['ListboxItem'].get_def())
        else:
            sge_listbox.update(set_to_index=[])
            sge_listbox.set_right_click_menu(self.right_click_menus['ListboxNone'].get_def())
    
    def _init_window_finalized(self, window):
        window[self.keys['Listbox']].Widget.config(activestyle='none')
        self.push(window)
    
    # Keys and Events

    def define_keys(self):
        super().define_keys()
        self.add_key('Listbox')
        self.add_key('Add')
        self.add_key('Edit')
        self.add_key('Remove')
        self.add_key('RemoveAll')
        self.add_key('Clone')
        self.add_key('MoveUp')
        self.add_key('MoveDown')
        self.add_key('MoveToTop')
        self.add_key('MoveToBottom')

    def define_menus(self):
        super().define_menus()
        rcms = self.right_click_menus
        rcms.unlock()
        rcms['ListboxNone']['Add']('Add')

        rcms['ListboxItem']['Edit']('Edit')
        rcms['ListboxItem']['Remove']('Remove')
        rcms['ListboxItem']['Clone']('Clone')
        rcms.lock()

    def define_events(self):
        super().define_events()
        
        @self.eventmethod(self.keys['Listbox'])
        def event_listbox(context):
            sge_listbox = context.window[self.keys['Listbox']]
            is_double_click = False
            if not sge_listbox.is_right_click():
                if self.check_double_click('Listbox'):
                    is_double_click = True
            if not self.items:
                self.deselect()
                self.push(context.window)
                return
            if is_double_click:
                context.event = self.key_rcm('ListboxItem', 'Edit')
                return self.handle_event(context)
            selections = context.window[self.keys['Listbox']].get_indexes()
            if len(selections):
                self.selected_index = selections[0]
            self.push(context.window)
    
        @self.eventmethod(self.key_rcm('ListboxItem', 'Edit'))
        @self.eventmethod(self.keys['Edit'])
        def event_edit(context):
            if self.selected_index == None:
                return
            item = self.get_selected_item()
            new_item = popups.edit_string(context, item, title='Edit')
            if new_item == item:
                return
            if new_item in self.items:
                rv = popups.choose(context,
                    text='"{}" already exists. Remove "{}" ?'.format(new_item, item),
                    options=['Remove', 'Cancel'])
                if rv != 'Remove':
                    return
                self.items.remove(item)
                self.selected_index = None
                self.push(context.window)
                return
            new_item = self.format_item(new_item)
            if new_item == '':
                self.items.remove(item)
                self.selected_index = None
            elif (not new_item) or new_item == item:
                return
            else:
                self.items[self.selected_index] = new_item
                self.select_item(new_item)
            self.push(context.window)
        
        @self.eventmethod(self.key_rcm('ListboxItem', 'Remove'))
        @self.eventmethod(self.keys['Remove'])
        def event_remove(context):
            if self.selected_index == None:
                return
            self.items.pop(self.selected_index)
            self.deselect()
            self.push(context.window)
        
        @self.eventmethod(self.keys['RemoveAll'])
        def event_remove_all(context):
            if not len(self):
                return
            if not popups.warning(context, 'Remove all entries?'):
                return
            self.items.clear()
            self.deselect()
            self.push(context.window)
        
        @self.eventmethod(self.key_rcm('ListboxItem', 'Clone'))
        @self.eventmethod(self.keys['Clone'])
        def event_clone(context):
            if self.selected_index == None:
                return
            item = popups.edit_string(context, self.get_selected_item(), title='Clone')
            item = self.format_item(item)
            if not item:
                return
            if item in self.items:
                return
            self.items.append(item)
            self.select_item(item)
            self.push(context.window)

        @self.eventmethod(self.key_rcm('ListboxNone', 'Add'))
        @self.eventmethod(self.keys['Add'])
        def event_add(context):
            item = popups.edit_string(context, '', title='Add')
            item = self.format_item(item)
            if not item:
                return
            if item in self.items:
                popups.ok(context, '"' + item + '" already exists.')
                return
            self.items.append(item)
            self.select_item(item)
            self.push(context.window)
        
        @self.eventmethod(self.keys['MoveUp'])
        def event_move_up(context):
            if self.selected_index == None:
                return
            index = self.selected_index
            if index == 0:
                return
            temp = self.items[index-1]
            self.items[index-1] = self.items[index]
            self.items[index] = temp
            self.selected_index -= 1
            self.push(context.window)
        
        @self.eventmethod(self.keys['MoveDown'])
        def event_move_down(context):
            if self.selected_index == None:
                return
            index = self.selected_index
            if index + 1 >= len(self.items):
                return
            temp = self.items[index+1]
            self.items[index+1] = self.items[index]
            self.items[index] = temp
            self.selected_index += 1
            self.push(context.window)
        
        @self.eventmethod(self.keys['MoveToTop'])
        def event_move_to_top(context):
            if self.selected_index == None:
                return
            item = self.get_selected_item()
            self.items.pop(self.selected_index)
            self.items.insert(0, item)
            self.selected_index = 0
            self.push(context.window)
        
        @self.eventmethod(self.keys['MoveToBottom'])
        def event_move_to_bottom(context):
            if self.selected_index == None:
                return
            item = self.get_selected_item()
            self.items.pop(self.selected_index)
            self.items.append(item)
            self.selected_index = len(self.items) - 1
            self.push(context.window)

    # Other

    ### TextList

    # iLength

    def __len__(self):
        return len(self.items)

    # iStringable

    def to_string(self):
        self.format_items()
        if self.delim:
            s_join = self.delim
            if ' ' in self.lstrip:
                s_join += ' '
            return s_join.join(self.items.copy())
        else:
            return json.dumps(self.items)
    def load_string(self, s):
        self.items.clear()
        if self.delim:
            items = s.split(self.delim)
        else:
            items = json.loads(s)
        for item in items:
            item = self.format_item(item)
            if item:
                self.items.append(item)
    
    # iEdittable

    def get_edit_layout(self):
        return self.get_layout()

    # Other

    def add_item(self, item):
        self.items.append(item)
    
    def get_selected_item(self):
        return self.items[self.selected_index]
    
    def get_selected_display_item(self):
        return self.item_to_display_item(self.items[self.selected_index])
    
    def select_item(self, item):
        self.selected_index = self.items.index(item)
    
    def deselect(self):
        self.selected_index = None
    
    def format_item(self, item):
        return item.lstrip(self.lstrip).rstrip(self.rstrip)
    
    def format_items(self):
        items = self.items.copy()
        self.items.clear()
        for item in items:
            item = self.format_item(item)
            if item:
                self.items.append(item)
    
    def item_to_display_item(self, item):
        return self.lborder + item + self.rborder
    
    def display_item_to_item(self, display_item):
        return display_item[len(self.lborder):0 - len(self.rborder)]
    
    def get_display_list(self):
        display_list = []
        for item in self.items:
            display_list.append(self.item_to_display_item(item))
        if not display_list:
            display_list.append(self.empty_text)
        return display_list

    

