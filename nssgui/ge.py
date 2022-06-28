from __future__ import annotations
from abc import ABC, abstractmethod
import time
from functools import wraps

import PySimpleGUI as sg
from nssgui import g as nss_g
from nssgui.event_manager import EventManager
from nssgui.sg.utils import MenuDict

__all__ = [
    'check_if_instances',
    'check_if_subclasses',
    'GuiElement',
    'GuiElementManager',
    'iLength',
    'iStringable',
    'iEdittable',
    'initafter'
]

def check_if_instances(obj, types:list):
    for t in types:
        if not isinstance(obj, t):
            raise TypeError('Obj ' + str(obj) + ' is not an instance of ' + str(t))
def check_if_subclasses(name, types:list):
    for t in types:
        if not issubclass(name, t):
            raise TypeError('Obj ' + str(name) + ' is not a subclass of ' + str(t))

class iLength(ABC):
    @abstractmethod
    def __len__(self):
        pass

class iStringable(ABC):
    @abstractmethod
    def to_string(self):
        pass
    @abstractmethod
    def load_string(self, s):
        pass

class iEdittable(ABC):
    """Can be editted with an 'Edit' button"""
    @abstractmethod
    def get_edit_layout(self):
        pass
    @abstractmethod
    def handle_event(self, context):
        pass

def initafter(f):
    @wraps(f)
    def func(*args, **kwargs):
        rv = f(*args, **kwargs)
        if 'self' in kwargs:
            obj = kwargs['self']
        else:
            obj = args[0]
        if not obj.events_defined:
            obj.define_events()
            obj.events_defined = True
        return rv
    return func


# GuiElement Manager

class GuiElementManager:
    num_gems = 0
    num_gem_keys = 0
    def __init__(self):
        self.gem_id = GuiElementManager.num_gems
        GuiElementManager.num_gems += 1
        self.ges = {}
        self.gem_keys = {}

        self.status_bar_key = None
    def __getitem__(self, key):
        return self.ges[key]
    def __setitem__(self, key, value):
        self.ges[key] = value
    def add_ge(self, ge, do_overwrite=False):
        id = ge.object_id
        if do_overwrite or not id in self.ges.keys():
            ge.init()
            self.ges[id] = ge
    
    # add an object if it doesn't already exist and return its layout elements

    def layout(self, ge):
        self.add_ge(ge)
        return self.ges[ge.object_id].get_layout()
    def row(self, ge):
        self.add_ge(ge)
        return self.ges[ge.object_id].get_row()
    def sge(self, ge):
        self.add_ge(ge)
        return self.ges[ge.object_id].get_sge()
    
    def save_all(self, data):
        for ge in self.ges.values():
            ge.save(data)
    def load_all(self, data):
        for ge in self.ges.values():
            ge.load(data)
    def init_window_all(self, window):
        for ge in self.ges.values():
            #if ge.object_id in window.AllKeysDict:
            ge.init_window(window)
    def pull_all(self, values):
        for ge in self.ges.values():
            # print('pulling values for', ge.object_id)
            ge.pull(values)
    def push_all(self, window):
        for ge in self.ges.values():
            ge.push(window)
    def handle_event(self, context):
        for ge in self.ges.values():
            ge.handle_event(context)
    
    # generate a unique key that won't need to be used manually
    def gem_key(self, unique_string):
        if unique_string in self.gem_keys:
            return self.gem_keys[unique_string]
        us_clip = unique_string[:30].replace(' ', '').replace('\n', '') # for debug if needed, is unique event without this
        key = 'GEM_KEY_' + str(self.gem_id) + '_' + str(GuiElementManager.num_gem_keys) + '_' + us_clip
        GuiElementManager.num_gem_keys += 1
        self.gem_keys[unique_string] = key
        return key

# GuiElement

class GuiElement(ABC):
    class layout_types:
        SGE = 'sge'
        ROW = 'row'
        LAYOUT = 'layout'
    def __init__(self, object_id, layout_type:str) -> None:
        if not layout_type in ['sge', 'row', 'layout']:
            raise ValueError('Bad layout_type')
        self.layout_type = layout_type
        self.object_id = object_id
        self.keys = {}
        self.define_keys()
        self.gem = GuiElementManager()
        self.requestable_events = {}
        self.sg_kwargs = {}
        self.sg_kwargs_all_dict = {}
        self.sg_kwargs_functions = {}
        self.disabled = False
        self.has_validity = False
        self.prev_click_time = 0
        self.prev_click_id = None
        self.em = EventManager()
        self.events_defined = False
        self.right_click_menus = MenuDict()
        self.define_menus()
        
    
    ## Abstracts

    # Layout

    # These are virtual, but one must be implemented
    # postfix partials/alternatives (e.g. get_sge_basename(...), get_sge_extension(...))
    def _get_sge(self):
        raise NotImplemented
    @initafter
    def get_sge(self): # One sg element
        if self.layout_type in [GuiElement.layout_types.LAYOUT, GuiElement.layout_types.ROW]:
            raise RuntimeError('GuiElement of type ' + self.layout_type + ' does not support get_sge()')
        return self._get_sge()
    
    def _get_row(self):
        raise NotImplementedError
    @initafter
    def get_row(self): # A list of sg elements
        if self.layout_type == GuiElement.layout_types.LAYOUT:
            raise RuntimeError('GuiElement of type ' + self.layout_type + ' does not support get_row()')
        elif self.layout_type == GuiElement.layout_types.SGE:
            return [self.get_sge()]
        return self._get_row()
    
    def _get_layout(self):
        raise NotImplementedError
    @initafter
    def get_layout(self): # A list of lists of sg elements
        if self.layout_type == GuiElement.layout_types.SGE:
            return [[self.get_sge()]]
        elif self.layout_type == GuiElement.layout_types.ROW:
            return [self.get_row()]
        return self._get_layout()

    # Data
    
    @abstractmethod
    def _init(self):
        pass
    def init(self):
        self._init()
    
    @abstractmethod
    def _save(self, data):
        pass
    def save(self, data):
        self.gem.save_all(data)
        if self.disabled:
            data[self.object_id] = None
        elif not self.is_valid():
            data[self.object_id] = None
        else:
            self._save(data)
    
    @abstractmethod
    def _load(self, data):
        pass
    def load(self, data):
        self.gem.load_all(data)
        if self.object_id in data.keys():
            self._load(data)
    
    @abstractmethod
    def _pull(self, values):
        pass
    def pull(self, values):
        if self.disabled:
            return
        self._pull(values)
    
    @abstractmethod
    def _push(self, window):
        pass
    def push(self, window):
        self._push(window)
    
    @abstractmethod
    def _init_window(self, window):
        pass
    def init_window(self, window):
        self.push(window)
        self._init_window(window)

    # Keys and Events

    @abstractmethod
    def define_keys(self):
        pass

    def define_menus(self):
        pass

    @abstractmethod
    def define_events(self):
        pass

    ## Virtuals

    def handle_event(self, context):
        self.em.handle_event(context)
        self.gem.handle_event(context)

    def _is_valid(self):
        pass
    def is_valid(self):
        if not self.has_validity:
            return True
        return self._is_valid()
    
    def _push_validity(self, window):
        pass
    def push_validity(self, window):
        if not self.has_validity:
            return
        self._push_validity(window)
    
    ## Other

    def prepare_event_manager(self):
        em = EventManager()
        em.handle_event_function(self.handle_event)
        return em

    def set_sg_kwargs(self, key_prefix, overwrite_kwargs=True, **kwargs):
        if not key_prefix in self.sg_kwargs:
            self.sg_kwargs[key_prefix] = {}
            self.sg_kwargs[key_prefix].update(self.sg_kwargs_all_dict)
        sg_kwargs = self.sg_kwargs[key_prefix]
        for k, v in kwargs.items():
            if overwrite_kwargs or not k in sg_kwargs:
                sg_kwargs[k] = v
        return self
    
    # Calling during init ensures dict in kwargs is set before get_layout() is called,
    #     as well as not overwriting values set at time of object instantiation
    def init_sg_kwargs(self, key_prefix, **kwargs):
        self.set_sg_kwargs(key_prefix, overwrite_kwargs=False, **kwargs)
        return self
    
    def sg_kwargs_all(self, **kwargs):
        self.sg_kwargs_all_dict.update(kwargs)
        for key_prefix in self.sg_kwargs.keys():
            self.set_sg_kwargs(key_prefix, **kwargs)
        return self
    

    
    def init_data(self, value):
        """Like calling load(data) while data[object_id] == value"""
        self.load({self.object_id: value})
        return self
    


    @classmethod
    def make_key(cls, key_prefix, key_root):
        return str(key_prefix) + str(key_root)
    
    
    def event(self, key):
        """Decorator\n
        \n
        @self.event('event_key')\n
        def event_func(context):\n
            ...\n
        \n
        Also, stackable\n
        @self.event('event_key1')\n
        @self.event('event_key2')\n
        def event_func(context):\n
            ..."""
        return self.em.event(key)
    def events(self, keys):
        """Decorator, shorthand for multiple @self.event(...) decorators\n
        \n
        @self.events(['event_key1', 'event_key2'])\n
        def event_func(context):\n
            ..."""
    def append_event(self, prev_key, key):
        return self.em.append(prev_key, key)
    
    def key_rcm(self, rcm_name, *args):
        menu = self.right_click_menus[rcm_name]
        for arg in args:
            menu = menu[arg]
        return menu.get_event_key()

    def add_key(self, key_prefix):
        self.keys[key_prefix] = GuiElement.make_key(key_prefix, self.object_id)
    def add_keys(self, key_prefixes):
        for kp in key_prefixes:
            self.add_key(kp)



    def sge(self, ge):
        self.gem.add_ge(ge)
        return self.gem[ge.object_id].get_sge()
    def row(self, ge):
        self.gem.add_ge(ge)
        return self.gem[ge.object_id].get_row()
    def layout(self, ge):
        self.gem.add_ge(ge)
        return self.gem[ge.object_id].get_layout()
    
    def ges(self, key_prefix):
        return self.gem[self.keys[key_prefix]]

    
    
    def disable(self, window, value=True):
        self.disabled = value
        self.push(window)
    
    def check_double_click(self, click_id=None):
        """Register a click, then return if it is a double click.\n
        Don't forget to set the sg kwarg bind_return_key if needed.\n
        click_id ensure the previous click came from the same place."""
        click_time = time.time()
        if (click_time - self.prev_click_time) < nss_g.double_click_secs:
            is_double_click = True
        else:
            is_double_click = False
        self.prev_click_time = click_time
        prev_click_id = self.prev_click_id
        self.prev_click_id = click_id
        if not is_double_click:
            return None
        if click_id != None:
            return (click_id == prev_click_id)
        return True
    register_click = check_double_click
    """Alias for check_double_click(), makes it more clear that ignoring the is_double_click rv is intentional"""

    def wrap_event_function(self, func, pull=False, push=False):
        def f(context):
            if pull:
                self.pull(context.values)
            func(context)
            if push:
                self.push(context.window)
        return f


# This is for reference, as well as to copy/paste into a new GuiElement subclass
class GuiElementExample(GuiElement):
    def __init__(self, object_id, label, value) -> None:
        super().__init__(object_id, GuiElement.layout_types.ROW)
        self.label = label
        self.value = value

    ### GuiElement

    # Layout

    def _get_layout(self):
        layout = [[]]
        return layout
    def _get_row(self):
        row = []
        if self.label:
            row.append(sg.Text(self.label, key=self.keys['Label'], **self.sg_kwargs['Label']))
        row.append(sg.Input(self.value, key=self.keys['ExampleIn'], **self.sg_kwargs['ExampleIn']))
        return row
    def _get_sge(self):
        sge = None
        return sge
    
    # Data

    def _init(self):
        self.init_sg_kwargs('Label')
        self.init_sg_kwargs('ExampleIn')
    def _save(self, data):
        value = self.value
        data[self.object_id] = value
    def _load(self, data):
        super().load(data)
        value = data[self.object_id]
        if value == None:
            value = 'DEFAULT'
        self.value = value
    def _pull(self, values):
        pass
    def _push(self, window):
        sge_example_in = window[self.keys['ExampleIn']]
        sge_example_in.update(disabled=self.disabled)
        if self.disabled:
            sge_example_in.update('')
        else:
            sge_example_in.update(self.value)
    def _init_window(self, window):
        self.push(window)
    
    # Keys and Events
    
    def define_keys(self):
        super().define_keys()
        self.add_key('Label')
        self.add_key('ExampleIn')
    
    def define_events(self):
        super().define_events()

    # Others

    def sg_kwargs_label(self, **kwargs):
        self.set_sg_kwargs('Label', **kwargs)
        return self
    def sg_kwargs_example_in(self, **kwargs):
        self.set_sg_kwargs('ExampleIn', **kwargs)
        return self

    ### GuiElementExample

    def set_value(self, value):
        if value == None:
            self.reset()
            return False
        self.value = value
        return True
    def reset(self):
        self.set_value('DEFAULT')
    def update(self, window, value):
        self.set_value(value)
        self.push(window)
