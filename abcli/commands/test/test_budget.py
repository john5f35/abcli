from pony import orm
from datetime import date

from abcli.commands.budget import load_budget_yaml, evaluate_progress
from abcli.commands.test import setup_db
from abcli.utils import Date


def test_load_budget_yaml():
    yaml_text = ("date_from: 01/01/2019\n"
                 "date_to:   31/01/2019\n"
                 "items:\n"
                 "    'TestAccount:SubCateg': 123\n")
    budget = load_budget_yaml(yaml_text)

    assert budget['date_from'] == date(2019, 1, 1)
    assert budget['date_to'] == date(2019, 1, 31)
    assert budget['items'] == {
        'TestAccount:SubCateg': 123.0
    }


def test_budget_progress(tmp_path):
    db, db_file = setup_db(tmp_path)

    with orm.db_session:
        checking = db.Account(name='Checking')
        expenses = db.Account(name='Expenses')
        db.Transaction.from_posts([
            (checking, -23, Date(2019, 1, 3), Date(2019, 1, 8)),
            (expenses, 23, Date(2019, 1, 3), Date(2019, 1, 8)),
        ])
        db.Transaction.from_posts([
            (checking, -7, Date(2019, 1, 4), Date(2019, 1, 7)),
            (expenses, 7, Date(2019, 1, 4), Date(2019, 1, 7)),
        ])

    assert evaluate_progress(db, {
        'date_from': Date(2019, 1, 3),
        'date_to': Date(2019, 1, 8),
        'items': {
            'Checking': -100,
            'Expenses': 200
        }
    }, False) == [('Checking', -30.0, -100, 0.3), ('Expenses', 30.0, 200, 0.15)]
