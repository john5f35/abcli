import uuid
import random
from datetime import date

from pony import orm

from abcli.model import init_orm
from abcli.commands.transaction import get_posts_between_period


def test_get_transaction_between_periods():
    orm.set_sql_debug(True)
    db = orm.Database(provider='sqlite', filename=':memory:', create_db=True)
    init_orm(db)

    with orm.db_session:
        acc1 = db.Account(name="TestAccount1")
        acc2 = db.Account(name="TestAccount2")
        def _random_txn_on_date(_date: date):
            amount = random.randrange(1, 100000) / 100.0
            return db.Transaction(
                uid=str(uuid.uuid4()), date=_date, posts=[
                    db.Post(account=acc1, amount=amount),
                    db.Post(account=acc2, amount=-amount)
                ]
            )
        txn1 = _random_txn_on_date(date(2019, 1, 1))
        txn2 = _random_txn_on_date(date(2019, 1, 3))
        txn3 = _random_txn_on_date(date(2019, 1, 4))

        _posts_from = lambda lst: set([p for txn in lst for p in txn.posts])
        query = get_posts_between_period(db, None, None)
        assert set(query) == _posts_from([txn1, txn2, txn3])

        query = get_posts_between_period(db, date(2019, 1, 2), None)
        assert set(query) == _posts_from([txn2, txn3])

        query = get_posts_between_period(db, None, date(2019, 1, 4))
        assert set(query) == _posts_from([txn1, txn2])

        query = get_posts_between_period(db, date(2018, 12, 29), date(2019, 1, 5))
        assert set(query) == _posts_from([txn1, txn2, txn3])

