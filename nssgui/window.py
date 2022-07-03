from abc import ABC, abstractmethod

import PySimpleGUI as sg
from nssgui.style import colors
from nssgui.event_manager import NULL_EVENT, EventManager, EventLoop, WRC
from nssgui.ge.gui_element import *
from nssgui.ge.output import StatusBar
from nssgui import sg as nss_sg

__all__ = [
    'WindowContext',
    'AbstractWindow',
    'AbstractBlockingWindow',
    'AbstractAsyncWindow',
    'ProgressWindow',
    'LoadingWindow'
]

class WindowContext:
    def __init__(self, window=None, event=NULL_EVENT, values=None, data=None):
        self.window:sg.Window = window
        self.event:str = event
        self.values:dict = values if values != None else {}
        self.data:dict = data if data != None else {}
        self.window_stack:list[sg.Window] = []
        self.async_windows:dict[str,AbstractAsyncWindow] = {}
        self.asyncs = self.async_windows


    
    def push(self, window:sg.Window):
        self.window_stack.append(self.window)
        self.window = window
        nss_sg.center_window(window)
    def pop(self):
        w = self.window
        self.window = self.window_stack.pop()
        self.event = NULL_EVENT
        self.values = {}
        return w
    
    def add_async(self, asyncwindow):
        self.async_windows[asyncwindow.window_id] = asyncwindow
        if asyncwindow.window != None:
            nss_sg.center_window(asyncwindow.window)
    def remove_async(self, window_id):
        del self.async_windows[window_id]

    def focus(self):
        if self.window == None:
            return
        self.window.bring_to_front()
        self.window.force_focus()
        for w in self.async_windows.values():
            w.window.bring_to_front()
            w.window.force_focus()

    def disable(self):
        if self.window == None:
            return
        self.window.disable()
        self.window.set_alpha(0.9)#(0.92)
    def enable(self):
        if self.window == None:
            return
        self.window.enable()
        self.window.set_alpha(1.0)
    def hide(self):
        if self.window == None:
            return
        self.window.hide()
    def unhide(self):
        if self.window == None:
            return
        self.window.un_hide()

class AbstractWindow(ABC, EventManager):
    def __init__(self, title, data=None) -> None:
        super().__init__(debug_id='AbstractWindow:{}'.format(title))
        self.title = title
        self.data = data.copy() if data != None else {}
        self.gem = GuiElementManager()

        # Before layout definition
        self.menubar = None
        self.right_click_menus = {}
        self.define_menus()


        # Layout definition
        self.get_layout() # trash a layout to create the GuiElements defined in it

        # After layout definition
        self.define_events()

        self.window:sg.Window = None
        self.status_bar_key = None
    
    # Layout
    
    def define_menus(self):
        pass
    @abstractmethod
    def get_layout(self):
        pass

    # Events

    @abstractmethod
    def define_events(self):
        """AbstractWindow:define_events()
            Adds only: gem handle_event function"""
        self.event_handler(self.gem.handle_event)

    # Data

    def save(self, data):
        self.gem.save_all(data)

    def load(self, data):
        self.gem.load_all(data)

    def pull(self, values):
        self.gem.pull_all(values)

    def push(self, window):
        self.gem.push_all(window)

    def init_window(self, window):
        self.gem.init_window_all(window)

    # Other

    @abstractmethod
    def open(self, context=None):
        self._close_loading_window(context)

    def get_data(self):
        return self.data
    
    def key_rcm(self, rcm_name, *args):
        menu = self.right_click_menus[rcm_name]
        for arg in args:
            menu = menu[arg]
        return menu.get_event_key()
    def key_menubar(self, *args):
        menu = self.menubar
        for arg in args:
            menu = menu[arg]
        return menu.get_event_key()
    
    @classmethod
    def open_loading_window(cls, context, title=''):
        """Open an async loading window that will automatically\n
        be closed when a Window of the caller's class is opened."""
        k = 'LoadingWindow' + cls.__name__
        LoadingWindow(k, title=title).open(context)
    @classmethod
    def _close_loading_window(cls, context):
        """Check for and close any loading windows opened for the class"""
        k = 'LoadingWindow' + cls.__name__
        if k in context.asyncs:
            context.asyncs[k].close(context)
    
    def status_bar(self, ge:StatusBar):
        """Links a ge element to the update_status_bar() function.
        Placing a [sg.Sizer(0, 10)] row above a status bar is suggested."""
        self.status_bar_key = ge.object_id
        return self.gem.row(ge)
    def update_status_bar(self, text):
        if self.status_bar_key == None:
            raise RuntimeError('StatusBar has not been specified.')
        self.gem[self.status_bar_key].update(self.window, text)
        self.window.refresh()

class AbstractBlockingWindow(AbstractWindow):
    """
    Make a subclass of this, implementing:\n
        - __init__()\n
        - get_layout()\n
        - define_events()\n
    Call open(), storing return value\n
    If bool(rv)==False, then window was closed with cancel/X/etc. Ignore data accordingly\n
    Access data via get_data()
    """
    class focus_types:
        HIDE_PREV = 'hide_prev'
        DISABLE_PREV = 'disable_prev'
    def __init__(self, title, data=None, focus_type='disable_prev') -> None:
        super().__init__(title=title, data=data)
        self.focus_type = focus_type
    
    def open(self, context=None):
        """Open a blocking window. Returns after closing."""
        context = context if context != None else WindowContext()
        layout = self.get_layout()

        if self.focus_type == self.focus_types.HIDE_PREV:
            context.hide()
        elif self.focus_type == self.focus_types.DISABLE_PREV:
            context.disable()

        self.load(self.data)
        super().open(context)
        self.window = sg.Window(self.title, layout, finalize=True)
        context.push(self.window)
        context.focus()
        self.init_window(self.window)
        nss_sg.center_window(self.window)
        rv = WRC(EventLoop(self).run(context))
        rv.closed_window()

        if rv.check_success():
            if context.values:
                self.pull(context.values)
            self.save(self.data)
        context.pop()

        if self.focus_type == self.focus_types.HIDE_PREV:
            context.unhide()
        elif self.focus_type == self.focus_types.DISABLE_PREV:
            context.enable()
        
        context.focus()
        return rv

class AbstractAsyncWindow(AbstractWindow):
    class focus_types:
        STEAL = 'steal'
    def __init__(self, window_id, title, data=None, focus_type='steal', window_kwargs=None) -> None:
        self.window_id = window_id
        self.keys = {}
        self.define_keys()
        self.focus_type = focus_type
        self.window_kwargs = window_kwargs if window_kwargs != None else {}
        super().__init__(title=title, data=data)
    def add_key(self, key_prefix):
        self.keys[key_prefix] = key_prefix + self.window_id
    def open(self, context:WindowContext):
        super().open(context)
        if self.window:
            return
        layout = self.get_layout()
        kwargs = self.window_kwargs
        kwargs['title'] = self.title
        kwargs['layout'] = layout
        kwargs['finalize'] = True
        self.window = sg.Window(**kwargs)
        context.add_async(self)
        self.window.refresh()
    def close(self, context:WindowContext):
        if not self.window:
            return
        self.window.close()
        self.window = None
        context.remove_async(self.window_id)
    def update(self):
        event, values = self.window.read(10)
    @abstractmethod
    def get_layout(self):
        pass
    @abstractmethod
    def define_keys(self):
        pass

    def key(self, key):
        return self.keys[key]

class ProgressWindow(AbstractAsyncWindow):
    def __init__(self, window_id, title='Progress', header='Progress', no_meter=False, no_text=False) -> None:
        self.header = header
        self.is_progress_visible = (not no_meter)
        self.is_out_visible = (not no_text)
        super().__init__(window_id, title)
    
    ### NBWindow

    def get_layout(self):
        layout = [
            [sg.Text(self.header, text_color=colors.header)]
        ]
        layout.append([sg.Multiline('', key=self.keys['Out'], size=(50, 5), expand_x=True, autoscroll=True, no_scrollbar=True, visible=self.is_out_visible)])
        layout.append([sg.Progress(1000, orientation='h', size=(1, 15), expand_x=True, key=self.keys['Progress'])])
        return layout

    def define_keys(self):
        self.add_key('Out')
        self.add_key('Progress')
        
    def define_events(self):
        super().define_events()
    
    ### ProgressWindow

    def __getitem__(self, key_prefix):
        return self.keys[key_prefix]
    def update_progress(self, progress:float):
        self.window[self.keys['Progress']].UpdateBar(progress * 1000)
    def set_text(self, text):
        self.window[self.keys['Out']](text)
    def append_text(self, text):
        self.window[self.keys['Out']].print(text)
    def progress_function(self, append_text=None, progress=None):
        if append_text:
            self.append_text(append_text)
        if progress:
            self.update_progress(progress)
        self.update()
    def get_progress_function(self):
        def func(append_text:str|None=None, progress:float|None=None):
            self.progress_function(append_text, progress)
        return func

class LoadingWindow(AbstractAsyncWindow):
    def __init__(self, window_id, text='Loading...', title='', data=None, focus_type='steal') -> None:
        self.text = text
        super().__init__(window_id, title, data, focus_type, window_kwargs={
            'no_titlebar': True
        })
    def get_layout(self):
        layout = []
        layout.append([sg.Column(p=(60, 30), layout=[[sg.Text(self.text, font='Helvetica 24')]])])
        if self.title:
            layout = [[sg.Frame(title='   ' + self.title + '   ', layout=layout, title_location=sg.TITLE_LOCATION_TOP, p=((0, 0), (0, 7)))]]
        return layout
    def define_keys(self):
        pass
    def define_events(self):
        super().define_events()
