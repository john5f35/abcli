import click

from abcli.commands.csv.classify import cmd_classify
from abcli.commands.csv.csv2json import cmd_csv2json


@click.group("csv")
def cli():
    pass


cli.add_command(cmd_classify)
cli.add_command(cmd_csv2json)
