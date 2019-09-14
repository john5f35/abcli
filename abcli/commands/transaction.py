import logging
import csv
from typing import *
import uuid
from pathlib import Path
from collections import defaultdict
from datetime import datetime as DateTime
import calendar

import click
from pony import orm
import textwrap
import tabulate as tabulate_mod
from tabulate import tabulate

from abcli.utils import (
    Date, format_date, parse_date, format_monetary,
    error_exit_on_exception, DateType
)
from abcli.model import ACCOUNT_TYPES
from abcli.utils import AccountTree
from abcli.commands import balance as mod_balance
from abcli.commands.csv import csv2json
from abcli.utils.click import PathType

logger = logging.getLogger()
tabulate_mod.PRESERVE_WHITESPACE = True

@click.group(__name__[__name__.rfind('.') + 1:])
def cli():
    pass


@cli.command('show')
@click.option('--date-from', '--from', '-f', type=DateType(), default=format_date(Date.fromtimestamp(0)),
              help="Summarise transactions from specified date (inclusive); default to Epoch.")
@click.option('--date-to', '--to', '-t', type=DateType(), default=format_date(Date.today()),
              help="Summarise transactions to specified date (inclusive); default to today.")
@click.option('--month', '-m', type=click.DateTime(("%m/%Y",)))
@click.option('--account', '-a', help="Show transactions that involve a specific account.")
@click.option("--include-nonresolved", '-i', is_flag=True, help="Include non-resolved transactions.")
@click.option('--verbose', '-v', is_flag=True, help="Verbose output; include posts.")
@click.option('--uid', help="Transaction id")
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_show(db, month: DateTime, date_from: Date, date_to: Date,
             account: str, include_nonresolved: bool, verbose: bool, uid: str):
    if month:
        date_from = Date(month.year, month.month, 1)
        date_to = Date(month.year, month.month, calendar.monthrange(month.year, month.month)[1])

    if uid:
        try:
            txn = db.Transaction[uid]
            txn_show(txn, verbose)
            return 0
        except orm.ObjectNotFound:
            raise KeyError(f"Transaction '{uid}' not found.")

    txn_uids_shown = set()
    query = get_posts_between_period(db, date_from, date_to, include_nonresolved)
    if account:
        query = query.filter(lambda post: post.account.name.startswith(account))

    for post in query:
        txn = post.transaction
        if txn.uid not in txn_uids_shown:
            txn_show(txn, verbose)
            txn_uids_shown.add(txn.uid)
            logger.info("")


@orm.db_session
def txn_show(txn, verbose=True):
    ref = f"({txn.ref})" if txn.ref else ""
    logger.info(f"Transaction '{txn.uid}' {ref}:")
    logger.info(f"  description: {txn.description}")
    logger.info(f"  min date occurred: {txn.min_date_occurred}")
    logger.info(f"  max date resolved: {txn.max_date_resolved}")
    logger.info(f"  summary:")
    sum_dic = defaultdict(float)
    for post in txn.posts:
        sum_dic[post.account.name] += float(post.amount)
    logger.info(textwrap.indent(tabulate([[name, format_monetary(amount)] for name, amount in sum_dic.items() if amount != 0.0],
                                         tablefmt="plain"), '    '))
    if verbose:
        logger.info(f"  posts:")
        table = [[post.account.name, format_monetary(post.amount), post.date_occurred, post.date_resolved] for post in txn.posts]
        logger.info(textwrap.indent(tabulate(table, headers=('account', 'amount', 'date occurred', 'date resolved'),
                                             tablefmt="simple"), '    '))


@cli.command('import')
@click.option("--create-missing/--no-create-missing", default=True,
              help="Create missing accounts.")
@click.argument('csvpath', type=PathType(exists=True, dir_okay=False))
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_import(db, csvpath: Path, create_missing: bool):
    with csvpath.open('r', encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        rows = list(reader)
    txn_json = csv2json.process(rows)

    account_names = _collect_account_names(txn_json)
    _ensure_accounts(db, account_names, create_missing)

    # Update operating account balance
    ctx: click.Context = click.get_current_context()
    ctx.invoke(mod_balance.cmd_set, account=txn_json['account'],
               balance=txn_json['balance']['balance'],
               date=parse_date(txn_json['balance']['date']))

    for txn in txn_json['transactions']:
        db.Transaction(
            uid=str(uuid.uuid4()),
            min_date_occurred=parse_date(txn['min_date_occurred']),
            max_date_resolved=parse_date(txn['max_date_resolved']),
            description=txn['description'],
            ref=txn['ref'],
            posts=[db.Post(account=db.Account[post['account']],
                           amount=float(post['amount']),
                           date_occurred=parse_date(post['date_occurred']),
                           date_resolved=parse_date(post['date_resolved']))
                   for post in txn['posts']]
        )
    logger.info(f"Imported {len(txn_json['transactions'])} transactions")

    return 0


def _collect_account_names(txn_json: Dict) -> Set[str]:
    account_names = set()
    account_names.add(txn_json['account'])

    for txn in txn_json['transactions']:
        for post in txn['posts']:
            account_names.add(post['account'])

    return account_names


@orm.db_session
def _ensure_accounts(db, account_names, create_missing: bool):
    for name in account_names:
        if db.Account.get(name=name) is None:
            if not create_missing:
                raise KeyError(f"Account '{name}' not found, and no --create-missing specified.")
            else:
                db.Account(name=name)


@cli.command('summary')
@click.option('--date-from', '--from', '-f', type=DateType(), default=format_date(Date.fromtimestamp(0)),
              help="Summarise transactions from specified date (inclusive); default to Epoch.")
@click.option('--date-to', '--to', '-t', type=DateType(), default=format_date(Date.today()),
              help="Summarise transactions to specified date (inclusive); default to today.")
@click.option('--month', '-m', type=click.DateTime(("%m/%Y",)))
@click.option('--account', '-a', help="Only include transactions that involve a specific account.")
@click.option("--include-nonresolved", '-i', is_flag=True, help="Include non-resolved transactions.")
@click.option('--depth', '-d', type=click.IntRange(min=1, max=10), default=10,
              help="Aggregation level on account name")
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_summary(db, month: DateTime, date_from: Date, date_to: Date, depth: int, account: str, include_nonresolved: bool):
    if month:
        date_from = Date(month.year, month.month, 1)
        date_to = Date(month.year, month.month, calendar.monthrange(month.year, month.month)[1])

    sum_dict = {}
    query = get_posts_between_period(db, date_from, date_to, include_nonresolved)
    if account:
        query = query.filter(lambda post: post.account.name.startswith(account))

    for post in query:
        name = _account_name_at_depth(post.account.name, depth)
        sum_dict[name] = sum_dict.get(name, 0.0) + float(post.amount)

    _show_summary_tree(sum_dict)


def _account_name_at_depth(name: str, depth: int):
    assert depth >= 1
    return ':'.join(name.split(':')[:depth])


def _show_summary_tree(sum_dict: Dict[str, float], indent=""):
    def _format_tree(tree):
        return (format_monetary(tree.amount),
                f"{tree.amount / tree._parent.amount * 100.00:.2f}%" if tree._parent else "")
    tuples = []
    for acctype in ACCOUNT_TYPES:
        tree = AccountTree(acctype)
        for acc_name in filter(lambda name: name.startswith(acctype), sum_dict):
            tree.add(acc_name, sum_dict[acc_name])
        # if tree.has_children():
        #     tuples += tree.get_format_tuples(indent)

        tuples += tree.get_format_tuples(callback=_format_tree, indent=indent)

    print(tabulate(tuples, tablefmt="simple", headers=("account", "amount", "% of parent"),
                   colalign=("left", "right", "right")))


@orm.db_session
def get_posts_between_period(db, date_from: Date, date_to: Date, include_nonresolved=False) -> orm.core.Query:
    if include_nonresolved:
        return db.Post.select(lambda p: p.date_resolved >= date_from and p.date_occurred <= date_to)
    else:
        return db.Post.select(lambda p: p.date_occurred >= date_from and p.date_resolved <= date_to)
