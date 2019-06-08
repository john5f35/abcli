import logging
import json

import click
from pony import orm
import textwrap
from tabulate import tabulate

from abcli.utils import (
    parse_date, format_date, format_monetary,
    error_exit_on_exception
)

logger = logging.getLogger()


@click.group(__name__[__name__.rfind('.') + 1:])
def cli():
    pass


@cli.command("import")
@click.argument("budget-json-path", type=click.Path(exists=True, dir_okay=False))
@click.pass_obj
@orm.db_session
@error_exit_on_exception
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


@cli.command("delete")
@click.argument("budget-id", type=click.INT)
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_delete(db, budget_id: int):
    try:
        db.Budget[budget_id].delete()
        logger.info(f"Budget {budget_id} deleted.")
        return 0
    except orm.ObjectNotFound:
        raise KeyError(f"Budget with id {budget_id} not found")


@cli.command("list")
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_list(db):
    query = db.Budget.select().order_by(db.Budget.date_from)

    table = [[b.id, format_date(b.date_from), format_date(b.date_to)] for b in query]

    logger.info(textwrap.indent(tabulate(table, headers=('id', 'date_from', 'date_to')), ""))
    return 0


@cli.command("progress")
@click.argument("budget-id", type=click.INT)
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_progress(db, budget_id: int):
    try:
        budget = db.Budget[budget_id]
        progress = _evaluate_progress(db, budget)
        logger.info((tabulate(
            [(n, format_monetary(s), format_monetary(a), f"{p * 100:.2f}%") for n, s, a, p in progress],
            headers=('account_name', 'consumed', 'budgeted', 'progress'))))
        return 0
    except orm.ObjectNotFound:
        raise KeyError(f"Budget with id {budget_id} not found.")


@orm.db_session
def _evaluate_progress(db, budget):
    progress = []
    for item in budget.items:
        account = item.account
        amount = item.amount
        txn_sum = orm.select(p.amount for p in db.Post
                             if p.account.name.startswith(account.name) and
                             (budget.date_from <= p.transaction.date and p.transaction.date <= budget.date_to)) \
                      .sum()
        progress.append((account.name, txn_sum, amount, txn_sum / amount))
    return progress
