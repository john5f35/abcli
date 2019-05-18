import logging
import datetime

import click
from pony import orm
from accbook.common import parse_date, JSON_FORMAT_DATE

logger = logging.getLogger()

@click.group(__name__[__name__.rfind('.')+1:])
def cli():
    pass

@cli.command('add')
@click.argument('name')
@click.pass_obj
@orm.db_session
def cmd_add(db, name: str):
    try:
        db.Account(name=name)
        click.echo(f"Account '{name}' added.")
        return 0
    except orm.ConstraintError:
        raise click.BadArgumentUsage(f"Account '{name}' already exists.")


@cli.command('delete')
@click.argument('name')
@click.pass_obj
@orm.db_session
def cmd_delete(db, name: str):
    try:
        db.Account[name].delete()
        click.echo(f"Account '{name}' deleted.")
        return 0
    except orm.ObjectNotFound:
        raise click.BadArgumentUsage(f"Account '{name}' does not exist.")


@cli.command('show')
@click.argument('name')
@click.pass_obj
@orm.db_session
def cmd_show(db, name: str):
    try:
        account = db.Account[name]
        click.echo(f"Account '{name}'")
        return 0
    except orm.ObjectNotFound:
        raise click.BadArgumentUsage(f"Account '{name}' does not exist.")
