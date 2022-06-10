import time
from typing import Callable, Iterable

class EventManager:
    def __init__(self, event_data=None, true_events=None, false_events=None, events:list[tuple[str, Callable]]=None):
        self.handle_event_funcs = []
        self._bool_events = {}
        self.event_funcs = {}
        self.update_functions = []
        self.init_window_functions = []
        self.save_functions = []
        self.load_functions = []
        self.pull_functions = []
        self.push_functions = []
        self.keys = {}
        self.final_event = None
        self.final_values = None
        if true_events:
            for e in true_events:
                self.true_event(e)
        if false_events:
            for e in false_events:
                self.false_event(e)
        if events:
            for e, func in events:
                self.event_function(e, func)
    
    def event_handler(self):
        def wrap(f):
            self.handle_event_function(f)
            return f
        return wrap
    def handle_event_function(self, func):
        """func(context)"""
        self.handle_event_funcs.append(func)
        return self
    
    def update(self):
        def wrap(f):
            self.update_function(f)
            return f
        return wrap
    def update_function(self, func):
        """func(context)"""
        self.update_functions.append(func)
        return self
    
    def event(self, event):
        """Decorator for adding event. Can be used in succession"""
        def wrap(f):
            self.event_function(event, f)
            return f
        return wrap
    def event_function(self, event, func):
        """func(context)"""
        # print('binding event func', event)
        self.event_funcs[event] = func
    
    def events(self, events:Iterable):
        """Decorator for adding events. Alternative to using event() in succession."""
        def wrap(f):
            self.event_functions(events, f)
            return f
        return wrap
    def event_functions(self, events, func):
        """func(context)"""
        for event in events:
            self.event_funcs[event] = func
    
    def append(self, prev_event, event):
        f = self.event_funcs[prev_event]
        self.event_function(event, f)
    
    def true_event(self, event):
        self._bool_events[event] = True
        return self
    def false_event(self, event):
        self._bool_events[event] = False
        return self
    def bool_events(self, true_events=None, false_events=None):
        if true_events:
            for event in true_events:
                self._bool_events[event] = True
        if false_events:
            for event in false_events:
                self._bool_events[event] = False
        return self
    
    def save_function(self, func, data):
        """func(data)"""
        def f():
            func(data)
        self.save_functions.append(f)
        return self
    def load_function(self, func, data):
        """func(data)"""
        def f():
            func(data)
        self.load_functions.append(f)
        return self
    def pull_function(self, func):
        """func(values)"""
        self.pull_functions.append(func)
        return self
    def push_function(self, func):
        """func(window)"""
        self.push_functions.append(func)
        return self
    def init_window_function(self, func):
        """func(window)"""
        self.init_window_functions.append(func)
        return self
    
    def handle_event(self, context):
        #print('DBG handle_event() start, event:', context.event, ', event_funcs:', self.event_funcs.keys())
        if context.event in self._bool_events.keys():
            #print('DBG em.handle_event(): event handled as bool')
            return self._bool_events[context.event]
        for func in self.handle_event_funcs:
            #print('DBG em.handle_event(): handing event to other handler')
            func(context)
        if context.event in self.event_funcs.keys():
            #print('DBG em.handle_event(): event handled by event func')
            return self.event_funcs[context.event](context)
        #print('DBG em.handle_event(): event not handled')
        return None
    
    def event_loop(self, context, read_time=None):
        """Exits immediately when a non-None value is returned from any
        handle-event function or update function. Returns the non-None value.
        Calls all pull and save functions if bool(returned value) == True.
        Saves the final event/values in 'final_event' and 'final_values' member variables"""
        start_time = time.time()
        for func in self.load_functions:
            func()
        for func in self.init_window_functions:
            func(context.window)
        for func in self.push_functions:
            func(context.window)
        rv = None
        while True:
            if read_time != None and read_time <= 0:
                context.event, context.values = context.window.read()
            else:
                context.event, context.values, = context.window.read(read_time)
            # print('values:', context.values)
            context.data['time'] = time.time() - start_time
            for uf in self.update_functions:
                if (rv := uf(context)) != None:
                    break
            if rv != None:
                break
            if (rv := self.handle_event(context)) != None:
                break
        context.window.close()
        if rv:
            for pull_function in self.pull_functions:
                pull_function(context.values)
            for save_function in self.save_functions:
                save_function()
        self.final_event = context.event
        self.final_values = context.values.copy() if context.values != None else None
        return rv
    def timed_event_loop(self, context):
        self.event_loop(context, read_time=50)