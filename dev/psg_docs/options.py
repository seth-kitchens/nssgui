import os
import pathlib

current_dir = os.path.dirname(os.path.abspath(__file__))

open_after = True

path_html_out = os.path.join(current_dir, 'psg_docs.html')

uri_psgu_github = 'https://github.com/seth-kitchens/psg-unsimplified'

relpath_psg_docs_home = 'psg_docs_home.html'
relpath_psg_docs_call_ref = 'psg_docs_call_reference.html'
relpath_psg_docs_cookbook = 'psg_docs_cookbook.html'
relpath_psg_docs_readme = 'psg_docs_readme.html'

uri_psg_docs_home = pathlib.Path(relpath_psg_docs_home).absolute().as_uri()
uri_psg_docs_call_ref = pathlib.Path(relpath_psg_docs_call_ref).absolute().as_uri()
uri_psg_docs_cookbook = pathlib.Path(relpath_psg_docs_cookbook).absolute().as_uri()
uri_psg_docs_readme = pathlib.Path(relpath_psg_docs_readme).absolute().as_uri()
uri_psg_github = 'https://github.com/PySimpleGUI/PySimpleGUI'

uri_pydocs_tkinter = 'https://docs.python.org/3/library/tk.html'
uri_pydocs_tkinter_how_do_i = 'https://docs.python.org/3/library/tkinter.html#how-do-i-what-option-does'

uri_tk_commands = 'https://www.tcl.tk/man/tcl8.6/TkCmd/contents.html'
