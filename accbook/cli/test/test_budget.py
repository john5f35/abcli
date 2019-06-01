from pathlib import Path
import json

import click
from click.testing import CliRunner
from pony.orm import *

from accbook.common import parse_date, format_date
from accbook.cli.main import cli
from accbook.cli.test.common import setup_db

def test_import_budget(tmp_path: Path):
    db, db_file = setup_db(tmp_path)

    date_from = parse_date("01/03/2019")
    date_to = parse_date("31/03/2019")
    sample_budget = {
        "date_from": format_date(date_from),
        "date_to": format_date(date_to),
        "items": [
            {
                "account": "TestAccount",
                "amount": 500
            },
            {
                "account": "Expenses",
                "amount": 200
            }
        ]
    }
    json_file = tmp_path / "budget.json"

    with json_file.open(mode='w') as fp:
        json.dump(sample_budget, fp, indent=2, separators=",:")

    CliRunner().invoke(cli, [str(db_file), 'account', 'add', 'TestAccount'])
    CliRunner().invoke(cli, [str(db_file), 'account', 'add', 'Expenses'])
    res = CliRunner().invoke(cli, [str(db_file), 'budget', 'import', str(json_file)])
    assert res.exit_code == 0, str(res)

    with db_session:
        query = db.Budget.select(lambda b: b.date_from == date_from and b.date_to == date_to)
        assert len(query) == 1
        budget = query.first()
        assert len(budget.items) == 2
