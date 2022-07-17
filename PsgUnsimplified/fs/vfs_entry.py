import os
from os.path import normpath


class VFSEntry:
    
    class entry_types:
        DIR = 'dir'
        FILE = 'file'
    
    def __init__(self, init_path):
        self.path:str = normpath(init_path)
        self.parent:VFSEntry = None
        self.children:list[VFSEntry] = []
        self.entry_type = VFSEntry.path_to_type(self.path)
        self.size:int = 0
        self.name:str = os.path.basename(self.path)
    
    def path_to_type(path):
        if os.path.isdir(path):
            return VFSEntry.entry_types.DIR
        elif os.path.isfile(path):
            return VFSEntry.entry_types.FILE
        return ''
    
    @classmethod
    def from_parent(cls, parent, init_path):
        child = VFSEntry(init_path)
        parent.connect_child()
        return child
    
    def connect_child(self, child):
        child.parent = self
        self.children.append(child)
    
    def find_children_where(self,
            func_cond, 
            func_found=None,
            recurse=True, 
            include_self=True):
        found = []
        if include_self and func_cond(self):
            if func_found:
                func_found(self)
            if not recurse:
                return found
        children = self.children.copy()
        for child in children:
            found_child = child.find_children_where(
                func_cond, func_found, recurse)
            found.extend(found_child)
        return found
    
    def find_parents_where(self,
            func_cond,
            func_found=None,
            recurse=True, 
            include_self=True):
        found = []
        if include_self and func_cond(self):
            found.append(self)
            if func_found:
                func_found(self)
            if not recurse:
                return found
        if self.parent:
            found_parent = self.parent.find_parents_where(
                func_cond, func_found, recurse)
            found.extend(found_parent)
        return found
    
    def for_children(self,
            func, 
            args=None,
            kwargs=None, 
            recurse=True,
            include_self=False,
            return_nones=False):
        if args == None:
            args = []
        if kwargs == None:
            kwargs = {}
        rvs = []
        if include_self:
            rv = func(self, *args, **kwargs)
            if rv != None or return_nones:
                rvs.append(rv)
        for child in self.children:
            rv = func(child, *args, **kwargs)
            if rv != None or return_nones:
                rvs.append(rv)
        if recurse:
            for child in self.children:
                child_rvs = child.for_children(func,
                    args=args, kwargs=kwargs, recurse=recurse,
                    include_self=False, return_nones=return_nones)
                rvs.extend(child_rvs)
        return rvs
    
    def for_parents(self,
            func,
            args=None, 
            kwargs=None,
            recurse=True,
            include_self=True,
            return_nones=False):
        if args == None:
            args = []
        if kwargs == None:
            kwargs = {}
        rvs = []
        if include_self:
            rv = func(self)
            if rv != None or return_nones:
                rvs.append(rv)
        if recurse:
            parent_rvs = self.parent.for_parents(func,
                recurse=recurse, include_self=False,
                return_nones=return_nones)
            rvs.extend(parent_rvs)
        return rvs
    
    def print_tree(self, indent=0):
        print(' ' * indent + self.name)
        for child in self.children:
            child.print_tree(indent+2)
    
    def delete_self(self):
        if self.parent:
            self.parent.children.remove(self)
        for child in self.children:
            child.parent = None
        self.children.clear()
        self.path = ''
        self.parent = None
        self.entry_type = ''
        self.size = 0
        self.name = ''
        return
    
    def delete_all(self):
        all = self.collect_entries()
        for entry in all:
            entry.delete_self()
        return
    
    def get_type_symbol(self):
        if self.is_dir():
            return 'DIR'
        return ''
    
    def adopt_orphan(self, orphan):
        pass
    
    def create_children(self, orphans:dict=None):
        if not self.is_dir():
            return
        if orphans == None:
            orphans = {}
        current_path = self.path
        fs_child_names = os.listdir(current_path)
        children_created = []
        for fs_child_name in fs_child_names:
            child_path = os.path.normpath(
                os.path.join(current_path, fs_child_name))
            if child_path in orphans:
                self.children.append(orphans[child_path])
                self.connect_child(orphans[child_path])
                orphans.pop(child_path)
            else:
                children_created.append(
                    self.__class__.from_parent(self, child_path))
        for child in children_created:
            if child.is_dir():
                child.create_children()
        return
    
    def is_file(self):
        if self.entry_type == self.entry_types.FILE:
            return True
        return False
    
    def is_dir(self):
        if self.entry_type == self.entry_types.DIR:
            return True
        return False
    
    def is_root(self):
        if self.parent == None:
            return True
        return False

    def get_path(self):
        return self.path
    
    def get_all_paths(self):
        paths = []
        paths.append(self.path)
        for child in self.children:
            child_paths = child.get_all_paths()
            paths.extend(child_paths)
        return paths

    def get_children(self) -> list:
        return self.children.copy()

    def collect_entries(self, entry_set=None) -> set:
        if not entry_set:
            entry_set = set()
        entry_set.add(self)
        for child in self.children:
            child.collect_entries(entry_set)
        return entry_set

    def get_size(self):
        return self.size

    def calc_size(self):
        if self.is_file():
            stat_result = os.stat(self.path)
            self.size = stat_result.st_size
        elif self.is_dir():
            self.size = 0
            for child in self.children:
                self.size += child.calc_size()
        return self.size
    
    def calc_all(self):
        """
        Meant to be overridden with subclass-specific calculated variables
        """
        self.calc_size()