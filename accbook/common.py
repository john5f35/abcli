import csv
from pathlib import Path

FIELDS = ['date', 'amount', 'desc', 'balance', 'this', 'that', 'ref', 'tags']

def load_csv(csvpath: Path) -> [dict]:
    lines = csvpath.read_text('UTF-8').strip().split('\n')
    txns = list(csv.DictReader(lines, FIELDS, restval=''))
    if txns[0]['date'] == 'date':
        # Skip header if file contains header
        txns = txns[1:]
    return txns

def this_str2dict(this_field: str, amount: float) -> dict:
    if this_field == '':
        this_field = '__this__'
    if not '{' in this_field:
        return {this_field: amount}
    if _is_valid_dictstr(this_field):
        return eval(this_field)
    return None

def _is_valid_dictstr(dictstr: str):
    try:
        d = eval(dictstr)
        assert isinstance(d, dict)
        return True
    except Exception:
        return False
