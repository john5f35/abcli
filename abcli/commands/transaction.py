import logging
import json
from typing import *
import uuid

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

logger = logging.getLogger()
tabulate_mod.PRESERVE_WHITESPACE = True

@click.group(__name__[__name__.rfind('.') + 1:])
def cli():
    pass


@cli.command('show')
@click.argument('uid')
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_show(db, uid: str):
    try:
        txn = db.Transaction[uid]
        txn_show(txn)
        return 0
    except orm.ObjectNotFound:
        raise KeyError(f"Transaction '{uid}' not found.")


@orm.db_session
def txn_show(txn):
    logger.info(f"Transaction '{txn.uid}':")
    logger.info(f"  date: {txn.date}")
    logger.info(f"  posts:")
    table = [[post.account.name, format_monetary(post.amount)] for post in txn.posts]
    logger.info(textwrap.indent(tabulate(table, tablefmt="plain"), '    '))


@cli.command('import')
@click.option("--create-missing/--no-create-missing", default=True,
              help="Create missing accounts.")
@click.argument('txn_json_path', type=click.Path(exists=True, dir_okay=False))
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_import(db, txn_json_path: str, create_missing: bool):
    with open(txn_json_path) as fp:
        txn_json = json.load(fp)

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
@click.option("--include-nonresolved", '-i', is_flag=True, help="Include non-resolved transactions.")
@click.option('--depth', '-d', type=click.IntRange(min=1, max=10), default=10,
              help="Aggregation level on account name")
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_summary(db, date_from: Date, date_to: Date, depth: int, include_nonresolved: bool):
    sum_dict = {}
    query = get_posts_between_period(db, date_from, date_to, include_nonresolved)

    for post in query:
        name = _account_name_at_depth(post.account.name, depth)
        sum_dict[name] = sum_dict.get(name, 0.0) + float(post.amount)

    _show_summary_tree(sum_dict)


def _account_name_at_depth(name: str, depth: int):
    assert depth >= 1
    return ':'.join(name.split(':')[:depth])


def _report_summary(sum_dict: Dict[str, float]):
    categ_dict = {ty: [] for ty in ACCOUNT_TYPES}

    for acc_name, sum_amount in sum_dict.items():
        categ_dict[_account_name_at_depth(acc_name, 1)].append((acc_name, sum_amount))

    total_dict = {ty: sum([a for _, a in lst]) for ty, lst in categ_dict.items()}
    sorted_categ_dict = {ty: sorted(sum_lst, key=lambda tup: abs(tup[1])) for ty, sum_lst in categ_dict.items()}
    categ_dict_with_perc = {ty: [(n, a, a / total_dict[ty], abs(a / total_dict['Income'])) for n, a in lst] for ty, lst
                            in sorted_categ_dict.items()}

    table = [(n, format_monetary(a), f"{perc_ty * 100:.2f}%", f"{perc_ttl * 100:.2f}%")
             for _, lst in categ_dict_with_perc.items()
             for n, a, perc_ty, perc_ttl in lst]
    logger.info(
        textwrap.indent(tabulate(table, headers=("account", "amount", "% of account type", "% of total income")), "  "))


def _show_summary_tree(sum_dict: Dict[str, float]):
    tuples = []
    for acctype in ACCOUNT_TYPES:
        tree = AccountTree(acctype)
        for acc_name in filter(lambda name: name.startswith(acctype), sum_dict):
            tree.add(acc_name, sum_dict[acc_name])
        tuples += tree.get_format_tuples()

    print(tabulate(tuples, tablefmt="plain", colalign=("left", "right")))


@orm.db_session
def get_posts_between_period(db, date_from: Date, date_to: Date, include_nonresolved=False) -> orm.core.Query:
    if include_nonresolved:
        return db.Post.select(lambda p: p.date_resolved >= date_from and p.date_occurred <= date_to)
    else:
        return db.Post.select(lambda p: p.date_resolved >= date_from and p.date_resolved <= date_to)
