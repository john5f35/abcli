import datetime
import sys
from datetime import date as Date
from typing import *
from collections import OrderedDict

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
    def __init__(self, segname: str, parent: 'AccountTree' = None):
        self.segname = segname
        self.amount = 0
        self._parent = parent
        self._children: OrderedDict[str, AccountTree] = OrderedDict()

    def add(self, name: str, amount: float):
        segname, _, rest = name.partition(':')
        if segname != self.segname:
            raise KeyError(f"{name} does not start with {self.segname}")

        self.amount += amount
        if rest:
            child_seg = rest.partition(':')[0]
            if child_seg not in self._children:
                self._children[child_seg] = AccountTree(child_seg, self)
                self._children.move_to_end(child_seg)
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
        result = []
        tree_str = self._get_prefix() + self.segname
        amount_str = format_monetary(self.amount)
        result.append((tree_str, amount_str))
        for child_seg in self._children:
            result += self._children[child_seg].get_format_tuples()
        return result

    def _get_is_last_childs(self) -> List[bool]:
        if self._parent is None:
            return [None]
        is_last_child = list(self._parent._children.keys())[-1] == self.segname
        return self._parent._get_is_last_childs() + [is_last_child]

    def _get_prefix(self):
        is_last_childs = self._get_is_last_childs()
        prefix = ""
        for parent_is_last_child in is_last_childs[:-1]:
            if parent_is_last_child is None:
                prefix += ""
            elif parent_is_last_child:
                prefix += ' ' * 4
            else:
                prefix += _SEG_PARENT_CONT + ' ' * 3

        this_is_last_child = is_last_childs[-1]
        if this_is_last_child is None:
            prefix += ""
        elif this_is_last_child:
            prefix += _SEG_CHILD_LAST + _SEG_DASH * 2 + ' '
        else:
            prefix += _SEG_CHILD_CONT + _SEG_DASH * 2 + ' '
        return prefix

    def format_string(self, tabular=True):
        format_tuples = self.get_format_tuples()
        if tabular:
            return tabulate(format_tuples, tablefmt="plain", colalign=("left", "right"))
        else:
            format_strings = map(lambda tup: "{} ({})".format(*tup), format_tuples)
            return '\n'.join(format_strings)


_SEG_CHILD_LAST = '└'
_SEG_CHILD_CONT = '├'
_SEG_PARENT_CONT = '│'
_SEG_DASH = '─'
