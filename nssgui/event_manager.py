from __future__ import annotations
import time
import inspect
import PySimpleGUI as sg

__all__ = [
    'EventManager',
    'EventLoop',
    'WindowReturnCode',
    'WRC',
    'NULL_EVENT'
]

NULL_EVENT = 'NULL_EVENT'

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
        cb.func = lambda context : value
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
        """Flip additional flags automatically based on current flags flipped."""
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
        """Verify that 'v' is a valid WRC value. Returns v, converting to WRC.NONE if None"""
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
        self._callbacks_event_handlers:list[Callback] = []
        self._callbacks_event:dict[str, Callback] = {}
        self.debug_id = debug_id
    
    def copy(self):
        em = EventManager(self.debug_id)
        em._callbacks_event_handlers = self._callbacks_event_handlers.copy()
        em._callbacks_event = self._callbacks_event.copy()
        return em
    

    ###


    def event_method(self, func, *events):
        """func: func(WindowContext)"""
        callback = Callback.event(func)
        for event in events:
            self._callbacks_event[event] = callback
    

    def event_handler(self, func):
        callback = Callback.event_handler(func)
        self._callbacks_event_handlers.append(callback)
    

    def event_value(self, value:int, *events):
        callback = Callback.event_value(value)
        for event in events:
            self._callbacks_event[event] = callback
    

    ###
    

    def eventmethod(self, *events):
        """
        Decorator for adding event(s).
        \n
        @self.eventmethodmethod('event_key')\n
        def event_func(context):\n
            ...\n
        \n
        Or,\n
        @self.eventmethodmethod('event_key1', 'event_key2')\n
        def event_func(context):\n
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
    def event_value_close_save(self, *events):      self.event_value(WRC.CLOSE | WRC.SUCCESS,    *events)
    def event_value_close_failure(self, *events):   self.event_value(WRC.CLOSE,                  *events)
    def event_value_close_discard(self, *events):   self.event_value(WRC.CLOSE,                  *events)
    def event_value_exit(self, *events):            self.event_value(WRC.EXIT,                   *events)


    ###
    

    def handle_event(self, context) -> WRC:
        for callback in self._callbacks_event_handlers:
            rv = WRC(callback.func(context), 'EventHandler ' + callback.get_info())
            if rv.check_close():
                return rv
        if context.event in self._callbacks_event.keys():
            callback = self._callbacks_event[context.event]
            rv = WRC(callback.func(context), 'Event ' + callback.get_info())
            if rv.check_close():
                return rv
        return WRC()
    
    

class EventLoop:
    def __init__(self, em:EventManager=None):
        self.em = em.copy()
        self.em.debug_id = 'EventLoop' + self.em.debug_id
        self._callbacks_update = []
        self._callbacks_init_window = []
        self._callbacks_save = []
        self._callbacks_load = []
        self._callbacks_pull = []
        self._callbacks_push = []
        self.final_event = 'NoEvent'
        self.final_values = None
    

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
    

    def run(self, context, read_time=None) -> WRC:
        """Calls all pull and save functions if bool(returned value) == True.
        Saves the final event/values in 'final_event' and 'final_values' member variables"""
        start_time = time.time()
        for cb in self._callbacks_load:
            cb()
        for cb in self._callbacks_init_window:
            cb(context._window)
        for cb in self._callbacks_push:
            cb(context.window)
        rv = WRC()
        is_win_closed = False
        while True:
            if read_time != None and read_time <= 0:
                context.event, context.values = context.window.read()
            else:
                context.event, context.values, = context.window.read(read_time)
            if context.event == sg.WIN_CLOSED:
                is_win_closed = True
            context.data['time'] = time.time() - start_time
            for uf in self._callbacks_update:
                rv = WRC(uf(context))
                if rv.check_close():
                    break
            if rv.check_close():
                break
            rv = WRC(self.em.handle_event(context))
            if rv.check_close():
                break
            if is_win_closed:
                print('Failed to catch WIN_CLOSED event.')
                print('Events: {}'.format(self.em._callbacks_event))
                print('EventHandlers: {}'.format(self.em._callbacks_event_handlers))
                break
        context.window.close()
        if rv.check_success():
            for cb in self._callbacks_pull:
                cb(context.values)
            for cb in self._callbacks_save:
                cb()
        self.final_event = context.event
        self.final_values = context.values.copy() if context.values != None else None
        return rv
    

    def run_timed(self, context) -> WRC:
        return self.run(context, read_time=50)