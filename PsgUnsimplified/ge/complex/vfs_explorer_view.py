import os

import PySimpleGUI as sg

from PsgUnsimplified.text import utils as text_utils
from PsgUnsimplified.data import units as unit
from PsgUnsimplified.fs.vfs import VFS
from PsgUnsimplified.fs.vfs_explorer import VFSExplorer
from PsgUnsimplified.gui_element import *
from PsgUnsimplified.popup import popups
from PsgUnsimplified.sg import wrapped as sg_wrapped
from PsgUnsimplified.text.utils import TableList
from PsgUnsimplified import g as sgu_g
from PsgUnsimplified import ge as sgu_el
from PsgUnsimplified import sg as sgu_sg


__all__ = ['VFSExplorerView']


class VFSExplorerView(GuiElement.iLayout, GuiElement):
    
    def __init__(self, object_id, vfs_explorer, read_only=False) -> None:
        self.read_only = read_only
        super().__init__(object_id)
        self.vfs_explorer:VFSExplorer = vfs_explorer
        self.vfs:VFS = vfs_explorer.vfs
        self.display_list:list[str] = []
        self.selection = None
        self.selected_row = None
    
    ### GuiElement

    # Layout
    
    def _get_layout(self):
        layout = self.get_layout_explorer()
        if not self.read_only:
            row_actions = self._get_row_actions()
            layout.append(row_actions)
        return layout

    _nav_button_kwargs = {
        'size': (5, 4),
        'expand_y': True
    }

    def _get_row_current_path(self):
        row_current_path = [
            sg.Sizer(6, 0),
            sg.Text('Current'),
            sg.Sizer(5, 0),
            *self.row(sgu_el.Input(self.keys['CurrentPath'], '') \
                ._set_sg_kwargs('In', readonly=True, expand_x=True) \
                .load_value('""'))
        ]
        return row_current_path
    
    def _get_row_details(self):
        button_root_folder = sg.Button('Root',
            key=self.keys['ExitToRoot'], **self._nav_button_kwargs)
        row_details = [
            sg.Column(layout=[[button_root_folder]]),
            sg.Multiline(
                key=self.keys['Details'], 
                size=(sgu_g.explorer_list_width, 5),
                expand_x=True,
                disabled=True)
        ]
        return row_details
    
    def _get_row_listbox(self):
        button_open_folder = sg.Button('>>>>\n\nOpen\n\n>>>>',
            key=self.keys['OpenFolder'], **self._nav_button_kwargs)
        button_exit_folder = sg.Button('<<<<\n\nBack\n\n<<<<', 
            key=self.keys['ExitFolder'], **self._nav_button_kwargs)
        column_nav_buttons = sg.Column(expand_x=True, expand_y=True, layout=[
            [button_open_folder],
            [button_exit_folder]
        ])
        right_click_menu = self.right_click_menus['ListboxNone'].get_def()
        right_click_selects = True
        item_list_size = (sgu_g.explorer_list_width, 12)
        sge_item_list = sg_wrapped.Listbox(values=[],
            key=self.keys['Listbox'],
            enable_events=True,
            bind_return_key=True,
            size=item_list_size,
            expand_x=True,
            font=sgu_g.explorer_list_font,
            right_click_menu=right_click_menu,
            right_click_selects=right_click_selects
        )
        row_listbox = [
            column_nav_buttons,
            sge_item_list
        ]
        return row_listbox
    
    def get_layout_explorer(self):
        row_current_path = self._get_row_current_path()
        row_details = self._get_row_details()
        row_listbox = self._get_row_listbox()
        layout = [
            row_current_path,
            row_details,
            row_listbox,
        ]
        return layout
    
    def _get_row_actions(self):
        control_button_kwargs = {
            'size': (10, 1)
        }
        row = [
            sg.Sizer(65, 0),
            sg.Button('Add Folder',
                key=self.keys['AddFolder'], **control_button_kwargs),
            sg.Button('Add Files',
                key=self.keys['AddFiles'], **control_button_kwargs),
            sg.Button('Remove',
                key=self.keys['Remove'], **control_button_kwargs),
            sg.Button('Remove All',
                key=self.keys['RemoveAll'], **control_button_kwargs)
        ]
        return row

    # Data
    
    def _push(self, window):
        self.update_rcm(window)
        self.vfs_explorer.refresh_current_dir()
        if self.selection:
            entry_details = self.get_entry_details(self.selection)
        else:
            entry_details = ''
        window[self.keys['Details']](entry_details)
        if self.vfs_explorer.current_dir_entry == None:
            current_path = ''
        else:
            current_path = self.vfs_explorer.current_dir_entry.get_path()
        self.ges('CurrentPath').update(window, current_path)
        self.refresh_display_list()
        window[self.keys['Listbox']](self.get_display_list())
        if self.selection:
            window[self.keys['Listbox']].set_value(self.selected_row)
    
    def _init_window_finalized(self, window):
        window[self.keys['Listbox']].Widget.config(activestyle='none')
        self.vfs_explorer.refresh_current_dir()
        self.push(window)
    
    def update_rcm(self, window):
        if self.selection:
            if self.selection.is_dir():
                rcm = self.right_click_menus['ListboxFolder']
            else:
                rcm = self.right_click_menus['ListboxFile']
        else:
            rcm = self.right_click_menus['ListboxNone']
        disable_tags = []
        if self.read_only:
            disable_tags.append('read_only')
        rcm_def = rcm.get_def(disable_tags=disable_tags)
        window[self.keys['Listbox']].set_right_click_menu(rcm_def)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('OpenFolder')
        self.add_key('ExitFolder')
        self.add_key('ExitToRoot')
        self.add_key('AddFolder')
        self.add_key('AddFiles')
        self.add_key('Remove')
        self.add_key('RemoveAll')
        self.add_key('Exclude')
        self.add_key('Include')
        self.add_key('Listbox')
        self.add_key('CurrentPath')
        self.add_key('Details')

    def define_menus(self):
        super().define_menus()
        rcms = self.right_click_menus
        rcms.unlock()
        rcms['ListboxNone']['AddFolder']('Add Folder', disable_tags=['read_only'])
        rcms['ListboxNone']['AddFiles']('Add Files', disable_tags=['read_only'])

        rcms['ListboxFolder']['Open']('Open')
        rcms['ListboxFolder']['Back']('Back')
        rcms['ListboxFolder']['Remove']('Remove', disable_tags=['read_only'])

        rcms['ListboxFile']['Back']('Back')
        rcms['ListboxFile']['Remove']('Remove', disable_tags=['read_only'])
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
            item_list = context.values[self.keys['Listbox']]
            if len(item_list) <= 0:
                return
            if item_list[0][1] == '#':
                self.deselect()
                self.push(context.window)
                return
            listbox_row = item_list[0]
            same_clicked = (listbox_row == self.selected_row)
            if same_clicked and is_double_click:
                context.event = self.key_rcm('ListboxFolder', 'Open')
                return self.handle_event(context)
            else:
                self.select(listbox_row)
                self.push(context.window)
        
        @self.eventmethod(self.key_rcm('ListboxFolder', 'Open'))
        def event_open_folder(context):
            if not self.selection:
                return
            entry = self.selection
            path = entry.get_path()
            self.vfs_explorer.open_folder(path)
            self.deselect()
            self.push(context.window)
        
        @self.eventmethod(self.key_rcm('ListboxFolder', 'Back'))
        @self.eventmethod(self.key_rcm('ListboxFile', 'Back'))
        @self.eventmethod(self.keys['ExitFolder'])
        def events_exit_folder(context):
            self.vfs_explorer.exit_folder()
            self.deselect()
            self.push(context.window)

        @self.eventmethod(self.key_rcm('ListboxFolder', 'Remove'))
        @self.eventmethod(self.key_rcm('ListboxFile', 'Remove'))
        @self.eventmethod(self.keys['Remove'])
        def event_remove(context):
            if not self.selection:
                return
            path = self.selection.get_path()
            self.vfs.remove(path)
            self.vfs.calc_all()
            self.vfs_explorer.refresh_current_dir()
            self.deselect()
            self.push(context.window)
        
        @self.eventmethod(self.key_rcm('ListboxNone', 'AddFolder'))
        @self.eventmethod(self.keys['AddFolder'])
        def event_add_folder(context):
            item_path = sgu_sg.browse_folder(context.window)
            if item_path == '':
                return
            self.vfs.add_path(item_path)
            self.vfs.calc_root(item_path)
            self.vfs_explorer.exit_to_root()
            self.push(context.window)
        
        @self.eventmethod(self.key_rcm('ListboxNone', 'AddFiles'))
        @self.eventmethod(self.keys['AddFiles'])
        def event_add_files(context):
            item_paths = sgu_sg.browse_files(context.window)
            if len(item_paths) <= 0:
                return
            for item_path in item_paths:
                self.vfs.add_path(item_path)
            self.vfs.calc_roots(item_paths)
            self.vfs_explorer.exit_to_root()
            self.push(context.window)
        
        @self.eventmethod(self.keys['ExitToRoot'])
        def events_exit_to_root(context):
            self.vfs_explorer.exit_to_root()
            self.deselect()
            self.push(context.window)
        
        @self.eventmethod(self.keys['RemoveAll'])
        def event_remove_all(context):
            if not popups.confirm(context, 'Remove All?'):
                return
            self.vfs.remove_all()
            self.vfs_explorer.refresh_current_dir()
            self.deselect()
            self.push(context.window)

    ### VFSExplorerView

    # Other

    def get_entry_details(self, entry):
        name = entry.name
        path = entry.path
        s = name + '   (' + path + ')'
        s += '\n\nType: '
        if os.path.isdir(path):
            s += 'Folder'
        else:
            s += 'File'
        size_best = unit.Bytes(entry.size, degree_name=unit.Bytes.BYTE) \
            .get_best()
        s += '\nSize: ' + size_best
        return s

    def refresh_display_list(self):
        self.display_list = []
        if self.vfs_explorer.current_dir_children == None:
            return
        i = 1
        display_table = TableList()
        display_table.add_row([
            '#', 'Typ', 'Name', 'Status', 'Inc Size',
            'Exc Size', 'I-F', 'I-f', 'E-F', 'E-f'
        ])
        for child in self.vfs_explorer.current_dir_children:
            i_size_value, i_size_symbol = unit.Bytes(int(child.get_included_size()), unit.Bytes.B).find_best(0.1)
            e_size_value, e_size_symbol = unit.Bytes(int(child.get_excluded_size()), unit.Bytes.B).find_best(0.1)
            i_size_value = round(i_size_value, 2)
            e_size_value = round(e_size_value, 2)
            i_size = text_utils.center_decimal_string(str(i_size_value), 2) + ' ' + i_size_symbol.rjust(2, ' ')
            e_size = text_utils.center_decimal_string(str(e_size_value), 2) + ' ' + e_size_symbol.rjust(2, ' ')
            display_table.add_row([
                str(i),
                child.get_type_symbol(),
                child.name,
                child.status,
                i_size,
                e_size,
                str(child.get_included_folder_count()),
                str(child.get_included_file_count()),
                str(child.get_excluded_folder_count()),
                str(child.get_excluded_file_count())
            ])
            i += 1
        display_table.trim_fields(sgu_g.explorer_list_width, [(2, 8)])
        rows = display_table.get_formatted_rows()
        for row in rows:
            self.display_list.append(row)
    
    def get_display_list(self):
        return self.display_list
    
    def resolve_listbox_row(self, listbox_row:str):
        start = listbox_row.find('[') + 1
        stop = listbox_row.find(']')
        index = int(listbox_row[start:stop])
        return self.vfs_explorer.current_dir_children[index - 1]
       
    def select(self, listbox_row):
        entry = self.resolve_listbox_row(listbox_row)
        self.selection = entry
        self.selected_row = listbox_row

    def deselect(self):
        self.selection = None
        self.selected_row = None
        
