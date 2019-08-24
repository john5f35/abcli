import logging
import json, yaml
from pathlib import Path

import click
from pony import orm
import textwrap
from tabulate import tabulate

from abcli.utils import (
    parse_date, format_date, format_monetary,
    error_exit_on_exception
)
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
    try:
        budget = load_budget_yaml(budget_yaml.read_text('utf-8'))
        progress = evaluate_progress(db, budget, include_nonresolved)
        logger.info((tabulate(
            [(n, format_monetary(s), format_monetary(a), f"{p * 100:.2f}%") for n, s, a, p in progress],
            headers=('account_name', 'consumed', 'budgeted', 'progress'))))
        return 0
    except yaml.YAMLError:
        raise KeyError(f"Failed to load budget YAML {budget_yaml}")


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


@orm.db_session
def evaluate_progress(db, budget, include_nonresolved: bool):
    progress = []
    budget_items = budget.get('items', {})
    for account_name, amount in budget_items.items():
        all_posts_in_period = get_posts_between_period(db, budget['date_from'], budget['date_to'], include_nonresolved)
        txn_sum = orm.select(p.amount for p in all_posts_in_period if p.account.name.startswith(account_name)).sum()
        progress.append((account_name, float(txn_sum), amount, (float(txn_sum) / amount)))
    return progress
