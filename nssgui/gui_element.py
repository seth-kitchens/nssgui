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
    'GuiElementLayoutManager'
]


def check_if_instances(obj, types:list):
    for t in types:
        if not isinstance(obj, t):
            raise TypeError('Obj ' + str(obj) + ' is not an instance of ' + str(t))

def check_if_subclasses(name, types:list):
    for t in types:
        if not issubclass(name, t):
            raise TypeError('Obj ' + str(name) + ' is not a subclass of ' + str(t))


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
            self.ges[id] = ge
    
    def get_ge(self, object_id) -> GuiElement | None:
        if object_id not in self.ges.keys():
            return None
        return self.ges[object_id]
    
    def ges_save(self, data):
        for ge in self.ges.values():
            ge.save(data)

    def ges_load(self, data):
        for ge in self.ges.values():
            ge.load(data)

    def ges_init_window_finalized(self, window):
        for ge in self.ges.values():
            ge.init_window_finalized(window)

    def ges_pull(self, values):
        for ge in self.ges.values():
            ge.pull(values)

    def ges_push(self, window):
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


class GuiElement(EventManager, GuiElementLayoutManager):

    class iLength(ABC):
        """GuiElement data can be measured with len()"""

        @abstractmethod
        def __len__(self):
            pass

    class iStringable(ABC):
        """GuiElement data can be represented by a string"""

        @abstractmethod
        def to_string(self):
            """data -> string"""
            pass

        @abstractmethod
        def load_string(self, s):
            """string -> data of existing class"""
            pass

    class iEdittable(ABC):
        """GuiElement data can be editted with an 'Edit' button"""

        @abstractmethod
        def get_edit_layout(self):
            """Return a layout that allows for editing, to be nested in a window"""
            pass
    
    class iLayout(ABC):
        """GuiElement's primary layout is "layout" of the form: list[list[sge]]"""

        def get_layout_type(self):
            return GuiElement.layout_types.LAYOUT
        
        @abstractmethod
        def _get_layout(self):
            pass
    
    class iRow(ABC):
        """GuiElement's primary layout is "row" of the form: list[sge]"""

        def get_layout_type(self):
            return GuiElement.layout_types.ROW
        
        @abstractmethod
        def _get_row(self):
            pass
    
        def _get_layout(self):
            return [self._get_row()]
    
    class iSge(ABC):
        """GuiElement's primary layout is "sge" of the form: sge"""

        def get_layout_type(self):
            return GuiElement.layout_types.ROW
        
        @abstractmethod
        def _get_sge(self):
            pass

        def _get_row(self):
            return [self._get_sge()]
        
        def _get_layout(self):
            return [[self._get_sge()]]

    class layout_types:
        SGE = 'sge'
        ROW = 'row'
        LAYOUT = 'layout'

    def __init__(self, object_id) -> None:
        """
        ## GuiElement

        ### Subclassing

        - Subclass iSge, iRow or iLayout before GuiElement.
        Example: `class mygesubclass(GuiElement.iRow, GuiElement)`
        - Define layout in the respective method:
            - `_get_sge()` OR
            - `_get_row()` OR
            - `_get_layout()`
        - Override definition methods needed
            - `define_keys()`
            - `define_events()`
            - `define_menus()`
        
        ### Initialization

        GuiElements are made to be defined within a layout definition, where instantiation is
        followed by a get (sge|row|layout) function, which may be called again later. Some of
        initialization is delayed until a layout function is first called.

        - External: GuiElement subclass's constructor
            - `__init__()`
            - `define_keys()`
            - internal GuiElementManager constructed
            - `define_menus()`
        - External: Any initializing functions, e.g. `load_value` (note that many are chainable)
        - External: `get_sge()` OR `get_row()` OR `get_layout()`
            - `_get_sge()` OR `_get_row()` OR `_get_layout()`
            - `define_events()`
        - External: `init_window_finalized()` after sg.Window is finalized
            - `_init_window_finalized()`
        
        ### SG Element Kwargs

        GuiElements represent one or more SG Elements. To easily provide a way to pass kwargs to
        sg elements, you may use `sg_kwargs` related functions.
        - Make a `sg_kwargs_<key_name>(self, **kwargs)` function, for each sg element you want to
        provide kwarg passing for
            - Use `_set_sg_kwargs('key_name')` to set the values
        - In the layout function (_get_layout(), etc):
            - Use `default_sg_kwargs()` to define defaults if needed
            - Add `**self._sg_kwargs['key_name']` to the elements' constructors
        
        Making the functions give clear indication that sg_kwargs are supported for the element,
        rather just adding parameter and expecting use of `_set_sg_kwargs()`.

        """
        super().__init__(debug_id='GE:' + object_id)
        if not (issubclass(self.__class__, GuiElement.iSge)
            or  issubclass(self.__class__, GuiElement.iRow)
            or  issubclass(self.__class__, GuiElement.iLayout)):
            raise TypeError('A GuiElement class must inherit one of: iSge, iRow, iLayout')
        self.object_id = object_id
        self.keys = {}
        self.define_keys()
        self.gem = GuiElementManager()
        self.requestable_events = {}
        self._sg_kwargs:dict[str, dict[str, str]] = {}
        self.disabled = False
        self.has_validity = False
        self.prev_click_time = 0
        self.prev_click_id = None
        self.events_defined = False
        self.init_window_finalized_finished = False
        self.right_click_menus = MenuDict()
        self.define_menus()
        
    ## Abstract / Virtual

    # Layout
    
    @abstractmethod
    def get_layout_type(self):
        """
        Do not override this! This should be overridden by one of:
        `GuiElement.iSge` `GuiElement.iRow` `GuiElement.iLayout`

        Then, that interface's respective `_get` method must be defined.
        """
        pass

    # Keys, Events, Menus

    def define_keys(self):
        """
        This is where all keys are defined. These seperate sg elements
        from one another, and allow for the use of key names local to each GuiElement.
        Define each key with `add_key()` and then access them elsewhere with the `keys` dict. 
        """
        pass

    def define_events(self):
        """
        Define events here. This function is called AFTER the layout function is called
        (see `initafter()`).
        """
        pass

    def define_menus(self):
        """
        Define menus here. This includes menu bars and right click menus
        """
        pass

    # Init
    
    def _init_window_finalized(self, window):
        pass

    # Data
    
    def _save(self, data):
        pass
    
    def _load(self, data):
        pass
    
    def _pull(self, values):
        pass
    
    def _push(self, window):
        pass

    ##

    # Init

    def init_window_finalized(self, window):
        """
        Do not override this! Most likely, the inner function `_init_window_finalized())`
        is what you want to override.
        """
        if self.init_window_finalized_finished:
            return self
        self.push(window)
        self._init_window_finalized(window)
        self.init_window_finalized_finished = True
        return self

    # Data

    def save(self, data):
        """
        Do not override this! Most likely, the inner function `_save()`
        is what you want to override.
        """
        self.gem.ges_save(data)
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
        self.gem.ges_load(data)
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
    
    # Layout

    def get_sge(self) -> sg.Element: # One sg element
        """
        Do not override this! Most likely, the inner function `_get_sge()`
        is what you want to override.
        """
        rv = self._get_sge()
        if not self.events_defined:
            self.define_events()
            self.events_defined = True
        return rv

    def get_row(self) -> list: # A list of sg elements
        """
        Do not override this! Most likely, the inner function `_get_row()`
        is what you want to override.
        """
        rv = self._get_row()
        if not self.events_defined:
            self.define_events()
            self.events_defined = True
        return rv

    def get_layout(self) -> list[list]: # A list of lists of sg elements
        """
        Do not override this! Most likely, the inner function `_get_layout()`
        is what you want to override.
        """
        rv = self._get_layout()
        if not self.events_defined:
            self.define_events()
            self.events_defined = True
        return rv
    
    #

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
    
    # sg kwargs

    def _set_sg_kwargs(self, key_name, overwrite_kwargs=True, **kwargs):
        if not key_name in self._sg_kwargs:
            self._sg_kwargs[key_name] = {}
        sg_kwargs = self._sg_kwargs[key_name]
        for k, v in kwargs.items():
            if overwrite_kwargs or not k in sg_kwargs:
                sg_kwargs[k] = v
        return self
    
    def sg_kwargs(self, key_name):
        if key_name in self._sg_kwargs:
            return self._sg_kwargs[key_name]
        return {}
    
    def default_sg_kwargs(self, key_name, **kwargs):
        """Call before layout to set default for passed sg kwargs"""
        return self._set_sg_kwargs(key_name, overwrite_kwargs=False, **kwargs)
    
    #
    
    def load_value(self, value):
        """Load a value as if it was stored data for this ge"""
        return self.load({self.object_id: value})

    @classmethod
    def make_key(cls, key_name, key_root):
        return str(key_name) + str(key_root)
    
    def key_rcm(self, rcm_name, *args):
        """Get key for a right click menu item"""
        menu = self.right_click_menus[rcm_name]
        for arg in args:
            menu = menu[arg]
        return menu.get_event_key()

    def add_key(self, key_name):
        self.keys[key_name] = GuiElement.make_key(key_name, self.object_id)
    
    def get_key(self, key_name):
        return self.keys[key_name]

    def add_ge(self, ge):
        self.gem.add_ge(ge)
    
    def get_ge(self, object_id) -> GuiElement | None:
        return self.gem.get_ge(object_id)
    
    def ges(self, key_name):
        return self.gem[self.keys[key_name]]    
    
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
