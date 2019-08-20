import csv
from collections import OrderedDict
from pathlib import Path

import click

from abcli.utils import PathType

FIELDS = ['date_occurred', 'date_resolved', 'amount', 'description', 'balance',
          'this', 'that_auto', 'that_overwrite', 'ref']


@click.command("prep")
@click.option("-a", "--this", required=True, help="The operating account name")
@click.argument("csvpath", type=PathType(exists=True, dir_okay=False))
def cmd_prep(this: str, csvpath: Path):
    lines = csvpath.read_text('UTF-8').strip().split('\n')
    converted_records = []
    for (date_resolved, amount, desc, balance) in csv.reader(lines):
        date_occurred = date_resolved
        if 'Value Date:' in desc:
            date_occurred = desc[-10:]
            desc = desc[:desc.index(" Value Date:")]

        converted_records.append(OrderedDict({
            'date_occurred': date_occurred,
            'date_resolved': date_resolved,
            'amount': amount,
            'description': desc,
            'balance': balance,
            'this': this
        }))

    with csvpath.open('w') as fp:
        writer = csv.DictWriter(fp, FIELDS)
        writer.writeheader()
        writer.writerows(converted_records)
