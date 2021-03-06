import click

from abcli.commands.csv.classify import cmd_classify
from abcli.commands.csv.prep import cmd_prep


@click.group("csv")
def cli():
    pass


cli.add_command(cmd_classify)
cli.add_command(cmd_prep)
