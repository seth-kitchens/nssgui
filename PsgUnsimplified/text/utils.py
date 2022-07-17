from typing import Iterable
import math


__all__ = [
    'center_decimal_string',
    'TableList',
    'PrintColumn'
]


def center_decimal_string(s, side, lpad=' ', rpad='0'):
    if '.' not in s:
        s = s.rjust(side, ' ') + ' ' * (side + 1)
    else:
        parts = s.split('.')
        s = parts[0].rjust(side, lpad) + '.' + parts[1].ljust(side, rpad)
    return s


class TableList:

    def __init__(self, sep='', sep_before_indices=[], field_border_l='[', field_border_r=']'):
        """
        ---
        Add rows with an equal number of fields, then print/get them as a
        formatted table of columns with equal length
        
        Usage:
          tl = TableList()
          tl.add_row(...), tl.add_row(...), ...
          tl.print() OR tl.get_formatted_rows()
        ---
        Args:
            sep (default=''): inserted between fields.
            sep_before_indices (default=[]): if given, only places sep before these indices.
            field_border_l (default='['): prepended to fields.
            field_border_r (default=']'): appended to fields.
        """
        self.sep = sep
        self.sep_before_indices = sep_before_indices # list of indices, if len>0 places sep only before these
        self.field_border_l = field_border_l
        self.field_border_r = field_border_r
        self.rows:list[list[str]] = [] # list of rows, each row is a list of fields

    def add_row(self, row: list):
        if self.rows and len(row) != len(self.rows[0]):
            expected = len(self.rows[0])
            actual = len(row)
            raise Exception('Bad Parameter',
                'Expected row of length {}, received row of length {}'.format(expected, actual))
        self.rows.append(row)
    
    def empty_row_len(self):
        num_fields = len(self.rows[0])
        sep_len = len(self.sep)
        if self.sep_before_indices:
            seps_len = sep_len * len(self.sep_before_indices)
        else:
            seps_len = sep_len * (num_fields - 1)
        lr_border_len = len(self.field_border_l) + len(self.field_border_r)
        borders_len = lr_border_len * num_fields
        return seps_len + borders_len

    def _trim__find_to_trim(self, max_table_width):
        empty_row_len = self.empty_row_len()
        max_lens = self.find_max_lens()
        current_table_len = empty_row_len + sum(max_lens)
        return current_table_len - max_table_width

    def trim_fields(self, max_table_width, fields_to_trim:list[tuple[int, int]]=None):
        """
        Make table fit into a max width by trimming fields
        fields_to_trim: (field_index, min_width)
        Only trims fields listed, in order listed, down to at most min_width,
            until max_table_width is achieved.
        Trims each field as much as possible before moving to next field.
        Make multiple calls for even trimming
        """
        if not self.rows:
            return
                
        num_fields = len(self.rows[0])

        max_lens = self.find_max_lens()
        total_to_trim = self._trim__find_to_trim(max_table_width)
        if total_to_trim < 1:
            return
        new_max_lens = max_lens.copy()
        for i_field, min_field_width in fields_to_trim:
            to_trim = max_lens[i_field] - min_field_width
            if to_trim > total_to_trim:
                to_trim = total_to_trim
            new_max_lens[i_field] -= to_trim
            total_to_trim -= to_trim
            if total_to_trim < 1:
                break
        for row in self.rows:
            for i_field in range(num_fields):
                max_len = new_max_lens[i_field]
                row[i_field] = row[i_field][:max_len]
    
    def trim_longest(self, max_table_width):
        max_lens = self.find_max_lens()
        to_trim = self._trim__find_to_trim(max_table_width)
        if to_trim <= 0:
            return

        num_fields = len(self.rows[0])

        longest = 0
        for i in range(len(max_lens)):
            if max_lens[i] > longest:
                longest = max_lens[i]
        max_col = longest
        current_trim = 0
        while current_trim < to_trim:
            max_col -= 1
            current_trim = 0
            for max in max_lens:
                if max > max_col:
                    current_trim += max - max_col
        for row in self.rows:
            for i_field in range(num_fields):
                if len(row[i_field]) > max_col:
                    row[i_field] = row[i_field][:max_col]

    def find_max_lens(self):
        num_fields = len(self.rows[0])
        for row in self.rows:
            if len(row) != num_fields:
                raise Exception(
                    'Rows Uneven', 'Expected: {}, Received: {}'.format(len(num_fields), len(row)))
        max_lens = []
        for i in range(num_fields):
            max_lens.append(0)
        for row in self.rows:
            for i in range(num_fields):
                length = len(row[i])
                if (length > max_lens[i]):
                    max_lens[i] = length
        return max_lens

    def format_table(self):
        num_fields = len(self.rows[0])
        max_lens = self.find_max_lens()

        for row in self.rows:
            for i_field in range(num_fields):
                field = row[i_field].ljust(max_lens[i_field])

                # set sep to use
                if len(self.sep_before_indices):
                    sep = self.sep if i_field in self.sep_before_indices else ''
                else:
                    sep = self.sep if i_field > 0 else ''
                
                row[i_field] = sep + self.field_border_l + field + self.field_border_r

    def get_formatted_rows(self) -> list:
        self.format_table()
        row_strings = []
        for row in self.rows:
            row_strings.append(''.join(row))
        return row_strings

    def print(self):
        rows = self.get_formatted_rows()
        for row in rows:
            print(row)


cmd_width = 120


class PrintColumn:

    def __init__(self, num_fields=1) -> None:
        self.rows = []
        self.num_fields = num_fields if num_fields > 0 else 0

    def __getitem__(self, index):
        return self.rows[index]

    def __setitem__(self, index, value):
        self.rows[index] = value

    def add_row(self, row):
        if self.num_fields:
            fields = []
            for field in row:
                fields.append(str(field))
            self.rows.append(fields)
        else:
            self.rows.append(str(row))

    def add_rows(self, rows):
        for row in rows:
            if isinstance(row, Iterable) and not isinstance(row, str):
                self.add_row(row)
            else:
                self.add_row([row])

    def add_blank_row(self):
        row = []
        for i in range(self.num_fields):
            row.append('')
        self.add_row(row)

    def add_dict(self, d):
        for k, v in d.items():
            self.add_row([k, v])

    def print(self):
        for row in self.rows:
            print(row)

    def print_section(columns: list, max_table_width=cmd_width, sep=' | '):
        """
        ---
        Print PrintColumn objects side-by-side
        
        ---
        Args:
            columns: list of PrintColumn objects
        """
        longest_col = 0
        for col in columns:
            if len(col.rows) > longest_col:
                longest_col = len(col.rows)
        for col in columns:
            for i in range(longest_col - len(col.rows)):
                col.add_blank_row()

        column_count = len(columns)
        row_count = len(columns[0].rows)
        tl_rows = []
        for i_row in range(row_count):
            tl_row = []
            for i_col in range(column_count):
                if columns[i_col].num_fields:
                    for field in columns[i_col][i_row]:
                        tl_row.append(field)
                else:
                    tl_row.append(columns[i_col][i_row])
            tl_rows.append(tl_row)
        
        # Create Borders between columns
        field_counts = []
        for pcol in columns:
            if pcol.num_fields:
                field_counts.append(len(pcol.rows[0]))
            else:
                field_counts.append(1)
        sep_before_indices = []
        i = 0
        for field_count in field_counts:
            i += field_count
            sep_before_indices.append(i)
        sep_before_indices.pop()
        
        # format columns
        tl = TableList(field_border_l='', field_border_r='', sep=sep, 
            sep_before_indices=sep_before_indices)
        for tl_row in tl_rows:
            tl.add_row(tl_row)
        tl.trim_longest(max_table_width)
        tl.print()

    def split_print_section(self,
            column_count,
            max_table_width=cmd_width,
            split_type='alternate',
            sep=' | '):
        """
        ---
        Split the column into multiple columns, then print them side-by-side
        
        ---
        Args:
            column_count: number of columns to split into
            split_type: alternate/divide
                alternate: every other row
                divide: divide evenly
        """
        columns = []
        row_count = len(self.rows)

        # create PrintColumns to split into
        for i in range(column_count):
            columns.append(PrintColumn(num_fields=self.num_fields))
            current = 0
            r = range(row_count)
        
        # split columns
        if split_type == 'alternate':
            for i in r:
                columns[i % column_count].add_row(self.rows[i])
                current = (current + 1) % column_count
        elif split_type == 'divide':
            rows_per_col = math.ceil(row_count / column_count)
            for i in r:
                columns[int(i / rows_per_col)].add_row(self.rows[i])
        
        return PrintColumn.print_section(columns, max_table_width=max_table_width, sep=sep)
