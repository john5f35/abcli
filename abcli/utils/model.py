import datetime
from datetime import date as Date
from typing import *

from tabulate import tabulate

JSON_FORMAT_DATE = '%d/%m/%Y'


def format_date(date: Date) -> str:
    return date.strftime(JSON_FORMAT_DATE)


def parse_date(date_str: str) -> Date:
    try:
        return datetime.datetime.strptime(date_str, JSON_FORMAT_DATE).date()
    except ValueError:
        raise ValueError(f"Failed to parse date '{date_str}'.")


def format_monetary(amount: float):
    return f"{'-' if amount < 0 else ''}${abs(amount):.2f}"


class AccountTree:
    def __init__(self, segname: str):
        self.segname = segname
        self.amount = 0
        self._children: Dict[str, AccountTree] = {}

    def add(self, name: str, amount: float):
        segname, _, rest = name.partition(':')
        if segname != self.segname:
            raise KeyError(f"{name} does not start with {self.segname}")

        self.amount += amount
        if rest:
            child_seg = rest.partition(':')[0]
            if not child_seg in self._children:
                self._children[child_seg] = AccountTree(child_seg)
            self._children[child_seg].add(rest, amount)

    def get(self, name: str):
        segname, _, rest = name.partition(':')
        if segname != self.segname:
            return None

        if not rest:
            return self
        child_seg = rest.partition(':')[0]
        return self._children[child_seg].get(rest)

    def get_format_tuples(self) -> List[Tuple[str, str]]:
        def _get_format_tuples(format_info):
            segname, amount, level, is_last_child = format_info
            prefix = _get_indent_prefix(level, is_last_child)
            tree_str = prefix + segname
            amount_str = format_monetary(amount)
            return tree_str, amount_str

        def _get_indent_prefix(level, is_last_child):
            if level == 0:
                return ""
            if level == 1:
                return (_SEG_CHILD_LAST if is_last_child else _SEG_CHILD_CONT) + _SEG_DASH * 2 + ' '
            return _SEG_PARENT_CONT + ' ' * 3 + _get_indent_prefix(level - 1, is_last_child)

        format_info = self._dfs(level=0, last_child=False)
        format_tuples = list(map(_get_format_tuples, format_info))
        return format_tuples

    def format_string(self, tabular=True):
        format_tuples = self.get_format_tuples()
        if tabular:
            return tabulate(format_tuples, tablefmt="plain", colalign=("left", "right"))
        else:
            format_strings = map(lambda tup: "{} ({})".format(*tup), format_tuples)
            return '\n'.join(format_strings)

    def _dfs(self, level: int, last_child: bool) -> List[Tuple[str, float, int, bool]]:
        tuples = [(self.segname, self.amount, level, last_child)]
        for idx, name in enumerate(self._children):
            child = self._children[name]
            tuples += child._dfs(level + 1, idx == len(self._children) - 1)
        return tuples


_SEG_CHILD_LAST = '└'
_SEG_CHILD_CONT = '├'
_SEG_PARENT_CONT = '│'
_SEG_DASH = '─'
