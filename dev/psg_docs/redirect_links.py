import pathlib
import re

from options import *

psg_docs_relpaths = [
    relpath_psg_docs_home,
    relpath_psg_docs_call_ref,
    relpath_psg_docs_cookbook,
    relpath_psg_docs_readme
]

# dict: replaced_by -> list[replaces]
subs = {
    relpath_psg_docs_home: [
        'https://www.pysimplegui.org/en/latest/'
    ],
    relpath_psg_docs_call_ref: [
        'https://www.pysimplegui.org/en/latest/call%20reference/'
    ],
    relpath_psg_docs_cookbook: [
        'https://www.pysimplegui.org/en/latest/cookbook/'
    ],
    relpath_psg_docs_readme: [
        'https://www.pysimplegui.org/en/latest/readme/'
    ]
}

for relpath in psg_docs_relpaths:
    path = pathlib.Path(relpath).absolute().resolve()
    with path.open('r', encoding='utf8') as file:
        text = file.read()
    for str_to, strs_from in subs.items():
        for str_from in strs_from:
            pattern = 'href="{}(?=[^\w])'.format(re.escape(str_from))
            repl = 'href="{}'.format(str_to)
            text = re.sub(pattern, repl, text)
    with path.open('w', encoding='utf8') as file:
        file.write(text)