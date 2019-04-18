from pathlib import Path
import json, yaml
import csv
import re
import datetime

import click


def process(txns: [dict], rulebook: dict, force=False) -> ([dict], int):
    restxns = []
    num_classified = 0

    is_custom = lambda that: '{' in that
    def _lookup_rulebook(note):
        for keyword, rule in rulebook['keyword'].items():
            if keyword.upper() in note.upper():
                return rule

        for regex, rule in rulebook['regex'].items():
            if re.match(regex, note):
                return rule

    for idx, txn in enumerate(txns):
        if not txn['that'] or (force and not is_custom(txn['that'])):
            # classify according to rulebook
            rule = _lookup_rulebook(txn['desc'])
            if rule is not None:
                if isinstance(rule, str):
                    txn['that'] = rule
                if isinstance(rule, dict):
                    txn.update(rule)

        if txn['that']:
            num_classified += 1

        restxns.append(txn)

    return restxns, num_classified


def preprocess(txns: [dict]) -> [dict]:
    def _fix_date(txn: dict) -> dict:
        note = txn['desc']
        if 'Value Date:' in note:
            txn['date'] = note[-10:]
            txn['desc'] = note[:note.index(" Value Date:")]
        return txn

    def _check_custom(txn: dict) -> dict:
        def __is_valid(dictstr: str):
            if dictstr != '' and '{' in dictstr:
                try:
                    d = eval(dictstr)
                    assert isinstance(d, dict)
                except Exception:
                    return False
            return True

        return __is_valid(txn['this']) and __is_valid(txn['that'])

    processed = []
    for idx, txn in enumerate(txns):
        txn = _fix_date(txn)
        if not _check_custom(txn):
            raise SyntaxError(f"invalid syntax in this or that field of transaction at line {idx}: {txn}")

        processed.append(txn)
    parse_date = lambda txn: datetime.datetime.strptime(txn['date'], '%d/%m/%Y')
    return list(sorted(processed, key=parse_date, reverse=True))


FIELDS = ['date', 'amount', 'desc', 'balance', 'this', 'that', 'ref', 'tags']

@click.command()
@click.option("-r", "--rulebook", required=True, type=click.Path(dir_okay=False),
                callback=lambda c, p, v: Path(v),
                help='Rule book JSON file for assigning accounts/categories')
@click.option("-f", "--force", is_flag=True, type=click.BOOL, help="Force re-classify")
@click.argument("csvpath", type=click.Path(exists=True, dir_okay=False),
                callback=lambda c, p, v: Path(v))
def main(csvpath: Path, rulebook: Path, force):
    with rulebook.open('r', encoding='utf-8') as fp:
        rulebook = yaml.full_load(fp)

    lines = csvpath.read_text('UTF-8').strip().split('\n')
    txns = list(csv.DictReader(lines, FIELDS, restval=''))
    if txns[0]['date'] == 'date':
        # Skip header if file contains header
        txns = txns[1:]

    txns = preprocess(txns)

    restxns, num_classified = process(txns, rulebook, force)

    print(f"{num_classified}/{len(restxns)} classified ({int(num_classified / len(restxns) * 100)}%)")

    with csvpath.open('w', encoding='utf-8') as fp:
        writer = csv.DictWriter(fp, FIELDS)
        writer.writeheader()
        writer.writerows(restxns)

if __name__ == "__main__":
    main()
