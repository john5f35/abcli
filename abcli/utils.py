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


def format_date(date: Date) -> str:
    return date.strftime(JSON_FORMAT_DATE)


def parse_date(date_str: str) -> Date:
    try:
        return datetime.datetime.strptime(date_str, JSON_FORMAT_DATE).date()
    except ValueError:
        raise ValueError(f"Failed to parse date '{date_str}'.")


def format_monetary(amount: float):
    return f"{'-' if amount < 0 else ''}${abs(amount):.2f}"


def error_exit_on_exception(fnc):
    def _wrapped(*args, **kwargs):
        try:
            return fnc(*args, **kwargs)
        except Exception:
            # raise
            exc_t, exc_v, tb = sys.exc_info()
            logger.error(''.join(traceback.format_exception(exc_t, exc_v, tb)))
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


class PathType(click.Path):
    name = 'path'

    def convert(self, value, param, ctx):
        try:
            return Path(value)
        except ValueError:
            self.fail(f"Failed to construct pathlib.Path object from '{value}.'", param, ctx)
