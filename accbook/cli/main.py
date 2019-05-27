import os, sys
import logging
from pathlib import Path
import json

import click
import coloredlogs
from pony.orm import Database, set_sql_debug

from accbook.cli.model import init_orm
from accbook.cli.commands import init_command_groups


def set_root_logger_level(cli_level):
    root_logger = logging.getLogger()
    env_level = os.environ.get("LOG_LEVEL", "INFO")
    root_logger.setLevel(env_level)
    if cli_level:
        root_logger.setLevel(cli_level)

    if root_logger.getEffectiveLevel() == logging.DEBUG:
        set_sql_debug(True)


@click.group()
@click.option("--log-level", type=click.Choice([str(k) for k in logging._nameToLevel.keys()]), default=None,
        help="Set the root logger level")
@click.argument("db_path", type=click.Path())
@click.pass_context
def cli(ctx, log_level, db_path):
    set_root_logger_level(log_level)

    db = Database(provider='sqlite', filename=os.path.abspath(db_path), create_db=True)
    init_orm(db)
    ctx.obj = db


init_command_groups(cli)

if __name__ == '__main__':
    globals()['cli']()

# TODO: turn this cli into repl using https://github.com/click-contrib/click-repl