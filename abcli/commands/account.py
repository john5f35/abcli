import logging

import click
from pony import orm
from abcli.utils import error_exit_on_exception

logger = logging.getLogger()

@click.group(__name__[__name__.rfind('.')+1:])
def cli():
    pass

@cli.command('add')
@click.argument('name')
@click.pass_obj
@error_exit_on_exception
def cmd_add(db, name: str):
    with orm.db_session:
        try:
            db.Account(name=name)
            orm.commit()
            logger.info(f"Account '{name}' added.")
            return 0
        except orm.TransactionIntegrityError:
            raise click.BadArgumentUsage(f"Account '{name}' already exists.")


@cli.command('delete')
@click.argument('name')
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_delete(db, name: str):
    try:
        db.Account[name].delete()
        logger.info(f"Account '{name}' deleted.")
        return 0
    except orm.ObjectNotFound:
        raise click.BadArgumentUsage(f"Account '{name}' does not exist.")


@cli.command('show')
@click.argument('name')
@click.pass_obj
@orm.db_session
@error_exit_on_exception
def cmd_show(db, name: str):
    try:
        account = db.Account[name]
        logger.info(f"Account '{name}'")
        return 0
    except orm.ObjectNotFound:
        raise click.BadArgumentUsage(f"Account '{name}' does not exist.")

# TODO: command 'list' (with prefix?)