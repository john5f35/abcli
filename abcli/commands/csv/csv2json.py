from pathlib import Path
from pprint import PrettyPrinter
import json, csv
from collections import defaultdict
import math

import click

from abcli.utils.model import parse_date, format_date

pformat = PrettyPrinter().pformat


def row2txn(row: dict) -> dict:
    if '{' not in row['this']:
        this = [{'account': row['this'], 'amount': float(row['amount'])}]
    else:
        this = [{'account': acc, 'amount': amt} for acc, amt in eval(row['this']).items()]

    that_field = 'that_overwrite' if row['that_overwrite'] else 'that_auto'
    if '{' not in row[that_field]:
        that = [{'account': row[that_field], 'amount': -float(row['amount'])}]
    else:
        that = [{'account': acc, 'amount': amt} for acc, amt in eval(row[that_field]).items()]
    posts = this + that
    for p in posts:
        p.update({'date_occurred': row['date_occurred'], 'date_resolved': row['date_resolved']})

    txn_sum = sum(map(lambda p: p['amount'], posts))
    assert math.isclose(txn_sum, 0.0, abs_tol=1e-09), \
        f"Transaction posts sum does not add up to 0 in '{row}' (sum: {txn_sum})"

    return {
        'min_date_occurred': row['date_occurred'],
        'max_date_resolved': row['date_resolved'],
        'description': row['description'],
        'ref': row['ref'],
        'posts': posts,
    }


def _merge_same_refs(txns: [dict]) -> dict:
    posts = []
    for txn in txns:
        posts.extend(txn['posts'])

    return {
        'min_date_occurred': format_date(min(map(lambda _txn: parse_date(_txn['min_date_occurred']), txns))),
        'max_date_resolved': format_date(max(map(lambda _txn: parse_date(_txn['max_date_resolved']), txns))),
        'description': txns[0]['description'],
        'ref': txns[0]['ref'],
        'posts': posts
    }


def merge_txns(txns: [dict]) -> [dict]:
    no_refs = filter(lambda txn: not txn['ref'], txns)
    has_refs = filter(lambda txn: txn['ref'], txns)
    by_ref = defaultdict(list)
    for txn in has_refs:
        by_ref[txn['ref']].append(txn)

    for ref in by_ref:
        by_ref[ref] = _merge_same_refs(by_ref[ref])

    sorted_txns = sorted(list(no_refs) + list(by_ref.values()), key=lambda _txn: parse_date(_txn['max_date_resolved']))
    return sorted_txns


def process(rows: [dict]) -> dict:
    txns = list(map(row2txn, rows))
    txns = merge_txns(txns)
    return {
        'account': rows[0]['this'],
        'balance': {
            'date': rows[0]['date_resolved'],
            'balance': float(rows[0]['balance'])
        },
        'transactions': txns
    }
