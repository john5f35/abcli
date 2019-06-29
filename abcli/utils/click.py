from pathlib import Path
import logging
import traceback
import sys

import click

from abcli.utils.model import parse_date, JSON_FORMAT_DATE

logger = logging.getLogger()


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
