from __future__ import annotations
import time
import inspect
import PySimpleGUI as sg

from psgu.data.ordered_dict import OrderedDict
from psgu.window_context import WindowContext

__all__ = [
    'EventContext',
    'EventManager',
    'EventLoop',
    'WindowReturnCode',
    'WRC',
    'NULL_EVENT'
]
NULL_EVENT = 'NULL_EVENT'


class EventContext:

    def __init__(self, event=NULL_EVENT, values=None, data=None, window_context=None):
        self.event = event
        if values is None:
            self.values = {}
        else:
            self.values = values
        if data is None:
            self.data = {}
        else:
            self.data = data
        if window_context is None:
            self.window_context = WindowContext()
        else:
            self.window_context = window_context
    
    @classmethod
    def from_event_context(cls, event_context:EventContext):
        if event_context.values is not None:
            values = event_context.values.copy()
        else:
            values = {}
        if event_context.data is not None:
            data = event_context.data.copy()
        else:
            data = {}
        return cls(
            event=event_context.event,
            values=values,
            data=data,
            window_context=event_context.window_context
        )

    def get_window(self):
        return self.window_context.window

    window = property(fget=get_window)


def get_func_location(func):
        file = inspect.getfile(func)
        try:
            _, lineno = inspect.getsourcelines(func)
        except OSError:
            lineno = -1
        return file, lineno


class Callback:

    def __init__(self):
        self.func:function = None
        self.dbginfo:list = []

    def dbg_location(self, file, lineno):
        location = 'Callback defined at "{}":{}'.format(file, lineno)
        self.dbginfo.append(location)
    
    def get_info(self):
        return 'Callback:\n    ' + '\n    '.join(self.dbginfo)

    @classmethod
    def event(cls, func):
        cb = cls()
        cb.func = func
        file, lineno = get_func_location(func)
        cb.dbg_location(file, lineno)
        return cb
    event_handler = event

    @classmethod
    def event_value(cls, value):
        cb = cls()
        cb.func = lambda event_context : value
        frame = inspect.currentframe()
        frameinfos = inspect.getouterframes(frame)
        frameinfo = frameinfos[3]
        del frame
        cb.dbg_location(frameinfo.filename, frameinfo.lineno)
        return cb


class WindowReturnCode:

    NONE = 0
    EXIT = 1 << 0
    CLOSE = 1 << 1
    SUCCESS = 1 << 2

    _MIN = 0
    _MAX = SUCCESS
    _SUM = _MAX * 2 - 1

    def __init__(self, value:WindowReturnCode|int|None=NONE, dbginfo=None):
        self.value = self.NONE
        self.dbginfo = dbginfo
        self |= value

    def __ior__(self, other:WindowReturnCode|int|None):
        if isinstance(other, self.__class__):
            self.check_valid_int(other.value)
            self.value |= other.value
        elif isinstance(other, int):
            self.check_valid_int(other)
            self.value |= other
        else:
            self.value = self.NONE
        self.propagate()
        return self

    def propagate(self):
        """
        Flip additional flags automatically based on current flags flipped.
        """
        if self.value & self.EXIT:
            self.value |= self.CLOSE
    
    @classmethod
    def none(cls):
        return WRC(WRC.NONE)
    
    @classmethod
    def exit(cls):
        return WRC(WRC.EXIT)

    @classmethod
    def close(cls):
        return WRC(WRC.CLOSE)

    @classmethod
    def success(cls):
        return WRC(WRC.SUCCESS)
    
    def check_none(self):    return bool(self.value == self.NONE)
    def check_exit(self):    return bool(self.value &  self.EXIT)
    def check_close(self):   return bool(self.value &  self.CLOSE)
    def check_success(self): return bool(self.value &  self.SUCCESS)

    def __str__(self):
        flags = []
        if self.check_none():
            flags.append('NONE')
        else:
            if self.check_exit():
                flags.append('EXIT')
            if self.check_close():
                flags.append('CLOSE')
            if self.check_success():
                flags.append('SUCCESS')
        return ' | '.join(flags)
    
    @classmethod
    def check_valid_int(cls, v:int, info=None) -> int:
        """
        Verify that 'v' is a valid WRC value.
        Returns v, converting to WRC.NONE if None
        """
        info = '\nDebug info: {}'.format(info) if info != None else ''
        if not isinstance(v, int):
            raise ValueError('Value is not an int' + info)
        if v < cls._MIN:
            raise ValueError('Value too small' + info)
        if v > cls._SUM:
            raise ValueError('Value too large' + info)
    
    def closed_window(self):
        if self.check_exit():
            return
        if self.check_close():
            self.clear(self.CLOSE)
        self.propagate()
    
    def clear(self, *flags):
        for flag in flags:
            self.value = self.value & ~flag
        self.propagate()
WRC = WindowReturnCode


class EventManager:

    def __init__(self, debug_id:str=None):
        self._callbacks_events_handlers:list[Callback] = []
        self._callbacks_events:dict[str, Callback] = {}
        self._callbacks_timed_events:OrderedDict[float, Callback] = OrderedDict()
        self.debug_id = debug_id
    
    def copy(self):
        em = EventManager(self.debug_id)
        em._callbacks_events_handlers = self._callbacks_events_handlers.copy()
        em._callbacks_events = self._callbacks_events.copy()
        return em

    ###

    def event_method(self, func, *events):
        """func: func(WindowContext)"""
        callback = Callback.event(func)
        for event in events:
            self._callbacks_events[event] = callback

    def event_handler(self, func):
        callback = Callback.event_handler(func)
        self._callbacks_events_handlers.append(callback)
    

    def event_value(self, value:int, *events):
        callback = Callback.event_value(value)
        for event in events:
            self._callbacks_events[event] = callback

    def event_after(self, func, after_secs:float):
        callback = Callback.event(func)
        at_time = time.time() + after_secs
        self._callbacks_timed_events.insert_before_if(lambda k, v: at_time < k, at_time, callback)

    ###

    def eventmethod(self, *events):
        """
        Decorator for adding event(s).
        \n
        @self.eventmethodmethod('event_key')\n
        def event_func(event_context:EventContext):\n
            ...\n
        \n
        Or,\n
        @self.eventmethodmethod('event_key1', 'event_key2')\n
        def event_func(event_context:EventContext):\n
            ..."""
        def wrap(f):
            self.event_method(f, *events)
            return f
        return wrap
    
    def eventhandler(self):
        def wrap(f):
            self.event_handler(f)
            return f
        return wrap

    ###

    def event_value_close_success(self, *events):   self.event_value(WRC.CLOSE | WRC.SUCCESS,    *events)
    def event_value_close(self, *events):           self.event_value(WRC.CLOSE,                  *events)
    def event_value_exit(self, *events):            self.event_value(WRC.EXIT,                   *events)

    ###

    def handle_event(self, event_context:EventContext) -> WRC:
        for callback in self._callbacks_events_handlers:
            rv = WRC(
                callback.func(event_context), 'EventHandler ' + callback.get_info())
            if rv.check_close():
                return rv
        if event_context.event in self._callbacks_events.keys():
            callback = self._callbacks_events[event_context.event]
            rv = WRC(callback.func(event_context), 'Event ' + callback.get_info())
            if rv.check_close():
                return rv
        return WRC()
    
    def handle_timed_events(self, event_context:EventContext):
        current_time = time.time()
        ready = self._callbacks_timed_events.pop_front_if(
            lambda k, v : k < current_time)
        for _, cb in ready:
            rv = WRC(cb.func(event_context))
            if rv.check_close():
                return rv
        return WRC()
    

class EventLoop:

    def __init__(self, em:EventManager=None):
        self.em = em
        self.em.debug_id = 'EventLoop' + self.em.debug_id
        self._callbacks_update = []
        self._callbacks_init_window = []
        self._callbacks_save = []
        self._callbacks_load = []
        self._callbacks_pull = []
        self._callbacks_push = []
        self.final_event_context = None

    def updatecallback(self):
        def wrap(f):
            self._callbacks_update.append(f)
            return f
        return wrap
    
    def savecallback(self, func, data):
        """func(data)"""
        def f():
            func(data)
        self._callbacks_save.append(f)
        return self
    
    def loadcallback(self, func, data):
        """func(data)"""
        def f():
            func(data)
        self._callbacks_load.append(f)
        return self
    
    def pullcallback(self, func):
        """func(values)"""
        self._callbacks_pull.append(func)
        return self

    def pushcallback(self, func):
        """func(window)"""
        self._callbacks_push.append(func)
        return self

    def initwindowcallback(self, func):
        """func(window)"""
        self._callbacks_init_window.append(func)
        return self

    def run(self, window_context:WindowContext, read_time=None) -> WRC:
        """Calls all pull and save functions if bool(returned value) == True.
        Saves the final event/values in 'final_event' and 'final_values' member variables"""
        start_time = time.time()
        for cb in self._callbacks_load:
            cb()
        for cb in self._callbacks_init_window:
            cb(window_context)
        for cb in self._callbacks_push:
            cb(window_context)
        rv = WRC()
        is_win_closed = False
        if read_time == None:
            read_time = -1
        event_context = EventContext(window_context=window_context)
        while True:
            if read_time > 0 or len(self.em._callbacks_timed_events) > 0:
                rt = read_time if read_time >= 10 else 10
                event_context.event, event_context.values = window_context.window.read(rt)
            else:
                event_context.event, event_context.values = window_context.window.read()
            if event_context.event == sg.WIN_CLOSED:
                is_win_closed = True
            event_context.data['time'] = time.time() - start_time
            rv = WRC(self.em.handle_timed_events(event_context))
            if rv.check_close():
                break
            for uf in self._callbacks_update:
                rv = WRC(uf(event_context))
                if rv.check_close():
                    break
            if rv.check_close():
                break
            rv = WRC(self.em.handle_event(event_context))
            if rv.check_close():
                break
            if is_win_closed:
                print('Failed to catch WIN_CLOSED event.')
                print('Events: {}'.format(self.em._callbacks_events))
                print('EventHandlers: {}'.format(
                    self.em._callbacks_events_handlers))
                break
        window_context.window.close()
        if rv.check_success():
            for cb in self._callbacks_pull:
                cb(event_context.values)
            for cb in self._callbacks_save:
                cb()
        self.final_event_context = EventContext.from_event_context(event_context)
        return rv

    def run_timed(self, window_context:WindowContext) -> WRC:
        return self.run(window_context, read_time=50)
        