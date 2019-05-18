from pony import orm

from accbook.cli.model import init_orm
from accbook.common import format_date, Date


def test_todictrepr():
    orm.set_sql_debug(True)
    db = orm.Database(provider='sqlite', filename=':memory:', create_db=True)
    init_orm(db)

    with db.set_perms_for(db.Account, db.Post, db.Transaction):
        orm.perm('view', group='anybody')

    with orm.db_session:
        account = db.Account(name="TestAccount")

        assert account.to_dictrepr() == {
            'name': 'TestAccount'
        }
        assert account.to_dictrepr(simple=False) == {
            'name': 'TestAccount',
            'balance': None,
            'budget_items': {},
            'posts': {}
        }
