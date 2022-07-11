# nssgui

## Description

NotSoSimpleGUI (nssgui). An extension of PySimpleGUI. Still very much a work-in-progress. Sacrifices simplicity for productivity. Adds event handling, data flow management, a popup builder, expandable widgets ("GuiElements"), and other small things.



## State of nssgui

For now, this project is mostly just a separated piece of BackupScripter with plans to become an independent library.

This package will soon (somewhat soon, at least) be making some major revisions to the names and structures within it, so it's not quite ready to be used.
There is a lack of documentation or examples, both of which will be coming with the revisions.

Until there are sufficient examples, I can't give any good argument for what this library has to offer, so I will wait on making a full intro into how it is used until then.



## Platforms

This library has only been developed and tested on Windows 10.

It should not take much work to get it working on other platforms, which is a priority.



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
