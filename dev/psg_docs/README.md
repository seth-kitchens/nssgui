This is a setup for quickly browsing the PySimpleGUI docs locally, grouping links to related concepts across docs (tk/tcl, etc), and having a hub for workspace related documentation

Use:
- Run `python -m pip install -r requirements.txt` to use the scripts here
- Extract zipped doc files to current directory (e.g. "Extract Here")
- Optional: Pull webpages manually in a browser with "Save Page As" (Chrome is suggested for this feature), overwriting the respectively named files extracted from the zip
- Run `redirect_links.py` to redirect the links in the webpages to these local files
- First time: Run `python gen_psg_docs.py`
- After first time: Open `psg_docs.html`

Options:
- In `options.py`, which is imported into the other scripts and is gitignore'd
