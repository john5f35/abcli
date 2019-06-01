from pathlib import Path
import json
import uuid

import click
from click.testing import CliRunner
from pony import orm

from accbook.common import parse_date, format_date, Date
from accbook.cli.main import cli
from accbook.cli.test.common import setup_db

def test_import_budget(tmp_path: Path):
    db, db_file = setup_db(tmp_path)

    date_from = parse_date("01/03/2019")
    date_to = parse_date("31/03/2019")
    accounts = ["TestAccount", "Expenses"]
    sample_budget = {
        "date_from": format_date(date_from),
        "date_to": format_date(date_to),
        "items": [
            {
                "account": accounts[0],
                "amount": 500
            },
            {
                "account": accounts[1],
                "amount": 200
            }
        ]
    }

    with orm.db_session:
        db.Account(name=accounts[0])
        db.Account(name=accounts[1])

    json_file = tmp_path / "budget.json"
    with json_file.open(mode='w') as fp:
        json.dump(sample_budget, fp, indent=2, separators=",:")


    res = CliRunner().invoke(cli, [str(db_file), 'budget', 'import', str(json_file)])
    assert res.exit_code == 0, str(res)

    with orm.db_session:
        query = db.Budget.select(lambda b: b.date_from == date_from and b.date_to == date_to)
        assert len(query) == 1
        budget = query.first()
        assert len(budget.items) == 2


def test_budget_list(tmp_path):
    db, db_file = setup_db(tmp_path)

    accounts = ["TestAccount", "Expenses"]

    with orm.db_session:
        budget = db.Budget(date_from=Date.today(), date_to=Date.today(), items=[
            db.BudgetItem(account=db.Account(name=accounts[0]), amount=1234),
            db.BudgetItem(account=db.Account(name=accounts[1]), amount=2345)
        ])

    res = CliRunner().invoke(cli, [str(db_file), 'budget', 'list'])
    assert res.exit_code == 0, str(res)

    print()
    print(res.output)


def test_budget_delete(tmp_path):
    db, db_file = setup_db(tmp_path)

    accounts = ["TestAccount", "Expenses"]

    with orm.db_session:
        account0 = db.Account(name=accounts[0])
        account1 = db.Account(name=accounts[1])
        budget = db.Budget(date_from=Date(2019, 1, 1), date_to=Date(2019, 1, 31), items=[
            db.BudgetItem(account=account0, amount=-1234),
            db.BudgetItem(account=account1, amount=2345)
        ])

    res = CliRunner().invoke(cli, [str(db_file), 'budget', 'delete', str(budget.id)])
    assert res.exit_code == 0, str(res)

    with orm.db_session:
        assert db.Budget.get(id=1) is None


def test_budget_progress(tmp_path):
    db, db_file = setup_db(tmp_path)

    accounts = ["TestAccount", "Expenses"]

    with orm.db_session:
        account0 = db.Account(name=accounts[0])
        account1 = db.Account(name=accounts[1])
        budget = db.Budget(date_from=Date(2019, 1, 1), date_to=Date(2019, 1, 31), items=[
            db.BudgetItem(account=account0, amount=-1234),
            db.BudgetItem(account=account1, amount=2345)
        ])
        db.Transaction(uid=str(uuid.uuid4()), date=Date(2019, 1, 3), posts=[
            db.Post(account=account0, amount=-23),
            db.Post(account=account1, amount=23)
        ])
        db.Transaction(uid=str(uuid.uuid4()), date=Date(2019, 1, 8), posts=[
            db.Post(account=account0, amount=-4359),
            db.Post(account=account1, amount=4359)
        ])

    res = CliRunner().invoke(cli, [str(db_file), 'budget', 'progress', str(budget.id)])
    assert res.exit_code == 0, str(res)

    print()
    print(res.output)
