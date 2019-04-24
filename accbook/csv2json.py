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

def groupby(iterable, key) -> dict:
    group = defaultdict(list)
    for obj in iterable:
        group[key(obj)].append(obj)
    return group


def _rec2txn(rec: dict, this: str) -> dict:
    amount = float(rec['amount'])
    this_dict = this_str2dict(rec['this'], amount)
    that_dict = this_str2dict(rec['that'], -amount)

    def _to_posts(this_dict: dict):
        posts = []
        for account, amount in this_dict.items():
            if account == '__this__':
                d = {'account': this, 'amount': amount, 'desc': rec['desc']}
            else:
                d = {'account': account, 'amount': amount}
            posts.append(d)
        return posts

    return {
        'id': str(uuid.uuid4()),
        'date': rec['date'],
        'ref': rec['ref'][1:],
        # 'tags': rec['tags'],
        'posts': _to_posts(this_dict) + _to_posts(that_dict)
    }

def recs2txns(csvrecs: [dict], this: str) -> [dict]:
    def _merge_same_date(txns: [dict]) -> dict:
        if len(txns) == 1:
            return txns

        posts = []
        for txn in txns:
            posts.extend(txn['posts'])

        return {
            'id': str(uuid.uuid4()),
            'date': txns[0]['date'],
            'ref': txns[0]['ref'],
            'posts': posts
        }

    def _group2txn(recs: [dict]) -> [dict]:
        _txns = list(map(lambda rec: _rec2txn(rec, this), recs))
        if len(_txns) == 1:
            return _txns

        date_groups = groupby(_txns, lambda txn: txn['date'])
        return list(map(_merge_same_date, date_groups.values()))


    group_dict = groupby(csvrecs, lambda rec: rec['ref'])

    txns = []
    for ref, recs in group_dict.items():
        if ref == '':
            txns.extend([_group2txn([rec])[0] for rec in group_dict['']])
        else:
            txns.extend(_group2txn(recs))

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
