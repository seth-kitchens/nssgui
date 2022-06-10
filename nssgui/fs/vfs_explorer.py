from nssgui.fs.vfs import VFS

class VFSExplorer:
    def __init__(self, vfs, script_data):
        self.current_dir_entry = None
        self.current_dir_children = []
        self.vfs:VFS = vfs
        self.script_data = script_data

    def sort_children(self):
        folders = []
        files = []
        for child in self.current_dir_children:
            if child.is_dir():
                folders.append(child)
            else:
                files.append(child)
        
        def compare_children(e):
            return e.get_included_size()
        folders.sort(key=compare_children, reverse=True)
        files.sort(key=compare_children, reverse=True)
        self.current_dir_children = folders + files
    
    def refresh_current_dir(self):
        if self.current_dir_entry == None:
            children = self.vfs.get_root_entries()
        else:
            children = self.current_dir_entry.get_children()
        self.current_dir_children = children
        self.sort_children()
    
    # Navigation
    
    def open_folder(self, path):
        folder_entry = self.vfs.find_entry(path)
        if not folder_entry.is_dir():
            return
        self.current_dir_entry = folder_entry
        self.refresh_current_dir()
    def exit_folder(self):
        if self.current_dir_entry == None:
            return
        if self.current_dir_entry.is_root():
            self.current_dir_entry = None
        else:
            self.current_dir_entry = self.current_dir_entry.parent
        self.refresh_current_dir()
    def exit_to_root(self):
        self.current_dir_entry = None
        self.refresh_current_dir()

        


