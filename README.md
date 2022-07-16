# Overview

## Description

nssgui (not-so-simple GUI). An extension of PySimpleGUI. Still a work-in-progress. Sacrifices simplicity for productivity, by extending PySimpleGUI with advanced features. nssgui does not require an overhaul of PySimpleGUI to use. They are able to coexist and maintain simplicity for simple programs. Incorporating nssgui windows and event handling, however, will turn a program into a more complex structure. nssgui's complex popups may be used as independent one-liners even, in an otherwise standard PySimpleGUI program.

The core features added by nssgui are:
- GuiElement: A base class for creating advanced, nestable elements with data flow (window<->objects<->dicts) made easy
- Event handling
- Data flow management
- Popup builder

&nbsp;

## State of nssgui

For now, this project is mostly just a separated piece of BackupScripter with plans to become an independent library.

This package is currently(July 2022) making some major revisions to:
- Names
- Classes, Inheritance, Interfaces
- Documentation
- Old, unused functions

And then there will be a slow build up of demo programs to flesh out the coverage of PySimpleGUI's features, incorporating convenience functions and such as appropriate. Anything that would not fit into the base PySimpleGUI due to complexity may be implemented here. Additionally, until there exist examples comparing use cases of PySimpleGUI vs PySimpleGUI+nssgui, I can't really advertise the effectiveness of this package. For simple programs, PySimpleGUI alone would more than suffice. If one becomes familiar with nssgui, I hope for PySimpleGUI+nssgui to be useful for even simple programs.

nssgui currently has a very small amount of tkinter-specific code. There is no strong dedication to tkinter as of now, but this is still up in the air. tkinter will serve as the default, whether nssgui is made compatible with qt, etc. Currently, the outlook is that if a desired feature will only be possible in tkinter, then nssgui will have to be tkinter only. (I have tried and failed to make a gray-out effect for an entire window when disabled, but this is likely the type of feature I am talking about.)

&nbsp;

## Platforms

This library has only been developed and tested on Windows 10.

It should not take much work to get it working on other platforms, which is a priority after the current(July 2022) major revisions.

&nbsp;

## Installation

nssgui is not currently in PyPi, but it may be installed from github

```
python -m pip install git+https://github.com/seth-kitchens/nssgui
```

Here is a one liner to test if it's working

```
import nssgui as nss
nss.popups.ok(nss.WindowContext(), 'NSS is installed and working!')
```

&nbsp;

# Documentation

## Terms

`nss`: Abbreviation and suggested import alias for nssgui

`ge`: GuiElement, nssgui's core element class

`sg`: Abbreviation and suggested import alias for PySimpleGUI

`sge`: PySimpleGUI Element. `Input`, `Text`, `Column`, etc.

`row`: This is commonly used to mean a list of sge's

&nbsp;

## Core Concepts

### PySimpleGUI

This project is an extension of PySimpleGUI, so a basic understanding of it is important. See its docs [here](https://pysimplegui.readthedocs.io/en/latest/).

&nbsp;

### GuiElement

A logical part of a window that represents one or more PySimpleGui elements, made to be subclassed to create your own reusable element.

The individual sg elements may be accessed from the `sg.Window` by accessing the key from a `GuiElement` object. See: [Keys](#keys)

By defining the data methods `save`, `load`, `pull` and `push` in a subclass, you can control how data moves between the object and the window, and how data is stored and loaded. See: [Data Flow](#data-flow)

The layout can be defined as one of three kinds, an `sge`, `row` or `layout`, which are a single sg element, a list of sg elements, or a list of lists of sg elements respectively. These are retrieved through the `get_sge()`, `get_row()` and `get_layout()` methods. See: [Layouts](#layouts)

A `GuiElementManager` (GEM) may be used to easily propagate calls to data methods and event handlers out to many `GuiElements` at once. The GEM's data methods are `for_ges_save()`, `for_ges_load()`, `for_ges_push()` and `for_ges_pull()`, taking the same parameters as the equivalent GE methods. The event handler takes the same form as other event handlers in nssgui, `handle_event(self, context:WindowContext)`. Both `GuiElement` and the nss window classes have their own `GuiElementManager`, with interface methods to easily use the GEM. By using nssgui windows, you will not need to use these methods yourself, but referencing the GEM will still be useful for accessing the stored GEs: `self.gem[object_id]`. More on nssgui windows: [Windows](#windows).

`GuiElement` may be useful to achieve the following:

- A reusable layout pattern of elements to be used repeatedly in different parts of a GUI program, or even multiple programs
- Defining a data flow for an otherwise simple section of a GUI layout
- Creating more advanced dynamically generated elements

For a guide to subclassing, see: [Subclassing GuiElement](#subclassing-guielement)

&nbsp;

### Keys

PySimpleGUI uses keys (strings) to differentiate elements on the screen. nssgui uses named keys to identify keys with an object, which makes them unique to that class. So if there was a `GuiElement` for inputting a full name, "FullName", with a "First" field, and there was an instance object "customer_name" with an object id "CustomerName", then the element would be accessed as `customer_name.keys['First']`, which would resolve to "FirstCustomerName". By convention, other classes using these keys should have a public `keys` dict and an `add_key(self, key_name)` method.

&nbsp;

### Layouts

One central design of nssgui is maintaining the layout system that PySimpleGUI uses, apart from breaking up the layout generation into `GuiElement` methods and nssgui windows separating layouts from the PySimpleGUI windows and from the event loop. Individual `GuiElement` instances may be completely defined in one line (optionally), within the layout definition. Any interaction with other elements will still need to be defined elsewhere of course.

`GuiElement` subclasses for the most part only need the required layout method. Classes made to be further subclassed might want to break the layout into separately overrideable methods.

&nbsp;

### Event Handling

nssgui provides infrastructure for event handling PySimpleGUI events, but it is optional, at least at the window level. Even if a program or window uses the standard PySimpleGUI layout->window->eventloop pattern, a GuiElement's `handle_event()` method may be used, which utilizes the event handling classes.

&nbsp;

### Windows

TODO

For a guide to subclassing nssgui windows, see below: [Subclassing Windows](#subclassing-windows)

&nbsp;

### Data Flow

Most elements in a GUI program are either a type of input or output. On the backend however, there are times where both of these require data to be communicated in either direction: From the object to the window, or from the window to the object (e.g. input elements are usually initialized, and output elements may be depended on by other elements). Then, data must flow between the objects and other functions. This gives four directions of data flow that must be managed. nssgui uses four methods to accomplish this:

- `save(self, data:dict)` Object -> Dict
- `load(self, data:dict)` Dict -> Object
- `push(self, window:sg.Window)` Object -> Window
- `pull(self, values:dict)` Window -> Object

These are essential to using `GuiElement` objects. Objects communicate to a sg.Window with their keys, and to a dict with their `object_id`.

&nbsp;

## Subclassing GuiElement

### Subclassing GE: Basic Process

1. Subclass `iSge`, `iRow` or `iLayout` before GuiElement. Example:
    ```
    class mygesubclass(GuiElement.iRow, GuiElement)
    ```

2. Define layout in the respective method:
    - `_get_sge()` OR
    - `_get_row()` OR
    - `_get_layout()`
    
3. Override definition methods needed
    - `define_keys()`
    - `define_events()`
    - `define_menus()`

&nbsp;

### Subclassing GE: Initialization

GuiElements are made to be defined within a layout definition, where instantiation is followed by a get (sge|row|layout) method, which may be called again later. Some of initialization is delayed until a layout method is first called.

- External: GuiElement subclass's constructor
    - `__init__()`
    - `define_keys()`
    - internal `GuiElementManager` constructed
    - `define_menus()`
- External: Any initializing methods, e.g. `load_value` (note that many are chainable)
- External: `get_sge()` OR `get_row()` OR `get_layout()`
    - `_get_sge()` OR `_get_row()` OR `_get_layout()`
    - `define_events()`
- External: `init_window_finalized()` after sg.Window is finalized
    - `_init_window_finalized()`
        - Initializing data methods

The order here is important, for several reasons:
- Named keys will be referenced in most methods, and must come first
- Nested GuiElements do not exist until the layout method is first called. These have to exist before `define_events()` is called, so `define_events()` is delayed until a layout method is called first. nssgui windows actually generate and discard a layout for this purpose.
- `init_window_finalized()`, as the name suggests, needs the window to be finalized before it is called. nssgui windows do this in their `open()` method.

&nbsp;

### Subclassing GE: SG Element Kwargs

GuiElements represent one or more SG Elements. To easily provide a way to pass kwargs to sg elements, you may use `sg_kwargs` related methods.
- Make a `sg_kwargs_<key_name>(self, **kwargs)` method for each sg element you want to
provide kwarg passing for
    - Use `_set_sg_kwargs('key_name')` to set the values
- In the layout method (_get_layout(), etc):
    - Use `default_sg_kwargs()` to define defaults if needed
    - Add `**self._sg_kwargs['key_name']` to the elements' constructors

Making the methods give clear indication that sg_kwargs are supported for the element, rather just adding parameter and expecting use of `_set_sg_kwargs()`.

&nbsp;

### Subclassing GE: Nested GuiElements

GuiElements can be used within a GuiElement's layout. `GuiElement` inherits `GuiElementLayoutManager` and can use it's layout storing methods

- Use the `sge()` `row()` and `layout()` methods within the layout method
- Use a named key for the nested GE's object_id
- Access the nested GE with the `ges()` method

&nbsp;

### Subclassing GE: Contained GuiElements

Subclass GuiElementContainer instead of GuiElement directly, passing the contained elements(s) to its `__init__()` method.

Unlike regular nested elements, contained elements are defined outside the class and passed to it. This has not been very thoroughly developed at the time or writing, but for an example you may check the abstract base class `ListContainer`, the subclass containers `StringContainer` and `CountContainer`, and the containable GuiElements `TextList` and `DetailList`.

GuiElementContainer:
- Stores the contained element(s) in self.contained
- Gives the container an object_id based on the contained object ids.
- Adds the contained element(s) with `add_ge()`

In `define_events()` Define the contained element's `handle_event()` method as an event handler:
```
self.event_handler(self.contained_ge.handle_event())
```

GuiElement provides some interfaces and the `check_if_instances()` function for defining containers and containable GuiElements.

&nbsp;

## Subclassing Windows

TODO
