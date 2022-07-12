from __future__ import annotations

from abc import ABC, abstractmethod
import time
from functools import wraps

import PySimpleGUI as sg

from nssgui import g as nss_g
from nssgui.event_handling import WRC, EventManager
from nssgui.sg.utils import MenuDict


__all__ = [
    'check_if_instances',
    'check_if_subclasses',
    'GuiElement',
    'GuiElementManager',
    'GuiElementLayoutManager',
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

class GuiElementLayoutManager(ABC):

    @abstractmethod
    def add_ge(self, ge:GuiElement):
        pass

    @abstractmethod
    def get_ge(self, object_id:str) -> GuiElement | None:
        pass

    def sge(self, ge:GuiElement) -> sg.Element:
        g = self.get_ge(ge.object_id)
        if g is not None:
            return g.get_sge()
        self.add_ge(ge)
        return self.get_ge(ge.object_id).get_sge()

    def row(self, ge:GuiElement) -> list:
        g = self.get_ge(ge.object_id)
        if g is not None:
            return g.get_row()
        self.add_ge(ge)
        return self.get_ge(ge.object_id).get_row()

    def layout(self, ge:GuiElement) -> list[list]:
        g = self.get_ge(ge.object_id)
        if g is not None:
            return g.get_layout()
        self.add_ge(ge)
        return self.get_ge(ge.object_id).get_layout()


class GuiElementManager(GuiElementLayoutManager):

    num_gems = 0
    num_gem_keys = 0

    def __init__(self):
        self.gem_id = GuiElementManager.num_gems
        GuiElementManager.num_gems += 1
        self.ges:dict[str,GuiElement] = {}
        self.gem_keys = {}

        self.status_bar_key = None

    def __getitem__(self, key):
        return self.ges[key]

    def __setitem__(self, key, value):
        self.ges[key] = value

    def add_ge(self, ge):
        id = ge.object_id
        if not id in self.ges.keys():
            ge.init()
            self.ges[id] = ge
    
    def get_ge(self, object_id) -> GuiElement | None:
        if object_id not in self.ges.keys():
            return None
        return self.ges[object_id]
    
    def save_ges(self, data):
        for ge in self.ges.values():
            ge.save(data)

    def load_ges(self, data):
        for ge in self.ges.values():
            ge.load(data)

    def init_window_ges(self, window):
        for ge in self.ges.values():
            ge.init_window(window)

    def pull_ges(self, values):
        for ge in self.ges.values():
            ge.pull(values)

    def push_ges(self, window):
        for ge in self.ges.values():
            ge.push(window)

    def handle_event(self, context):
        for ge in self.ges.values():
            rv = WRC(ge.handle_event(context))
            if rv.check_close():
                return rv
        return WRC.none()
    
    # generate a unique key that won't need to be used manually
    def gem_key(self, unique_string):
        if unique_string in self.gem_keys:
            return self.gem_keys[unique_string]
        us_clip = unique_string[:30].replace(' ', '').replace('\n', '') # for debug if needed, is unique event without this
        key = 'GEM_KEY_{}_{}_{}'.format(self.gem_id, GuiElementManager.num_gem_keys, us_clip)
        GuiElementManager.num_gem_keys += 1
        self.gem_keys[unique_string] = key
        return key

# GuiElement

class GuiElement(EventManager, GuiElementLayoutManager):

    class layout_types:
        SGE = 'sge'
        ROW = 'row'
        LAYOUT = 'layout'

    def __init__(self, object_id, layout_type:str) -> None:
        """
        
        """
        if not layout_type in ['sge', 'row', 'layout']:
            raise ValueError('Bad layout_type')
        super().__init__(debug_id='GE:' + object_id)
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
        self.events_defined = False
        self.right_click_menus = MenuDict()
        self.define_menus()
        
    
    ## Abstract / Virtual

    # Layout

    # These are virtual, but one must be implemented
    # postfix partials/alternatives (e.g. get_sge_basename(...), get_sge_extension(...))
    def _get_sge(self) -> sg.Element:
        raise NotImplementedError
    
    def _get_row(self) -> list:
        raise NotImplementedError
    
    def _get_layout(self) -> list[list]:
        raise NotImplementedError

    # Data
    
    def _init(self):
        pass
    
    def _save(self, data):
        pass
    
    def _load(self, data):
        pass
    
    def _pull(self, values):
        pass
    
    def _push(self, window):
        pass
    
    def _init_window(self, window):
        pass

    # Keys, Events, Menus

    def define_keys(self):
        pass

    def define_events(self):
        pass

    def define_menus(self):
        pass

    ##

    def init(self):
        """
        Do not override this! Most likely, the inner function `_init()`
        is what you want to override.
        """
        self._init()
        return self

    def save(self, data):
        """
        Do not override this! Most likely, the inner function `_save()`
        is what you want to override.
        """
        self.gem.save_ges(data)
        if self.disabled:
            data[self.object_id] = None
        elif not self.is_valid():
            data[self.object_id] = None
        else:
            self._save(data)
        return self

    def load(self, data):
        """
        Do not override this! Most likely, the inner function `_load()`
        is what you want to override.
        """
        self.gem.load_ges(data)
        if self.object_id in data.keys():
            self._load(data)
        return self

    def pull(self, values):
        """
        Do not override this! Most likely, the inner function `_pull()`
        is what you want to override.
        """
        if self.disabled:
            return
        self._pull(values)
        return self

    def push(self, window):
        """
        Do not override this! Most likely, the inner function `_push()`
        is what you want to override.
        """
        self._push(window)

    def init_window(self, window):
        """
        Do not override this! Most likely, the inner function `_init_window())`
        is what you want to override.
        """
        self.push(window)
        self._init_window(window)

    @initafter
    def get_sge(self) -> sg.Element: # One sg element
        """
        Do not override this! Most likely, the inner function `_get_sge()`
        is what you want to override.
        """
        return self._get_sge()

    @initafter
    def get_row(self) -> list: # A list of sg elements
        """
        Do not override this! Most likely, the inner function `_get_row()`
        is what you want to override.
        """
        return self._get_row()

    @initafter
    def get_layout(self) -> list[list]: # A list of lists of sg elements
        """
        Do not override this! Most likely, the inner function `_get_layout()`
        is what you want to override.
        """
        return self._get_layout()
    
    ##

    def handle_event(self, context):
        rv = WRC(EventManager.handle_event(self, context))
        if rv.check_close():
            return rv
        rv |= WRC(self.gem.handle_event(context))
        return rv
    
    # Validity

    def is_valid(self):
        """
        For Overriding: function should probably start with a has_validity check:
        `if not self.has_validity: return True`
        """
        return True

    def push_validity(self, window):
        """
        For Overriding: function should probably start with a has_validity check:
        `if not self.has_validity: return`
        """
        pass
    
    ## sg kwargs

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
    
    ## Other
    
    def load_value(self, value):
        """Load a value as if it was stored data for this ge"""
        return self.load({self.object_id: value})

    @classmethod
    def make_key(cls, key_prefix, key_root):
        return str(key_prefix) + str(key_root)
    
    def key_rcm(self, rcm_name, *args):
        """Get key for a right click menu item"""
        menu = self.right_click_menus[rcm_name]
        for arg in args:
            menu = menu[arg]
        return menu.get_event_key()

    def add_key(self, key_prefix):
        self.keys[key_prefix] = GuiElement.make_key(key_prefix, self.object_id)

    def add_ge(self, ge):
        self.gem.add_ge(ge)
    
    def get_ge(self, object_id) -> GuiElement | None:
        return self.gem.get_ge(object_id)
    
    def ges(self, key_prefix):
        return self.gem[self.keys[key_prefix]]    
    
    def disable(self, window, value=True):
        self.disabled = value
        self.push(window)
    
    def check_double_click(self, click_id=None):
        """
        Register a click, then return if it is a double click.\n
        Don't forget to set the sg kwarg bind_return_key if needed.\n
        click_id ensures the previous click came from the same place.
        """
        click_time = time.time()
        if (click_time - self.prev_click_time) < nss_g.double_click_secs:
            is_double_click = True
        else:
            is_double_click = False
        self.prev_click_time = click_time
        prev_click_id = self.prev_click_id
        self.prev_click_id = click_id
        if not is_double_click:
            return False
        if click_id != None:
            return (click_id == prev_click_id)
        return True
    
    register_click = check_double_click
    """
    Alias for check_double_click() for more clearly showing that
    ignoring the is_double_click rv is intentional
    """
