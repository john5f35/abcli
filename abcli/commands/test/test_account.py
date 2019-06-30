from pony.orm import *

from abcli.commands.test import setup_db, invoke_cmd


def test_add_account(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp('test_add_account')
    print(tmp_path)
    db, db_file = setup_db(tmp_path)

    res = invoke_cmd(db_file, ['account', 'add', 'TestAccount'])
    assert res.exit_code == 0, str(res)

    with db_session:
        account = db.Account['TestAccount']
        assert account.name == 'TestAccount'


def test_add_account_fail_already_exists(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp('test_add_account_fail_already_exists')
    print(tmp_path)
    db, db_file = setup_db(tmp_path)

    res = invoke_cmd(db_file, ['account', 'add', 'TestAccount'])
    assert res.exit_code == 0, str(res)

    res = invoke_cmd(db_file, ['account', 'add', 'TestAccount'])
    assert res.exit_code == 1, str(res)

    assert "Account 'TestAccount' already exists" in res.output