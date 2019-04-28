import json
import logging

import click
from pony.orm import *

from accbook.cli.model import (
    Account, BalanceAccount, Post, Transaction, Date
)

logger = logging.getLogger()

@click.group('transactions')
def cli():
    pass

@cli.command('import')
@click.argument('json_file', type=click.Path(exists=True, dir_okay=False))
def cmd_import(json_file: str):
    # with open(json_file) as fp:
    #     txn_json = json.load(fp)
    #     import_txn_json(txn_json)
    logger.info('transaction import command invoked')


@db_session
def import_txn_json(txn_json):
    pass