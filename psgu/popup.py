import textwrap
import time
from math import ceil
from typing import Any, Iterable

import PySimpleGUI as sg

from psgu.style import colors
from psgu.event_handling import NULL_EVENT, EventManager, WRC
from psgu.event_loop import EventLoop
from psgu.event_context import EventContext
from psgu import sg as psgu_sg
from psgu.window_context import WindowContext


__all__ = [
    'PopupElement',
    'Popup',
    'PopupBuilder',
    'popups'
]
button_size = psgu_sg.button_size


class PopupElement:

    GE_SGE = 'ge_sge'
    GE_ROW = 'ge_row'
    SGE = 'sge'

    def __init__(self, cls, pe_type, key=None, args=None, **kwargs):
        self.cls = cls
        self.pe_type = pe_type
        self.key = key
        if key != None:
            kwargs['key'] = key
        self.args = args if args != None else ()
        self.kwargs = kwargs

    def sge(cls, key=None, args=None, **kwargs):
        return PopupElement(
            cls, PopupElement.SGE, key=key, args=args, **kwargs)

    def ge_sge(cls, key=None, args=None, **kwargs):
        return PopupElement(
            cls, PopupElement.GE_SGE, key=key, args=args, **kwargs)

    def ge_row(cls, key=None, args=None, **kwargs):
        return PopupElement(
            cls, PopupElement.GE_ROW, key=key, args=args, **kwargs)


class Popup(EventManager):

    def __init__(self):
        super().__init__(debug_id='Popup')
        self.title = None
        self.auto_ok_text = None
        self.auto_ok_secs = None
        self.pes = {} # key->PopupElement, ordered, key may be garbage unique value
        self.final_event_context = None
        self.init_focus = None
        self.true_events = []
        self.false_events = []

    def get_layout(self):
        layout = []
        row = []
        for pe in self.pes.values():
            if pe == None:
                if not row:
                    row = [sg.Text('')]
                layout.append(row)
                row = []
            else:
                el = pe.cls(*pe.args, **pe.kwargs)
                if pe.pe_type == PopupElement.SGE:
                    row.append(el)
                elif pe.pe_type == PopupElement.GE_SGE:
                    row.append(el)
                elif pe.pe_type == PopupElement.GE_ROW:
                    for sge in el.row():
                        row.append(sge)
        if row:
            layout.append(row)
        return layout
    
    def update_auto_ok(self, window, secs_left):
        window['ok'].update(text=self.auto_ok_text + ' [' + str(ceil(secs_left)) + ']')
    
    def make_key(self):
        return str(time.time()) + str(len(self.pes))

    def newline(self):
        key = self.make_key()
        self.pes[key] = None
        return self

    def pe(self, pe):
        key = pe.key if pe.key != None else self.make_key()
        self.pes[key] = pe
        return self

    def sge(self, cls, key=None, args=None, **kwargs):
        self.pe(PopupElement.sge(cls, key, args=args, **kwargs))
        return self

    def ge_sge(self, cls, key=None, args=None, **kwargs):
        self.pe(PopupElement.ge_sge(cls, key, args=args, **kwargs))
        return self

    def ge_row(self, cls, key=None, args=None, **kwargs):
        self.pe(PopupElement.ge_row(cls, key, args=args, **kwargs))
        return self

    def open(self, window_context:WindowContext|None=None) -> WRC:
        window_context = window_context.from_any(window_context)
        window_context.disable()
        self.event_value_close(sg.WIN_CLOSED)
        self.event_value_close_success(*self.true_events)
        self.event_value_close(*self.false_events)
        layout = self.get_layout()
        title = self.title if self.title else ''
        window_context.push(sg.Window(title, layout, finalize=True))
        if self.init_focus:
            we = window_context.window[self.init_focus]
            we.set_focus()
            psgu_sg.set_cursor_to_end(we)
        event_loop = EventLoop(self)
        if self.auto_ok_secs:
            window_context.data['self'] = self
            
            @event_loop.updatecallback
            def uf(event_context:EventContext):
                popup = event_context.data['self']
                secs_passed = event_context.data['time']
                secs_left = popup.auto_ok_secs - secs_passed
                popup.update_auto_ok(event_context.window, secs_left)
                if secs_left < -0.2:
                    return WRC.close()
                return WRC.none()
            
            rv = WRC(event_loop.run_timed(window_context))
        else:
            rv = WRC(event_loop.run(window_context))
        self.final_event_context = event_loop.final_event_context
        window_context.pop()
        window_context.enable()
        window_context.focus()
        rv.closed_window()
        return rv


class PopupBuilder:

    def __init__(self) -> None:
        """
        Some elements are ordered (text, ges/sges, etc)
        and some aren't (ok button, title, etc) The ordered elements
        form the body of the popup, between any headers or buttons
        """
        self.popup = Popup()
        self._pes = []
        self.final_event_context = None

        # Unordered
        self._header = None
        self._header_color = None
        self._subheader = None
        self._ok = None
        self._cancel = None
        self._auto_ok_secs = None

    # Ordered

    def pe(self, pe):
        """Ordered"""
        self._pes.append(pe)
        return self

    def newline(self):
        """Ordered"""
        self._pes.append(None)
        return self

    def sge(self, cls, key=None, args=None, **kwargs):
        """Ordered"""
        self.pe(PopupElement.sge(cls, key, args=args, **kwargs))
        return self

    def ge_sge(self, cls, key=None, args=None, **kwargs):
        """Ordered"""
        self.pe(PopupElement.ge_sge(cls, key, args=args, **kwargs))
        return self

    def ge_row(self, cls, key=None, args=None, **kwargs):
        """Ordered"""
        self.pe(PopupElement.ge_row(cls, key, args=args, **kwargs))
        return self

    def text(self, text:str|Iterable|None, text_color=None):
        """Ordered. 'None' is ignored."""
        if text == None:
            return self
        if isinstance(text, str):
            self.sge(sg.Text, text=text, text_color=text_color).newline()
        else:
            for s in text:
                self.sge(sg.Text, text=s, text_color=text_color).newline()
        return self

    def textwrap(self, s, width=70):
        """Ordered"""
        strings = s.split('\n')
        wrapped_strings = []
        for string in strings:
            wrapped_strings.append(textwrap.fill(string, width))
        s = '\n'.join(wrapped_strings)
        self.sge(sg.Text, text=s).newline()
        return self
    
    # Unordered

    def title(self, s):
        """Unordered"""
        if s == None:
            return self
        self.popup.title = s
        return self

    def header(self, s, color=None):
        """Unordered"""
        if s == None:
            return self
        self._header = s
        if color:
            self._header_color = color
        return self

    def subheader(self, s):
        """Unordered"""
        if s == None:
            return self
        self._subheader = s
        return self

    def ok(self, s='OK'):
        """Unordered"""
        self._ok = s
        return self

    def cancel(self, s='Cancel'):
        """Unordered"""
        self._cancel = s
        return self

    def auto_ok(self, secs=3):
        """Unordered"""
        if not self._ok:
            self._ok = 'OK'
        self._auto_ok_secs = secs
        return self

    def init_focus(self, key):
        """Unordered"""
        self.popup.init_focus = key
        return self
    
    # Events

    def event_save_close(self, key):
        self.popup.event_value_close_success(key)

    def event_close(self, key):
        self.popup.event_value_close(key)
    
    # Finalizers
    
    def get(self):
        """Finalizer. Returns Popup object."""
        if self._header != None:
            if self._header_color:
                header_color = self._header_color
            else:
                header_color = colors.header
            self.popup.sge(
                sg.Text, text=self._header, text_color=header_color).newline()
        if self._subheader != None:
            self.popup.sge(sg.Text, text=self._subheader).newline()
            self.popup.sge(sg.HSeparator).newline()
        for pe in self._pes:
            if pe != None:
                self.popup.pe(pe)
            else:
                self.popup.newline()
        has_button_row = (self._ok or self._cancel)
        if has_button_row:
            self.popup.sge(sg.Sizer, args=(0, 5)).newline()
            self.popup.sge(sg.Push)
            if self._ok:
                if self._auto_ok_secs != None:
                    self.popup.auto_ok_text = self._ok
                    self.popup.auto_ok_secs = self._auto_ok_secs
                    ok_text = self._ok + ' [' + str(self._auto_ok_secs) + ']'
                else:
                    ok_text = self._ok
                self.popup.sge(
                    sg.Button, key='ok', button_text='Ok',
                    size=button_size.at_least(10, ok_text))
                self.popup.true_events.append('ok')
            if self._cancel:
                self.popup.sge(
                    sg.Button, key='cancel', button_text='Cancel',
                    size=button_size.at_least(10, self._cancel))
                self.popup.false_events.append('cancel')
            self.popup.sge(sg.Push)
        return self.popup

    def open(self, window_context:WindowContext|None=None):
        """
        Finalizer. Opens popup window, then returns rv from event
        (non-None that closed window) and values
        from last sg.Window.read() call
        """
        rv = self.get().open(window_context)
        self.final_event_context = self.popup.final_event_context
        return rv

    def get_layout(self):
        return self.popup.get_layout()


class popups:

    def ok(window_context:WindowContext|None, text:str|Iterable|None, title=''):
        return PopupBuilder() \
            .ok() \
            .title(title) \
            .text(text) \
            .open(window_context)
    
    def confirm(window_context:WindowContext|None, text:str|Iterable|None, title='Confirm'):
        wrc = PopupBuilder() \
            .ok() \
            .cancel() \
            .title(title) \
            .text(text) \
            .open(window_context)
        return wrc.check_success()
    
    def error(window_context:WindowContext|None, text:str|Iterable|None):
        return PopupBuilder() \
            .title('Error') \
            .header('Error', colors.error) \
            .ok() \
            .text(text) \
            .open(window_context)
    
    def warning(window_context:WindowContext|None, text:str|Iterable|None):
        wrc = PopupBuilder() \
            .title('Warning') \
            .header('Warning', colors.warning) \
            .ok() \
            .cancel() \
            .text(text) \
            .open(window_context)
        return wrc.check_success()
    
    def edit_string(
            window_context:WindowContext|None,
            s,
            label=None,
            title='',
            body_text:str|Iterable|None=None, 
            fill_prev=True):
        pb = PopupBuilder() \
            .ok() \
            .cancel() \
            .title(title) \
            .text(body_text)
        if label != None:
            pb.pe(PopupElement.sge(sg.Text, key='Label', text=label))
        in_text = s if fill_prev else ''
        pb.pe(
            PopupElement.sge(sg.Input, default_text=in_text, key='In')
        ).init_focus('In')
        wrc = pb.open(window_context)
        values = pb.final_event_context.values
        return values['In'] if wrc.check_success() else s
    
    def choose(window_context:WindowContext|None, text:str|Iterable|None, options:Iterable|dict, title='', **button_kwargs):
        pb = PopupBuilder().title(title).text(text)
        if 'size' not in button_kwargs and 's' not in button_kwargs:
            button_kwargs['size'] = 10
        pb.pe(PopupElement.sge(sg.Push))
        if isinstance(options, dict):
            for key, text in options.items():
                pe = PopupElement.sge(sg.Button, key=key, button_text=text, **button_kwargs)
                pb.pe(pe)
                pb.event_save_close(key)
        else:
            for text in options:
                pe = PopupElement.sge(sg.Button, key=text, button_text=text, **button_kwargs)
                pb.pe(pe)
                pb.event_save_close(text)
        pb.pe(PopupElement.sge(sg.Push))
        wrc = pb.open(window_context)
        event = pb.final_event_context.event
        return event if wrc.check_success() else None

    def ok_multiline(window_context:WindowContext|None, text:str|Any, size=(120, 20)):
        """
        Converts `text` to str then displays it in a large multiline.
        Good for debugging.
        """
        text = str(text)
        return PopupBuilder() \
            .ok() \
            .sge(sg.Multiline, default_text=str(text), size=size) \
            .open(window_context)