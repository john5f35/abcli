import os
import logging
from pathlib import Path
import json

import click
from pony.orm import Database, set_sql_debug

from abcli.model import init_orm
from abcli.commands import init_command_groups
from abcli.utils import PathType, error_exit_on_exception


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
@click.option("--config", "-c", "config_path", type=PathType(), default=Path("./config.json"),
        help="Path to config JSON file")
@click.pass_context
@error_exit_on_exception
def cli(ctx: click.Context, log_level, config_path: Path):
    set_root_logger_level(log_level)

    if ctx.invoked_subcommand != 'csv':  # Doesn't need to initialise the db
        with config_path.open('r') as fp:
            config = json.load(fp)
            ctx.meta.update(config)

        db = Database(**config['db'])
        init_orm(db)
        ctx.obj = db


init_command_groups(cli)

# TODO: turn this cli into repl using https://github.com/click-contrib/click-repl