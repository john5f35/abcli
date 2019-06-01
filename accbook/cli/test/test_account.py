from pathlib import Path

import click
from click.testing import CliRunner
from pony.orm import *

from accbook.common import parse_date
from accbook.cli.main import cli
from accbook.cli.model import init_orm
from accbook.cli.test.common import setup_db


def test_add_account(tmp_path):
    db, db_file = setup_db(tmp_path)

    res = CliRunner().invoke(cli, [str(db_file), 'account', 'add', 'TestAccount'])
    assert res.exit_code == 0, str(res)

    with db_session:
        account = db.Account['TestAccount']
        assert account.name == 'TestAccount'

def test_add_account_fail_already_exists(tmp_path):
    db, db_file = setup_db(tmp_path)

    res = CliRunner().invoke(cli, [str(db_file), 'account', 'add', 'TestAccount'])
    assert res.exit_code == 0, str(res)

    res = CliRunner().invoke(cli, [str(db_file), 'account', 'add', 'TestAccount'])
    assert res.exit_code == 1, str(res)

    assert "Account 'TestAccount' already exists" in res.output