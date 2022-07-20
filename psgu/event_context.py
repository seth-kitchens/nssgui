from __future__ import annotations

import PySimpleGUI as sg

from psgu.window_context import WindowContext


__all__ = [
    'EventContext'
]
NULL_EVENT = 'NULL_EVENT'


class EventContext:

    def __init__(self, window_context:WindowContext|sg.Window|None=None, event=NULL_EVENT, values=None, data=None):
        self.event = event
        if values is None:
            self.values = {}
        else:
            self.values = values
        if data is None:
            self.data = {}
        else:
            self.data = data
        self.window_context = WindowContext.from_any(window_context)
    
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
            window_context=event_context.window_context,
            event=event_context.event,
            values=values,
            data=data
        )
    
    def get_window(self):
        return self.window_context.window
    window = property(fget=get_window)