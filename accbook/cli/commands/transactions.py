import json
import logging

import click
from pony.orm import *

from accbook.common import parse_date
from accbook.cli.model import (
    Account, BalanceAccount, Post, Transaction, Date,
    is_balance_account
)

logger = logging.getLogger()

@click.group('transactions')
def cli():
    pass

@cli.command('import')
@click.argument('json_file', type=click.Path(exists=True, dir_okay=False))
def cmd_import(json_file: str):
    with open(json_file) as fp:
        txn_json = json.load(fp)
        import_txn_json(txn_json)


@db_session
def import_txn_json(txn_json):
    update_balance_account(txn_json['account'], txn_json['balance'])

    for txn in txn_json['transactions']:
        logger.info(f"Importing transaction {txn['id']}")
        import_txn(txn)


def update_balance_account(name, balance):
    date = parse_date(balance['date'])
    amount = float(balance['balance'])
    try:
        balacc = BalanceAccount[name]
        balacc.date = date
        balacc.balance = amount
    except ObjectNotFound:
        balacc = BalanceAccount(name=name, date=date, balance=amount)

def get_or_create_account(name):
    try:
        return Account[name]
    except ObjectNotFound:
        if is_balance_account(name):
            # TODO: enforce existance and initial value?
            logger.warn(f"Unknown balance account {name}, initialise balance to $0 at {Date.today()}")
            return BalanceAccount(name=name, date=Date.today(), balance=0.0)
        return Account(name=name)

def import_txn(txn):
    posts = []
    for post_json in txn['posts']:
        post = Post(
            account=get_or_create_account(post_json['account']),
            amount=float(post_json['amount']),
            description=post_json.get('desc', "")
        )
        posts.append(post)
    return Transaction(uid=txn['id'], date=parse_date(txn['date']), posts=posts)