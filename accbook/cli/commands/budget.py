import logging
import datetime
import json

import click
from pony import orm
import textwrap
from tabulate import tabulate

from accbook.common import (
    parse_date, format_date, JSON_FORMAT_DATE,
    error_exit_on_exception
)

logger = logging.getLogger()

@click.group(__name__[__name__.rfind('.')+1:])
def cli():
    pass

@cli.command("import")
@click.argument("budget-json-path", type=click.Path(exists=True, dir_okay=False))
@click.pass_obj
@orm.db_session
def cmd_import(db, budget_json_path: str):
    with open(budget_json_path, "r") as fp:
        budget_json = json.load(fp)

    date_from = parse_date(budget_json['date_from'])
    date_to = parse_date(budget_json['date_to'])

    # Construct BudgetItems
    budget_items = []
    for item_json in budget_json['items']:
        account_name = item_json['account']
        if db.Account.get(name=account_name) is None:
            raise KeyError(f"Account {account_name} not found!")
        account = db.Account[account_name]
        budget_items.append(db.BudgetItem(account=account, amount=item_json['amount']))

    budget = db.Budget(date_from=date_from, date_to=date_to, items=budget_items)
    logger.info(f"Added budget ({budget.id})")
    return 0

@cli.command("list")
@click.pass_obj
@orm.db_session
def cmd_list(db):
    query = db.Budget.select(lambda b: True).order_by(db.Budget.date_from)

    table = [[b.id, format_date(b.date_from), format_date(b.date_to)] for b in query]

    logger.info(textwrap.indent(tabulate(table, headers=('id', 'date_from', 'date_to'), tablefmt="plain"), ""))