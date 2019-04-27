import os, sys
import logging
from pathlib import Path
import json

import click


root_logger = logging.getLogger()

def set_root_logger_level(cli_level):
    default_level = "WARNING"
    env_level = os.environ.get("LOG_LEVEL", "NOTSET")
    root_logger.setLevel(default_level)
    root_logger.setLevel(env_level)
    root_logger.setLevel(cli_level)

    logging.basicConfig(format="[%(level)s] %(message)s")


@click.group()
@click.option("--log-level", type=click.Choice([logging._nameToLevel.keys()]),
        help="Set the root logger level")
@click.argument("db", type=click.Path(),
        help="Database. Currently a JSON file.")
@click.pass_context
def entry_point(ctx, log_level, db):
    set_root_logger_level(log_level)

    db_path = Path(db)
    root_logger.info("loading db...")
    try:
        with db_path.open("r") as fp:
            db_json = json.load(fp)
    except FileNotFoundError:
        root_logger.warning(f"Database file {db_path} not found; creating a new one.")
        db_path.touch()
        db_json = {}
    except json.JSONDecodeError:
        root_logger.error(f"Failed to load JSON db at {db_path}: invalid JSON.")
        ctx.exit(1)

    ctx.obj = db_json
