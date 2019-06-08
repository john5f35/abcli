import csv
from pathlib import Path
import datetime
import logging
from datetime import date as Date
import traceback
import sys

import click

logger = logging.getLogger()

JSON_FORMAT_DATE = '%d/%m/%Y'
JSON_FORMAT = {
    'indent': 2,
    'separators': (',', ': ')
}

FIELDS = ['date', 'amount', 'desc', 'balance', 'this', 'that', 'ref', 'tags']

def format_date(date: Date) -> str:
    return date.strftime(JSON_FORMAT_DATE)

def parse_date(date_str: str) -> Date:
    try:
        return datetime.datetime.strptime(date_str, JSON_FORMAT_DATE).date()
    except ValueError:
        raise ValueError(f"Failed to parse date '{date_str}'.")

def format_monetary(amount: float):
    return f"{'-' if amount < 0 else ''}${abs(amount):.2f}"

def load_csv(csvpath: Path) -> [dict]:
    lines = csvpath.read_text('UTF-8').strip().split('\n')
    txns = list(csv.DictReader(lines, FIELDS, restval=''))
    if txns[0]['date'] == 'date':
        # Skip header if file contains header
        txns = txns[1:]
    return txns

def this_str2dict(this_field: str, amount: float) -> dict:
    if this_field == '':
        this_field = '__this__'
    if not '{' in this_field:
        return {this_field: amount}
    if _is_valid_dictstr(this_field):
        return eval(this_field)
    return None

def _is_valid_dictstr(dictstr: str):
    try:
        d = eval(dictstr)
        assert isinstance(d, dict)
        return True
    except Exception:
        return False

def error_exit_on_exception(fnc):
    def _wrapped(*args, **kwargs):
        try:
            return fnc(*args, **kwargs)
        except Exception:
            exc_t, exc_v, tb = sys.exc_info()
            # logger.error(''.join(traceback.format_exception(exc_t, exc_v, tb)))
            try:
                logger.error(f"{exc_v.__class__.__name__}: {exc_v.args[0]}")
            except Exception:
                logger.error(f"{exc_v.__class__.__name__}")
            click.get_current_context().exit(1)
    return _wrapped

class DateType(click.ParamType):
    name = 'date'

    def convert(self, value, param, ctx):
        try:
            return parse_date(value)
        except ValueError:
            self.fail(f"Failed to parse date '{value}', must be in format '{JSON_FORMAT_DATE}'", param, ctx)