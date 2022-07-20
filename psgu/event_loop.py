from __future__ import annotations
import time

import PySimpleGUI as sg

from psgu.event_handling import *
from psgu.event_context import *
from psgu.window_context import WindowContext


__all__ = [
    'EventLoop'
]


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

    def run(self, window_context:WindowContext|None=None, read_time=None) -> WRC:
        """Calls all pull and save functions if bool(returned value) == True.
        Saves the final event/values in 'final_event' and 'final_values' member variables"""
        window_context = WindowContext.from_any(window_context)
        window = window_context.window
        start_time = time.time()
        for cb in self._callbacks_load:
            cb()
        for cb in self._callbacks_init_window:
            cb(window)
        for cb in self._callbacks_push:
            cb(window)
        rv = WRC()
        is_win_closed = False
        if read_time == None:
            read_time = -1
        event_context = EventContext(window_context=window_context)
        while True:
            if read_time > 0 or len(self.em._callbacks_timed_events) > 0:
                rt = read_time if read_time >= 10 else 10
                event_context.event, event_context.values = window.read(rt)
            else:
                event_context.event, event_context.values = window.read()
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
        window.close()
        if rv.check_success():
            for cb in self._callbacks_pull:
                cb(event_context.values)
            for cb in self._callbacks_save:
                cb()
        self.final_event_context = EventContext.from_event_context(event_context)
        return rv

    def run_timed(self, window_context) -> WRC:
        return self.run(window_context, read_time=50)
        