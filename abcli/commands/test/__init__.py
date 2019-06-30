from pathlib import Path
import json
from typing import *

from click.testing import Result, CliRunner
from pony.orm import Database

from abcli.main import cli
from abcli.model import init_orm


def setup_db(tmp_path: Path):
    tmpfile = tmp_path / 'tmp.db'

    db = Database(provider='sqlite', filename=str(tmpfile), create_db=True)
    init_orm(db)
    return db, tmpfile


def invoke_cmd(db_file: Path, args: List[str]) -> Result:
    config_file = db_file.parent / 'config.json'
    with config_file.open('w', encoding='utf-8') as fp:
        json.dump({
            'db': {
                'provider': 'sqlite',
                'filename': str(db_file)
            }
        }, fp, indent=2)

    return CliRunner().invoke(cli, ['--config', str(config_file)] + args)
