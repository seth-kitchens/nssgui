from psgu.fs.vfs_entry import VFSEntry

class VirtualFS:

    def __init__(self):
        self.root_entries = {}
        self.all_entries = {}
    
    def for_entries(self, func, return_nones=False):
        """func(entry) called on every entry. rv's returned as list"""
        rvs = []
        for entry in self.all_entries.values():
            rv = func(entry)
            if rv != None or return_nones:
                rvs.append(func(entry))
        return rvs
    
    def for_roots(self, func, return_nones=False):
        """func(entry) called on every root. rv's returned as list"""
        rvs = []
        for entry in self.root_entries.values():
            rv = func(entry)
            if rv != None or return_nones:
                rvs.append(func(entry))
        return rvs
    
    def get_root_folder_count(self):
        return len(self.for_roots(VFSEntry.is_dir))
    
    def get_root_file_count(self):
        return len(self.for_roots(VFSEntry.is_file))
VFS = VirtualFS
