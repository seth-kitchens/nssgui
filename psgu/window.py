from __future__ import annotations

from abc import ABC, abstractmethod

import PySimpleGUI as sg

from psgu.style import colors
from psgu.event_handling import NULL_EVENT, EventManager, WRC
from psgu.event_loop import EventLoop
from psgu.gui_element import *
from psgu import sg as psgu_sg
from psgu.window_context import WindowContext


__all__ = [
    'WindowContext',
    'AbstractWindow',
    'AbstractBlockingWindow',
    'AbstractAsyncWindow',
    'ProgressWindow',
    'LoadingWindow'
]


class AbstractWindow(EventManager, GuiElementLayoutManager):

    COLOR_STATUS = '#FFFFFF'
    COLOR_STATUS_FADED = '#CCCCCC'

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
        self.timed_events = []
    
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
        self.gem.for_ges_save(data)

    def load(self, data):
        self.gem.for_ges_load(data)

    def pull(self, values):
        self.gem.for_ges_pull(values)

    def push(self, window):
        self.gem.for_ges_push(window)

    def init_window_finalized(self, window:sg.Window):
        self.gem.for_ges_init_window_finalized(window)

    # Other

    @abstractmethod
    def open(self, window_context=None):
        self._close_loading_window(window_context)

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
    def open_loading_window(cls, window_context, title=''):
        """Open an async loading window that will automatically\n
        be closed when a Window of the caller's class is opened."""
        k = 'LoadingWindow' + cls.__name__
        LoadingWindow(k, title=title).open(window_context)

    @classmethod
    def _close_loading_window(cls, window_context):
        """Check for and close any loading windows opened for the class"""
        k = 'LoadingWindow' + cls.__name__
        if k in window_context.async_windows:
            window_context.async_windows[k].close(window_context)
    
    def status_bar(self, ge):
        """Links a ge element to the update_status() function.
        Placing a [sg.Sizer(0, 10)] row above a status bar is suggested."""
        self.status_bar_key = ge.object_id
        return self.gem.row(ge)

    def update_status(
            self, text:str=None, secs:float|None=None,
            replace_text:str='', text_color=COLOR_STATUS,
            replace_text_color=COLOR_STATUS):
        """
        `text`: If not `None`, updates status bar with this immediately
        `secs`: If not `None`, updates status bar with 
            `replace_text` after `secs` seconds
        `replace_text`: Text to be displayed after `secs` seconds
        """
        if self.status_bar_key == None:
            raise RuntimeError('StatusBar has not been specified.')
        status_bar = self.gem[self.status_bar_key]
        if text != None:
            status_bar.update_status(self.window, text, text_color=text_color)
        self.window.refresh()
        if secs != None:
            def func(event_context):
                status_bar.update_status(
                    event_context.window, replace_text,
                    text_color=replace_text_color)
            self.event_after(func, secs)
    
    def add_ge(self, ge):
        self.gem.add_ge(ge)
    
    def get_ge(self, object_id) -> GuiElement | None:
        return self.gem.get_ge(object_id)
    
    def get_window(self):
        return self.window

class AbstractBlockingWindow(AbstractWindow, WindowContext.iBlockingWindow):
    """
    Make a subclass of this, implementing:\n
        - __init__()\n
        - get_layout()\n
        - define_events()\n
    Call open(), storing return value\n
    If bool(rv)==False, then window was closed with cancel/X/etc.
    Ignore data accordingly\n
    Access data via get_data()
    """

    class focus_types:
        HIDE_PREV = 'hide_prev'
        DISABLE_PREV = 'disable_prev'

    def __init__(self, title, data=None, focus_type='disable_prev') -> None:
        super().__init__(title=title, data=data)
        self.focus_type = focus_type
    
    def open(self, window_context:WindowContext|None=None):
        """Open a blocking window. Returns after closing."""
        window_context = WindowContext.from_any(window_context)
        layout = self.get_layout()
        if self.focus_type == self.focus_types.HIDE_PREV:
            window_context.hide()
        elif self.focus_type == self.focus_types.DISABLE_PREV:
            window_context.disable()
        self.load(self.data)
        super().open(window_context)
        self.window = sg.Window(self.title, layout, finalize=True)
        window_context.push(self.window)
        window_context.focus()
        self.init_window_finalized(self.window)
        psgu_sg.center_window(self.window)
        event_loop = EventLoop(self)
        rv = event_loop.run(window_context)
        rv.closed_window()

        # save if successful
        if rv.check_success():
            if event_loop.final_event_context is not None:
                self.pull(event_loop.final_event_context.values)
            self.save(self.data)
        window_context.pop()

        if self.focus_type == self.focus_types.HIDE_PREV:
            window_context.unhide()
        elif self.focus_type == self.focus_types.DISABLE_PREV:
            window_context.enable()
        window_context.focus()
        return rv

class AbstractAsyncWindow(AbstractWindow, WindowContext.iAsyncWindow):

    class focus_types:
        STEAL = 'steal'
    
    def __init__(self, window_id, title, data=None,
            focus_type='steal', window_kwargs=None) -> None:
        self.window_id = window_id
        self.keys = {}
        self.define_keys()
        self.focus_type = focus_type
        self.window_kwargs = window_kwargs if window_kwargs != None else {}
        super().__init__(title=title, data=data)

    def add_key(self, key_name):
        self.keys[key_name] = key_name + self.window_id
    
    def open(self, window_context:WindowContext):
        super().open(window_context)
        if self.window:
            return
        layout = self.get_layout()
        kwargs = self.window_kwargs
        kwargs['title'] = self.title
        kwargs['layout'] = layout
        kwargs['finalize'] = True
        self.window = sg.Window(**kwargs)
        window_context.add_async(self)
        self.window.refresh()
    
    def close(self, window_context:WindowContext):
        if not self.window:
            return
        self.window.close()
        self.window = None
        window_context.remove_async(self.window_id)
    
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
    
    def get_window_id(self):
        return self.window_id

class ProgressWindow(AbstractAsyncWindow):
    
    def __init__(
            self, window_id, title='Progress', header='Progress', 
            no_meter=False, no_text=False) -> None:
        self.header = header
        self.is_progress_visible = (not no_meter)
        self.is_out_visible = (not no_text)
        super().__init__(window_id, title)
    
    ### NBWindow

    def get_layout(self):
        layout = [
            [sg.Text(self.header, text_color=colors.header)]
        ]
        layout.append([
            sg.Multiline('', key=self.keys['Out'], size=(50, 5),
                expand_x=True, autoscroll=True, no_scrollbar=True,
                visible=self.is_out_visible)
        ])
        layout.append([
            sg.Progress(1000, orientation='h', size=(1, 15),
                expand_x=True, key=self.keys['Progress'])
        ])
        return layout

    def define_keys(self):
        self.add_key('Out')
        self.add_key('Progress')
        
    def define_events(self):
        super().define_events()
    
    ### ProgressWindow

    def __getitem__(self, key_name):
        return self.keys[key_name]
    
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
    
    def __init__(self,
            window_id,
            text='Loading...',
            title='',
            data=None,
            focus_type='steal') -> None:
        self.text = text
        super().__init__(window_id, title, data, focus_type, window_kwargs={
            'no_titlebar': True
        })
    
    def get_layout(self):
        layout = []
        layout.append([
            sg.Column(
                p=(60, 30),
                layout=[[sg.Text(self.text, font='Helvetica 24')]])
        ])
        if self.title:
            layout = [
                [
                    sg.Frame(
                        title='   {}   '.format(self.title),
                        layout=layout, 
                        title_location=sg.TITLE_LOCATION_TOP,
                        p=((0, 0), (0, 7)))
                ]
            ]
        return layout
    
    def define_keys(self):
        pass
    
    def define_events(self):
        super().define_events()
