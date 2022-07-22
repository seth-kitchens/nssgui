import os
from yattag import Doc

from options import *

###

doc, tag, text = Doc().tagtext()

def link_line(label, linktext, link, add_local=True):
    if link.startswith('file:'):
        linktext = linktext + ' (local)'
    with tag('p'):
        if label:
            text(label + ' ')
        with tag('a', href=link, target='_blank'):
            text(linktext)

###

with tag('h1'):
    text('psg docs')

doc.stag('hr')

with tag('h2'):
    text('Links to Docs')

with tag('h3'):
    text('psg-unsimplified')

link_line('', 'psgu github', uri_psgu_github)

with tag('h3'):
    text('PySimpleGUI')

link_line('', 'psg docs home', uri_psg_docs_home)
link_line('', 'psg docs call ref', uri_psg_docs_call_ref)
link_line('', 'psg docs cookbook', uri_psg_docs_cookbook)
link_line('', 'psg docs readme', uri_psg_docs_readme)
link_line('', 'psg github', uri_psg_github)

with tag('h3'):
    text('tkinter')

link_line('', 'docs.python tkinter', uri_pydocs_tkinter)
link_line('', 'docs.python tkinter how do i', uri_pydocs_tkinter_how_do_i)

with tag('h3'):
    text('tk/tcl')

link_line('', 'tk commands', uri_tk_commands)

doc.stag('hr')

with tag('h2'):
    text('Elements')

with tag('p'):
    text('TODO')

text_html_out = doc.getvalue()
with open(path_html_out, 'w') as file_out:
    file_out.write(text_html_out)

if open_after:
    if os.name == 'nt':
        os.system('start {}'.format(path_html_out))
