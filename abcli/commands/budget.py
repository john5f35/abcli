import logging
import json, yaml
from pathlib import Path
from typing import *
from datetime import date

import click
from pony import orm
from tabulate import tabulate

from abcli.utils import (
    parse_date, format_monetary,
    error_exit_on_exception, AccountTree
)
from abcli.model import ACCOUNT_TYPES
from abcli.commands.transaction import get_posts_between_period
from abcli.utils.click import PathType

logger = logging.getLogger()


@click.group(__name__[__name__.rfind('.') + 1:])
def cli():
    pass


@cli.command("progress")
@click.argument("budget-yaml", type=PathType(dir_okay=False, exists=True))
@click.option("--include-nonresolved", '-i', is_flag=True, help="Include non-resolved transactions.")
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_progress(db, budget_yaml: Path, include_nonresolved: bool):
    # TODO: show in tree format, with aggregation
    # TODO: also show non-categorised accounts
    try:
        budget = load_budget_yaml(budget_yaml.read_text('utf-8'))
        format_tuples = get_format_tuples(db, budget.get('items', {}), budget['date_from'], budget['date_to'],
                      include_nonresolved)
        print(tabulate(format_tuples, tablefmt="plain", headers=('account_name', 'consumed', 'budgeted', 'progress'),
                       colalign=("left", "right", "right", "right")))
        return 0
    except yaml.YAMLError:
        raise KeyError(f"Failed to load budget YAML {budget_yaml}")


def get_format_tuples(db, budget_items: Dict[str, float], date_from: date, date_to: date, include_nonresolved: bool):
    @orm.db_session
    def _format_tree(tree):
        account_name = tree.fullname
        all_posts_in_period = get_posts_between_period(db, date_from, date_to, include_nonresolved)
        txn_sum = orm.select(p.amount for p in all_posts_in_period if p.account.name.startswith(account_name)).sum()
        if tree.amount:
            return (format_monetary(txn_sum), format_monetary(tree.amount),
                    f"{float(txn_sum) / tree.amount * 100.00:.2f}%")
        return ("", "", "")

    tuples = []
    for acctype in ACCOUNT_TYPES:
        tree = AccountTree(acctype)
        for acc_name in filter(lambda name: name.startswith(acctype), budget_items):
            tree.add(acc_name, budget_items[acc_name])

        tuples += tree.get_format_tuples(callback=_format_tree)
    return tuples


def load_budget_yaml(yaml_text: str):
    try:
        budget = yaml.full_load(yaml_text)
        budget['date_from'] = parse_date(budget['date_from'])
        budget['date_to'] = parse_date(budget['date_to'])
        items = budget.get('items', {})
        for account_name in items:
            items[account_name] = float(items[account_name])
        return budget
    except Exception:
        raise yaml.YAMLError()
