import PySimpleGUI as sg
import tkinter as tk

__all__ = [
    'button_size',
    'browse_folder',
    'browse_file',
    'browse_files',
    'MenuBar',
    'EmbedText',
    'center_window',
    'set_cursor_to_end'
]

taskbar_height = 50
def center_window(window:sg.Window):
    width_window = window.TKroot.winfo_width()
    height_window = window.TKroot.winfo_height()
    width_screen = window.TKroot.winfo_screenwidth()
    height_screen = window.TKroot.winfo_screenheight()
    height_screen_actual = height_screen - taskbar_height

    x = int((width_screen - width_window)/2)
    y = int((height_screen_actual - height_window)/2)
    window.move(x, y)


class button_size:
    def at_least(w, text):
        """Autosize for button with min width. Useful for uniform-width buttons with varying text.
        Returns width:int"""
        if len(text) > w:
            w = len(text) + 1
        return w

def browse_folder_button(text, key): return sg.Input(key=key, enable_events=True, visible=False), sg.FolderBrowse(text)
def browse_files_button(text, key): return sg.Input(key=key, enable_events=True, visible=False), sg.FilesBrowse(text)

def browse_folder(window:sg.Window, initialdir=None):
    if sg.running_mac():  # macs don't like seeing the parent window (go firgure)
        folder_name = tk.filedialog.askdirectory(initialdir=initialdir)  # show the 'get folder' dialog box
    else:
        folder_name = tk.filedialog.askdirectory(initialdir=initialdir, parent=window.TKroot)  # show the 'get folder' dialog box
    return folder_name

def browse_file(window:sg.Window, initialdir=None):
    if sg.running_mac():  # macs don't like seeing the parent window (go firgure)
        folder_name = tk.filedialog.askopenfilename(initialdir=initialdir)  # show the 'get folder' dialog box
    else:
        folder_name = tk.filedialog.askopenfilename(initialdir=initialdir, parent=window.TKroot)  # show the 'get folder' dialog box
    return folder_name

def browse_files(window:sg.Window, initialdir=None):
    if sg.running_mac():  # macs don't like seeing the parent window (go firgure)
        folder_name = tk.filedialog.askopenfilenames(initialdir=initialdir)  # show the 'get folder' dialog box
    else:
        folder_name = tk.filedialog.askopenfilenames(initialdir=initialdir, parent=window.TKroot)  # show the 'get folder' dialog box
    return folder_name

def set_cursor_to_end(sg_element):
    if isinstance(sg_element, sg.Input):
        sg_element.Widget.icursor(len(sg_element.get()))

def multiline_append_str(sge_ml, s):
    sge_ml.update(s, append=True)
def multiline_append_color_text(sge_ml, s, text_color=None, background_color=None):
    kwargs = {}
    if text_color != None:
        kwargs['text_color_for_value'] = text_color
        kwargs['background_color_for_value'] = background_color
    sge_ml.update(s, append=True, **kwargs)

class MenuNode:
    def __init__(self, id, text=None, sep='::', locked=True, disable_tags=None):
        """This class represents a PySimpleGUI menu tree.\n
        The format is 'id' or 'text::id''\n
        sep: string between 'id' and 'text' in event key\n
        id: 'id' if no text, otherwise 'text'\n
        __getitem__(): returns id\n
        get_event_key(): returns the entire string, 'id' or 'id::text'\n
        update(): takes 0-2 args, being (text) if one arg or (id, text) if two args\n
        mymenu['EntryA']['EntryA1']('Entry A1', disable_tags=('read_only',)\n
        without declaring 'EntryA' or 'EntryA1' beforehand"""
        self.id = id
        self.text = text
        self.sep = sep
        self.disable_tags = set(disable_tags) if disable_tags != None else set()
        self.nodes = {}
        self.locked = locked
    def __getitem__(self, id):
        if not id in self.nodes:
            if self.locked:
                raise KeyError(id)
            else:
                self.nodes[id] = MenuNode(id, locked=self.locked)
        return self.nodes[id]
    def __call__(self, *args, **kwargs):
        self.update(*args, **kwargs)
    def get_event_key(self, disabled=False):
        if self.text != None:
            key = self.text + self.sep + self.id
        else:
            key = self.id
        if disabled:
            key = '!' + key
        return key
    def update(self, text=None, disable_tags=None):
        if text != None:
            self.text = text
        if disable_tags != None:
            self.disable_tags.update(disable_tags)
    def get_def(self, disabled=False, disable_tags=None):
        """Returns disabled def if 'disabled' is True or if matches any of disable_tags"""
        if disable_tags != None and self.disable_tags.intersection(disable_tags):
            disabled = True
        entry_defs = []
        for node in self.nodes.values():
            entry_defs.append(node.get_def(disabled=disabled, disable_tags=disable_tags))
        
        if entry_defs:
            menu_def = [self.get_event_key(disabled), entry_defs]
        else:
            menu_def = self.get_event_key(disabled)
        
        return menu_def
    def unlock(self):
        self.locked = False
        for node in self.nodes.values():
            node.unlock()
    def lock(self):
        self.locked = True
        for node in self.nodes.values():
            node.lock()

class MenuDict:
    def __init__(self, locked=True):
        self.nodes = {}
        self.locked = locked
    def __getitem__(self, id):
        if not id in self.nodes:
            if self.locked:
                raise KeyError(id)
            else:
                self.nodes[id] = MenuNode(id, locked=self.locked)
        return self.nodes[id]
    def unlock(self):
        self.locked = False
        for node in self.nodes.values():
            node.unlock()
    def lock(self):
        self.locked = True
        for node in self.nodes.values():
            node.lock()

class MenuBar(MenuDict):
    def get_def(self):
        menu_def = []
        for menu_node in self.nodes.values():
            menu_def.append(menu_node.get_def())
        return menu_def

class EmbedText:
    def __init__(self, s=None) -> None:
        self.strings:list[tuple[dict[str, str], str]] = []
        if s:
            self += s
    def __iadd__(self, other):
        return self.append(other)
    def append(self, other):
        if isinstance(other, str):
            self.strings.append([{}, other])
        else:
            s_formats = other[0]
            formats = EmbedText.process_format_string(s_formats)
            s = other[1]
            self.strings.append([formats, s])
        return self
    def process_format_string(formats):
        format_list = formats.split(';')
        f = {}
        for s_f in format_list:
            parts = s_f.split(':')
            k = parts[0]
            if len(parts) > 1:
                v = parts[1]
            else:
                v = None
            f[k] = v
        return f
    def color(self, s, text_color=None, background_color=None):
        f = {}
        if text_color:
            f['text_color'] = text_color
        if background_color:
            f['background_color'] = background_color
        self.strings.append((f, s))
    def print_to_multiline(self, sge_ml:sg.Multiline):
        sge_ml.update('')
        for f, s in self.strings:
            text_color = background_color = None
            if 'text_color' in f.keys():
                text_color = f['text_color']
            if 'background_color' in f.keys():
                background_color = f['background_color']
            multiline_append_color_text(sge_ml, s, text_color, background_color)


def test():
    et = EmbedText()
    et += 'This is unformatted text, but '
    et += ('')
