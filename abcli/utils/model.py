import datetime
from datetime import date as Date
from typing import Dict

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

    def format_string(self):
        pass
