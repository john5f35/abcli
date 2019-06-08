from pathlib import Path
import yaml
import csv
import re
import datetime
from pprint import PrettyPrinter
import logging

import click

from abcli.utils import PathType
from abcli.commands.csv.utils import load_csv, this_str2dict, FIELDS

pformat = PrettyPrinter().pformat
logger = logging.getLogger()


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


def _check_custom(txn: dict) -> bool:
    """ Verifies that custom transaction splitting is legitimate. """
    amount = float(txn['amount'])
    this_dict = this_str2dict(txn['this'], amount)
    that_dict = this_str2dict(txn['that'], -amount)

    if this_dict is None or that_dict is None:
        return False
    return abs(sum(this_dict.values()) + sum(that_dict.values())) < 1e-6


def preprocess(txns: [dict]) -> [dict]:
    def _fix_date(txn: dict) -> dict:
        """ Fix transaction date if there's 'Value Date:' in description """
        note = txn['desc']
        if 'Value Date:' in note:
            txn['date'] = note[-10:]
            txn['desc'] = note[:note.index(" Value Date:")]
        return txn

    processed = []
    for idx, txn in enumerate(txns):
        txn = _fix_date(txn)
        if not _check_custom(txn):
            raise ValueError(
                f"Validation failed in this or that field of transaction at line {idx + 2}: \n{pformat(txn)}")

        processed.append(txn)
    parse_date = lambda txn: datetime.datetime.strptime(txn['date'], '%d/%m/%Y')
    return list(sorted(processed, key=parse_date, reverse=True))


@click.command("classify")
@click.option("-r", "--rulebook", "rulebook_path", type=PathType(exists=True, dir_okay=False),
              help='Rule book JSON file for assigning accounts/categories; default can be specified in config.json')
@click.option("-f", "--force", is_flag=True, type=click.BOOL, help="Force re-classify")
@click.argument("csvpath", type=PathType(exists=True, dir_okay=False))
def cmd_classify(csvpath: Path, rulebook_path: Path, force):
    rulebook = _load_rulebook(rulebook_path)

    txns = load_csv(csvpath)
    txns = preprocess(txns)

    restxns, num_classified = process(txns, rulebook, force)

    logger.info(f"{num_classified}/{len(restxns)} classified ({int(num_classified / len(restxns) * 100)}%)")

    with csvpath.open('w', encoding='utf-8') as fp:
        writer = csv.DictWriter(fp, FIELDS)
        writer.writeheader()
        writer.writerows(restxns)


CONFIG_RULEBOOK_KEY = "csv.classify.rulebook"


def _load_rulebook(rb_path: Path):
    if rb_path is None:
        config = click.get_current_context().meta
        if config.get(CONFIG_RULEBOOK_KEY, None):
            rb_path = Path(config[CONFIG_RULEBOOK_KEY])
        else:
            raise click.UsageError(f"Rulebook path not specified on command line, nor defined in config JSON.",
                                   click.get_current_context())

    with rb_path.open('r', encoding='utf-8') as fp:
        return yaml.full_load(fp)
