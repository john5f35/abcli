import json

from accbook.cli import db
from accbook.cli.model import *

from pony.orm import *

from pprint import PrettyPrinter
pprint = PrettyPrinter().pprint

def test_todictrepr():
    set_sql_debug(True)
    db.bind('sqlite', ':memory:', create_db=True)
    db.generate_mapping(create_tables=True)

    with db.set_perms_for(Account, BalanceAccount, Post, Transaction):
        perm('view', group='anybody')

    with db_session:
        a = Account(name="TestAccount")
        b = BalanceAccount(name="TestBalanceAccount", date=Date.today(), balance=0.0)
        # commit()
        posts=[
            Post(account=a, amount=123.45),
            Post(account=b, amount=-123.45)
        ]
        txn = Transaction(uid="123", date=Date.today(), posts=posts)

        txn_dic = txn.to_dictrepr()

        assert isinstance(txn_dic['posts'], dict)
        assert txn_dic['posts'][1] == posts[0].to_dictrepr()
