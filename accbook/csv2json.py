from pathlib import Path
import json, yaml
import csv
import re
import datetime
from pprint import PrettyPrinter
import json
from collections import defaultdict
import uuid

import click

from accbook.common import load_csv, this_str2dict

pformat = PrettyPrinter().pformat


def _group_by_ref(recs: [dict]) -> dict:
    refgroup = defaultdict(list)

    for rec in recs:
        refgroup[rec['ref']].append(rec)

    return refgroup

def recs2txns(csvrecs: [dict], this: str) -> [dict]:
    def _convert_this_dict(this_dict: dict, rec: dict) -> [dict]:
        return [{
                "account": account,
                "amount": amount,
                "desc": rec['desc'],
                'date': rec['date']
            } for account, amount in this_dict.items()]

    def _group2txn(recs: [dict]) -> dict:
        posts = []
        for rec in recs:
            amount = float(rec['amount'])
            this_dict = this_str2dict(rec['this'], amount)
            if '__this__' in this_dict:
                this_dict[this] = this_dict['__this__']
                del this_dict['__this__']
            that_dict = this_str2dict(rec['that'], -amount)

            posts.extend(_convert_this_dict(this_dict, rec))
            posts.extend(_convert_this_dict(that_dict, rec))

        return {
            'id': str(uuid.uuid4()),
            'posts': posts
        }

    txns = []

    group_dict = _group_by_ref(csvrecs)

    for ref, recs in group_dict.items():
        if ref == '':
            txns.extend([_group2txn([rec]) for rec in group_dict['']])
        else:
            txns.append(_group2txn(recs))

    return txns

def process(csvrecs: [dict], this: str) -> [dict]:
    return recs2txns(csvrecs, this)


@click.command()
@click.option("-o", "--output", required=True, type=click.Path(dir_okay=False),
                callback=lambda c, p, v: Path(v))
@click.option("-a", "--this", required=True, help="The operating account name")
@click.argument("csvpath", type=click.Path(exists=True, dir_okay=False),
                callback=lambda c, p, v: Path(v))
def main(csvpath: Path, output: Path, this: str):
    txns = load_csv(csvpath)
    res = process(txns, this)
    with output.open('w', encoding='utf-8') as fp:
        json.dump(res, fp, separators=(',', ':'), indent=2)


if __name__ == '__main__':
    main()
