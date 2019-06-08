from click.testing import CliRunner
from pony.orm import *

from abcli.main import cli
from abcli import setup_db


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