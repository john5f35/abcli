import logging

import click
from pony import orm
from tabulate import tabulate
import textwrap
from abcli.utils import (
    Date, format_date, format_monetary,
    error_exit_on_exception, DateType
)

logger = logging.getLogger()

@click.group(__name__[__name__.rfind('.')+1:])
def cli():
    pass


@cli.command('set')
@click.argument('account')
@click.argument('balance', type=click.FLOAT)
@click.option('--date', '-d', type=DateType(), default=format_date(Date.today()),
    help='Date of balance (end-of-day); default to today.')
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_set(db, account: str, balance: float, date: Date):
    try:
        account = db.Account[account]
        obj = db.Balance.get(account=account)
        if obj:
            obj.amount = balance
            obj.date_eod = date
        else:
            obj = db.Balance(account=account, amount=balance, date_eod=date)
        logger.info(f"Balance:")
        table = [[str(obj.date_eod), obj.account.name, format_monetary(obj.amount)]]
        logger.info(textwrap.indent(tabulate(table, tablefmt="plain"), "  "))
        return 0
    except ValueError:
        raise ValueError(f"Failed to parse date '{date}'.")
    except orm.ObjectNotFound:
        raise KeyError(f"Account '{account}' does not exist.")

# TODO: verify balance using transactions when setting it


@cli.command('show')
@click.argument('account')
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_show(db, account: str):
    account = db.Account.get(name=account)
    if account is None:
        raise KeyError(f"Account '{account}' does not exist.")
    balance = db.Balance.get(account=account)
    if balance is None:
        raise KeyError(f"No balance defined on account '{account.name}'.")

    logger.info(f"{account.name}:")
    logger.info(f"  balance: ${balance.amount}")
    logger.info(f"  date: {balance.date}")