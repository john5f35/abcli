import logging
import datetime
import random
from hashlib import sha1

import click
from pony import orm
from accbook.common import (
    Date, format_date, parse_date, format_monetary,
    JSON_FORMAT_DATE, error_exit_on_exception
)

logger = logging.getLogger()

@click.group(__name__[__name__.rfind('.')+1:])
def cli():
    pass

@cli.command('add')
@click.option('--date', '-d', default=format_date(Date.today()),
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
def cmd_add(db, date: str, accounts, amounts, create_missing: bool):
    date = parse_date(date)
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

    txn = txn_add(db, date, accounts, amounts)
    txn_show(txn)


@orm.db_session
def txn_add(db, date: Date, accounts: [str], amounts: [float]):
    accounts = [db.Account[name] for name in accounts]

    posts = [db.Post(account=acc, amount=amn) for acc, amn in zip(accounts, amounts)]
    uid = sha1(f"{date}{accounts}{amounts}{random.random()}".encode()).hexdigest()

    return db.Transaction(uid=uid, date=date, posts=posts)

@orm.db_session
def txn_show(txn):
    logger.info(f"Transaction (uid={txn.uid}):")
    logger.info(f"  date: {txn.date}")
    logger.info(f"  posts:")
    for post in txn.posts:
        logger.info(f"    {post.account.name}: {format_monetary(post.amount)}")

# @cli.command('import')
# @click.argument('json_file', type=click.Path(exists=True, dir_okay=False))
# def cmd_import(json_file: str):
#     with open(json_file) as fp:
#         txn_json = json.load(fp)
#         import_txn_json(txn_json)


# @db_session
# def import_txn_json(txn_json):
#     update_balance_account(txn_json['account'], txn_json['balance'])

#     for txn in txn_json['transactions']:
#         logger.info(f"Importing transaction {txn['id']}")
#         import_txn(txn)


# def update_balance_account(name, balance):
#     date = parse_date(balance['date'])
#     amount = float(balance['balance'])
#     try:
#         balacc = BalanceAccount[name]
#         balacc.date = date
#         balacc.balance = amount
#     except ObjectNotFound:
#         balacc = BalanceAccount(name=name, date=date, balance=amount)

# def get_or_create_account(name):
#     try:
#         return Account[name]
#     except ObjectNotFound:
#         if is_balance_account(name):
#             # TODO: enforce existance and initial value?
#             logger.warn(f"Unknown balance account {name}, initialise balance to $0 at {Date.today()}")
#             return BalanceAccount(name=name, date=Date.today(), balance=0.0)
#         return Account(name=name)

# def import_txn(txn):
#     posts = []
#     for post_json in txn['posts']:
#         post = Post(
#             account=get_or_create_account(post_json['account']),
#             amount=float(post_json['amount']),
#             description=post_json.get('desc', "")
#         )
#         posts.append(post)
#     return Transaction(uid=txn['id'], date=parse_date(txn['date']), posts=posts)