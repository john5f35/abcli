import logging
import datetime

import click
from pony import orm
from accbook.common import Date, format_date, parse_date, JSON_FORMAT_DATE, error_exit_on_exception

logger = logging.getLogger()

@click.group(__name__[__name__.rfind('.')+1:])
def cli():
    pass

@cli.command('set')
@click.argument('account')
@click.argument('balance', type=click.FLOAT)
@click.option('--date', '-d', default=format_date(Date.today()),
    help='Date of balance; default to today.')
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_set(db, account: str, balance: float, date: str):
    try:
        date = parse_date(date)
        account = db.Account[account]
        obj = db.Balance.get(account=account)
        if obj:
            obj.amount = balance
            obj.date = date
        else:
            db.Balance(account=account, amount=balance, date=date)
        return 0
    except ValueError:
        raise ValueError(f"Failed to parse date '{date}'.")
    except orm.ObjectNotFound:
        raise KeyError(f"Account '{account}' does not exist.")


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