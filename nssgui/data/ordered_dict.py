
__all__ = [
    'OrderedDict'
]

class OrderedDict:
    def __init__(self, init_dict=None) -> None:
        self.key_list = []
        self.value_list = []
        if init_dict:
            for k, v in init_dict.items():
                self.append(k, v)
    def __len__(self):
        return len(self.key_list)
    def __getitem__(self, key):
        i = self.key_list.index(key)
        return self.value_list[i]
    def __setitem__(self, key, value):
        if key in self.key_list:
            i = self.key_list.index(key)
            self.value_list[i] = value
        else:
            self.append(key, value)
    def index(self, key):
        return self.key_list.index(key)
    def get_at(self, index):
        return self.key_list[index], self.value_list[index]
    def in_keys(self, key):
        return key in self.key_list
    def in_values(self, value):
        return value in self.key_list
    def pop(self, index=None):
        if index:
            key = self.key_list.pop(index)
            value = self.value_list.pop(value)
        else:
            key = self.key_list.pop()
            value = self.value_list.pop()
        return key, value
    def prepend(self, key, value):
        self.remove(key)
        self.key_list.insert(0, key)
        self.value_list.insert(0, value)
    def append(self, key, value):
        self.remove(key)
        self.key_list.append(key)
        self.value_list.append(value)
    def _remove_duplicates(self):
        seen_keys = set()
        duplicates = []
        for i in range(len(self)):
            k = self.key_list[i]
            if k in seen_keys:
                duplicates.insert(0, i)
            else:
                seen_keys.add(k)
        for i in duplicates:
            self.key_list.pop(i)
            self.value_list.pop(i)
    def insert(self, index, key, value):
        """Insert before index"""
        self.key_list.insert(index, key)
        self.value_list.insert(index, value)
        self._remove_duplicates()
    def remove(self, key):
        if not key in self.key_list:
            return
        i_key = self.key_list.index(key)
        self.key_list.pop(i_key)
        self.value_list.pop(i_key)
    def clear(self):
        self.key_list.clear()
        self.value_list.clear()
    def insert_before_key(self, before_key, key, value):
        if not before_key in self.key_list:
            self.prepend(key, value)
            return
        i_before = self.key_list.index(before_key)
        self.insert(i_before, key, value)
    def insert_after_key(self, after_key, key, value):
        if not after_key in self.key_list:
            self.append(key, value)
        i_before = self.key_list.index(after_key) + 1
        self.insert(i_before, key, value)
    def move_forward(self, key, n=1):
        if n < 1 or not key in self.key_list:
            return
        i_key = self.key_list.index(key)
        i_insert_before = i_key - n
        if i_insert_before < 0:
            i_insert_before = 0
        value = self.value_list[i_key]
        self.remove(key)
        self.insert(i_insert_before, key, value)
    def move_back(self, key, n=1):
        if n < 1 or not key in self.key_list:
            return
        i_key = self.key_list.index(key)
        value = self.value_list[i_key]
        i_insert_before = i_key + n
        self.remove(key)
        self.insert(i_insert_before, key, value)
    def move_to_front(self, key):
        self.move_forward(key, len(self))
    def move_to_back(self, key):
        self.move_back(key, len(self))
    def items(self):
        return self.to_pairs(self)
    def keys(self):
        return self.key_list.copy()
    def values(self):
        return self.value_list.copy()
    def to_pairs(self):
        pairs = []
        for i in range(len(self)):
            pairs.append((self.key_list[i], self.value_list[i]))
        return pairs
    def load_pairs(self, pairs):
        for k, v in pairs:
            self.append(k, v)
        return self
    @classmethod
    def from_pairs(cls, pairs):
        return OrderedDict(init_dict=dict(pairs))
