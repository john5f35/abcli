import csv
import logging
import re
from pathlib import Path
from pprint import PrettyPrinter

import click
import yaml

from abcli.utils import PathType

pformat = PrettyPrinter().pformat
logger = logging.getLogger()


def classify(txns: [dict], rulebook: dict) -> ([dict], int):
    restxns = []

    def _lookup_rulebook(note):
        for keyword, rule in rulebook['keyword'].items():
            if keyword.upper() in note.upper():
                return rule

        for regex, rule in rulebook['regex'].items():
            if re.match(regex, note):
                return rule

    for idx, txn in enumerate(txns):
        rule = _lookup_rulebook(txn['description'])
        if rule is not None:
            if isinstance(rule, str):
                txn['that_auto'] = rule
            if isinstance(rule, dict):
                txn.update(rule)

        restxns.append(txn)

    return restxns


@click.command("classify")
@click.option("-r", "--rulebook", "rulebook_path", type=PathType(exists=True, dir_okay=False),
              help='Rule book JSON file for assigning accounts/categories; default can be specified in config.json')
@click.argument("csvpath", type=PathType(exists=True, dir_okay=False))
def cmd_classify(csvpath: Path, rulebook_path: Path):
    rulebook = _load_rulebook(rulebook_path)

    with csvpath.open('r', encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        fieldnames = reader.fieldnames
        rows = list(reader)

    restxns = classify(rows, rulebook)
    num_classified = len(list(filter(lambda txn: txn['that_auto'] or txn['that_overwrite'], restxns)))

    logger.info(f"{num_classified}/{len(restxns)} classified ({int(num_classified / len(restxns) * 100)}%)")

    with csvpath.open('w', encoding='utf-8') as fp:
        writer = csv.DictWriter(fp, fieldnames)
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
