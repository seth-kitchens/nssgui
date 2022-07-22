This is a setup for quickly browsing the PySimpleGUI docs locally, grouping links to related concepts across docs (tk/tcl, etc), and having a hub for workspace related documentation

Use:
- Run `python -m pip install -r requirements.txt` to use the scripts here
- Extract zipped doc files to current directory (e.g. "Extract Here")
- Optional: Pull webpages manually, see below
- First time: Run `python gen_psg_docs.py`
- After first time: Open `psg_docs.html`

Pull webpages manually:
- In a browser (Chrome worked better than Firefox for me), save the webpages with "Save Page As...", overwriting the respective files extracted from the zip
- Run `redirect_links.py` to redirect the links in the webpages to these local files

Options:
- In `options.py`, which is imported into the other scripts and is gitignore'd
