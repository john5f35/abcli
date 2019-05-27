import logging
import time
from datetime import datetime as DateTime
import random
import json
from typing import *
from hashlib import sha1
import uuid

import click
from pony import orm
import textwrap
from tabulate import tabulate
from tqdm import tqdm as pbar

from accbook.common import (
    Date, format_date, parse_date, format_monetary,
    JSON_FORMAT_DATE, error_exit_on_exception, DateType
)
from accbook.cli.commands import balance as mod_balance

logger = logging.getLogger()

@click.group(__name__[__name__.rfind('.')+1:])
def cli():
    pass

@cli.command('add')
@click.option('--date', '-d', type=DateType(), default=format_date(Date.today()),
    help='Date of transaction; default to today.')
@click.option('--post-account', '--from', '-f', 'accounts', multiple=True, required=True,
    help='Account of a post')
@click.option('--post-amount', '--amount', '-a', 'amounts', type=click.FLOAT, multiple=True, required=True,
    help='Amount of a post')
@click.option("--create-missing", '-n', is_flag=True, default=False,
    help='Create an account if not found')
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_add(db, date: Date, accounts, amounts, create_missing: bool):
    assert len(accounts) == len(amounts), "Number of post account and amount should be the same."
    _sum = sum(amounts)
    if _sum != 0.0:
        raise ValueError(f"Sum of post amounts is not 0 (sum = {format_monetary(_sum)})!")

    for name in accounts:
        if db.Account.get(name=name) is None:
            if create_missing:
                db.Account(name=name)
            else:
                raise KeyError(f"Account '{name}' not found, and no --create-missing specified.")

    _ensure_accounts(db, accounts, create_missing)
    posts = [{
        "account": acc,
        "amount": amn
    } for acc, amn in zip(accounts, amounts)]

    txn = txn_add(db, date, posts)
    txn_show(txn)
    return 0


@orm.db_session
def txn_add(db, date: Date, posts: [dict], uid=None):
    if uid is None:
        # uid = sha1(f"{date}{''.join([p['account']+str(p['amount'])])}{random.random()}")
        uid = str(uuid.uuid4())
    return db.Transaction(uid=uid, date=date, posts=[db.Post(account=p['account'], amount=p['amount']) for p in posts])


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

    # Set operating account balance
    ctx: click.Context = click.get_current_context()
    ctx.invoke(mod_balance.cmd_set, account=txn_json['account'],
                                    balance=txn_json['balance']['balance'],
                                    date=txn_json['balance']['date'])

    for txn in txn_json['transactions']:
        txn_add(db, parse_date(txn['date']), txn['posts'])
    logger.info(f"Imported {len(txn_json['transactions'])} transactions")

    return 0

def _collect_account_names(txn_json: Dict) -> Set[str]:
    account_names = set(txn_json['account'])

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

# TODO: command 'search' / 'list'

@cli.command('summary')
@click.option('--date-from', '--from', '-f', type=DateType(),
    help="Summarise transactions from specified date (inclusive)")
@click.option('--date-to', '--to', '-t', type=DateType(),
    help="Summarise transactions to specified date (exclusive)")
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_summary(db, date_from: Date, date_to: Date):
    def _txn_in_date_range(txn: db.Transaction):
        if date_from and txn.date < date_from:
            return False
        if date_to and txn.date >= date_to:
            return False
        return True

    sum_dict = {}
    query = db.Post.select(lambda p: not ((date_from and p.transaction.date < date_from) or (date_to and p.transaction.date >= date_to)))

    for post in query:
        sum_dict[post.account.name] = sum_dict.get(post.account.name, 0.0) + float(post.amount)

    table = [[k, format_monetary(v)] for k, v in (sorted(sum_dict.items(), key=lambda tup: tup[1]))]
    logger.info(textwrap.indent(tabulate(table, tablefmt="plain"), ""))
