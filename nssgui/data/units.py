from math import floor, log10

from nssgui.text.utils import center_decimal_string


# based on https://stackoverflow.com/questions/3410976
def round_to_n(x, n):
    if x < 0:
        return -round_to_n(-x, n)
    if x == 0:
        return 0
    return round(x, -int(floor(log10(x))) + (n - 1))


class Degree:
    
    def __init__(self, name, symbol, power=None) -> None:
        self.name = name
        self.symbol = symbol
        self.power = power
        self.conversions = {} # name -> conversion
        self.connections = {} # name -> degree
    
    def convert_to(self, value, name):
        return value * self.conversions[name]
    
    def add_conversion(self, degree, conversion, do_two_way=True):
        self.conversions[degree.name] = conversion
        self.connections[degree.name] = degree
        if do_two_way:
            degree.conversions[self.name] = (1 / conversion)
            degree.connections[self.name] = self
    
    def find_conversion(self, name_to, visited=None, current=1):
        if not visited:
            visited = set()
        if self.name in visited:
            return 0
        visited.add(self.name)
        for name, conversion in self.conversions.items():
            next_conversion = current * conversion
            if name == name_to:
                return next_conversion
            degree = self.connections[name]
            found_conversion = degree.find_conversion(
                name_to, visited.copy(), next_conversion)
            if found_conversion:
                return found_conversion
        return 0
    
    def find_and_add(self, degree):
        if degree.name in self.conversions.keys():
            return
        conversion = self.find_conversion(degree.name)
        self.add_conversion(degree, conversion)
    
    def print(self):
        print('Degree: ' + self.name)
        print('  conversions: ' + str(self.conversions))


class UnitScale:
    
    unit_scales = {}
    
    def __init__(self, unit_name, base_degree, interval=None):
        self.name = unit_name
        self.base_degree = base_degree
        self.degrees_by_name = {}
        self.degrees_by_symbol = {}
        self.symbols_by_name = {}
        self.degrees_by_name[base_degree.name] = base_degree
        self.degrees_by_symbol[base_degree.symbol] = base_degree
        self.symbols_by_name[base_degree.name] = base_degree.symbol
        self.interval = interval
        self.is_power = bool(interval)
    
    def get_degree_by_name(self, name):
        return self.degrees_by_name[name]
    
    def get_degree_by_symbol(self, symbol):
        return self.degrees_by_symbol[symbol]
    
    def get_symbol_by_name(self, name):
        return self.symbols_by_name[name]
    
    def get_name_by_symbol(self, symbol):
        for n, s in self.symbols_by_name.items():
            if symbol == s:
                return n
        return None
    
    def add_degree(self, degree):
        self.degrees_by_name[degree.name] = degree
        self.degrees_by_symbol[degree.symbol] = degree
        self.symbols_by_name[degree.name] = degree.symbol
    
    def define_power(self, degree):
        self.add_degree(degree)
    
    def connect_all(self):
        for n1, d1 in self.degrees_by_name.items():
            for n2, d2 in self.degrees_by_name.items():
                if n1 == n2:
                    continue
                d1.find_and_add(d2)

    def define_interval(self, degree_from, degree_to, interval):
        name_from = degree_from.name
        name_to = degree_to.name
        if not name_from in self.degrees_by_name.keys():
            self.add_degree(degree_from)
        if not name_to in self.degrees_by_name.keys():
            self.add_degree(degree_to)
        degree_from.add_conversion(degree_to, interval)
        self.connect_all()

    def convert_degree(self, value, d1_name, d2_name):
        if self.is_power:
            result = value
            d1 = self.degrees_by_name[d1_name]
            d2 = self.degrees_by_name[d2_name]
            p1 = d1.power
            p2 = d2.power
            if p1 < p2:
                for p in range(p1, p2):
                    result /= self.interval
            elif p1 > p2:
                for p in range(p2, p1):
                    result *= self.interval
        else:
            d1 = self.degrees_by_name[d1_name]
            result = d1.convert_to(value, d2_name)
        return result
    
    def print_degrees(self):
        for d in self.degrees_by_name.values():
            d.print()
    
    def strip_s_if_singular(self, symbol, value, decimal_digits=2):
        if round(value, decimal_digits) == 1:
            degree_name = self.get_name_by_symbol(symbol)
            if symbol.rstrip('s') == degree_name:
                return degree_name
        return symbol


class Unit:
    
    unit_scale:UnitScale = None
    
    def __init__(self,
            value,
            degree_name=None,
            degree_symbol=None,
            degree_power=None) -> None:
        if not self.unit_scale:
            self._create_unit_scale()
        self.value = value
        if degree_symbol:
            degree = self.unit_scale.get_degree_by_symbol(degree_symbol)
        elif degree_name:
            degree = self.unit_scale.get_degree_by_name(degree_name)
        elif degree_power:
            degree = self.unit_scale.get_degree_by_symbol(degree_power)
        self.degree = degree
    
    def _create_unit_scale(self):
        return
    
    def copy_from_unit(self, unit):
        self.value = unit.value
        self.degree = unit.degree
    
    def set_value(self, value):
        self.value = value
    
    def get_degree_from_any(self, degree_name=None, degree_symbol=None):
        if degree_name:
            degree = self.unit_scale.get_degree_by_name(degree_name)
        elif degree_symbol:
            degree = self.unit_scale.get_degree_by_symbol(degree_symbol)
        return degree
    
    def set_degree(self, degree_name=None, degree_symbol=None):
        degree = self.get_degree_from_any(degree_name, degree_symbol)
        self.degree = degree
    
    def get_value(self):
        return self.value
    
    def get_degree_name(self):
        return self.degree.name
    
    def get_degree_symbol(self):
        return self.degree.symbol
    
    def get_names(self):
        return list(self.unit_scale.degrees_by_name.keys())
    
    def get_symbols(self):
        return list(self.unit_scale.degrees_by_symbol.keys())
    
    def convert_to_degree(self, degree_name=None, degree_symbol=None):
        degree = self.get_degree_from_any(degree_name, degree_symbol)
        if degree.name == self.degree.name:
            return
        self.value = self.unit_scale.convert_degree(
            self.value, self.degree.name, degree.name)
        self.degree = self.unit_scale.get_degree_by_name(degree.name)
    
    def get_as_name(self, name):
        if name == self.degree.name:
            return self.value
        degree = self.unit_scale.get_degree_by_name(name)
        return self.unit_scale.convert_degree(
            self.value, self.degree.name, degree.name)
    
    def get_as_symbol(self, symbol):
        if symbol == self.degree.symbol:
            return self.value
        degree = self.unit_scale.get_degree_by_symbol(symbol)
        return self.unit_scale.convert_degree(
            self.value, self.degree.name, degree.name)
    
    def print_as_symbol(self, symbol):
        value = self.get_as_symbol(symbol)
        print(str(value) + ' ' + symbol)
    
    def find_best_accurate(self, accuracy=3):
        as_each_degree = {}
        for symbol in self.unit_scale.degrees_by_symbol.keys():
            as_each_degree[symbol] = self.get_as_symbol(symbol)
        best_vs = (None, None)
        rounded_original = round_to_n(self.value, accuracy)
        best_vs = (self.value, self.degree.symbol)
        for symbol, value in as_each_degree.items():
            if symbol == best_vs[1]:
                continue

            # default MB stored as B
            # set to 5 GB
            # saved as 5*1024*1024*1024 B
            # loaded as B, how to know to set to GB?
            # -> 5*1024*1024*1024 B
            # -> 5*1024*1024 KB
            # -> 5*1024 MB
            # -> 5 GB
            # -> 5/1024 TB
            # must: convert to B and compare as equal with accuracy given

            # must compare equal to original with rounding accuracy
            name = self.unit_scale.get_name_by_symbol(symbol)
            rounded_value = round_to_n(value, accuracy)
            converted_back = self.unit_scale.convert_degree(
                rounded_value, name, self.degree.name)
            if not round_to_n(converted_back, accuracy) == rounded_original:
                continue

            # shorter rounded value string is better
            len_value = len(str(rounded_value))
            rounded_best = round_to_n(best_vs[0], accuracy)
            len_best = len(str(rounded_best))
            if len_best < len_value:
                continue
            if len_value < len_best:
                best_vs = (value, symbol)
                continue

            # smaller whole value is better
            whole_value = int(value)
            whole_best = int(best_vs[0])
            if whole_best < whole_value:
                continue
            if whole_value < whole_best:
                best_vs = (value, symbol)
                continue

        return best_vs
    
    def find_best(self, minimum=0.5) -> tuple[str, str]:
        as_each_degree = {}
        for symbol in self.unit_scale.degrees_by_symbol.keys():
            as_each_degree[symbol] = self.get_as_symbol(symbol)
        best_vs = (self.value, self.degree.symbol)
        for symbol, value in as_each_degree.items():
        
            # at least {minimum} is better
            enough_value = (value >= minimum)
            enough_best = (best_vs[0] >= minimum)
            if enough_best and not enough_value:
                continue
            if enough_value and not enough_best:
                best_vs = (value, symbol)
                continue

            # smaller whole value is better
            whole_value = int(value)
            whole_best = int(best_vs[0])
            if whole_best < whole_value:
                continue
            if whole_value < whole_best:
                best_vs = (value, symbol)
                continue

        return best_vs
    
    def get_best(self, decimal_digits=2, minimum=0.5, sep=' ') -> str:
        value, symbol = self.find_best(minimum)
        if decimal_digits:
            value = round(value, decimal_digits)
        value_string = str(value)
        symbol = self.unit_scale.strip_s_if_singular(symbol, value)
        if value:
            value_string = value_string.rstrip('0').rstrip('.')
        return value_string + sep + symbol
    
    def get_best_accurate(self,
            accuracy=3,
            do_round=True,
            center_decimal=False,
            sep=' ') -> str:
        value, symbol = self.find_best_accurate(accuracy)
        if do_round:
            value = round_to_n(value, accuracy)
        value_string = str(value)
        if center_decimal:
            center_decimal_string(value_string, accuracy)
        symbol = self.unit_scale.strip_s_if_singular(symbol, value)
        if value:
            value_string = value_string.rstrip('0').rstrip('.')
        return value_string + sep + symbol
    
    def print_best(self):
        print(self.get_best())
    
    def convert_to_best(self, minimum=1.0):
        value, symbol = self.find_best(minimum)
        self.convert_to_degree(degree_symbol=symbol)
    
    def convert_to_best_accurate(self, accuracy=3):
        value, symbol = self.find_best_accurate(accuracy)
        self.convert_to_degree(degree_symbol=symbol)


class TimeStandard(Unit):
    
    SECOND = 'second'
    MINUTE = 'minute'
    HOUR = 'hour'
    DAY = 'day'
    WEEK = 'week'
    MONTH = 'month'
    YEAR = 'year'

    def __init__(self,
            value,
            degree_name=None,
            degree_symbol=None,
            degree_power=None) -> None:
        super().__init__(value, degree_name, degree_symbol, degree_power)
    
    def _create_unit_scale(self):
        unit_name = 'time'

        degree_second = Degree(TimeStandard.SECOND, 'secs')
        degree_minute = Degree(TimeStandard.MINUTE, 'mins')
        degree_hour = Degree(TimeStandard.HOUR, 'hours')
        degree_day = Degree(TimeStandard.DAY, 'days')
        degree_week = Degree(TimeStandard.WEEK, 'weeks')
        degree_month = Degree(TimeStandard.MONTH, 'months')
        degree_year = Degree(TimeStandard.YEAR, 'years')

        unit_scale = UnitScale(unit_name, degree_second)
        unit_scale.define_interval(degree_minute, degree_second, 60)
        unit_scale.define_interval(degree_hour, degree_minute, 60)
        unit_scale.define_interval(degree_day, degree_hour, 24)
        unit_scale.define_interval(degree_week, degree_day, 7)
        unit_scale.define_interval(degree_year, degree_day, 365.25)
        unit_scale.define_interval(degree_year, degree_month, 12)

        TimeStandard.unit_scale = unit_scale
Time = TimeStandard


class DataBytes(Unit):

    BYTE = B = 'byte'
    KILOBYTE = KB = 'kilobyte'
    MEGABYTE = MB = 'megabyte'
    GIGABYTE = GB = 'gigabyte'
    TERABYTE = TB = 'terabyte'

    def __init__(self,
            value,
            degree_name=None,
            degree_symbol=None,
            degree_power=None) -> None:
        super().__init__(value, degree_name, degree_symbol, degree_power)
    
    def _create_unit_scale(self):
        unit_name = 'bytes'
        interval = 1024
        degree_byte = Degree(DataBytes.BYTE, 'B', 0)
        
        unit_scale = UnitScale(unit_name, degree_byte, interval)
        unit_scale.define_power(Degree(DataBytes.KILOBYTE, 'KB', 1))
        unit_scale.define_power(Degree(DataBytes.MEGABYTE, 'MB', 2))
        unit_scale.define_power(Degree(DataBytes.GIGABYTE, 'GB', 3))
        unit_scale.define_power(Degree(DataBytes.TERABYTE, 'TB', 4))
        
        DataBytes.unit_scale = unit_scale
Data = DataBytes
Bytes = DataBytes
