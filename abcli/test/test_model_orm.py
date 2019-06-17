from pony import orm

from abcli.model import init_orm, AccoutTree


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


def test_account_tree():
    tree = AccoutTree()
    tree.add_account('A:B', 15)
    assert tree.contains('A:B')
    assert tree.contains('A')
    assert tree.contains('')
    assert tree.get_node('A:B').data == 15.0
    assert tree.get_node('A').data == 15.0
    assert tree.get_node('').data == 15.0

    tree.add_account("A:B:C", -10)
    assert tree.contains("A:B:C")
    assert tree.get_node("A:B:C").data == -10
    assert tree.get_node("A:B").data == 5
    assert tree.get_node("A").data == 5

    tree.add_account("A:D", 3)
    assert tree.contains("A:D")
    assert tree.get_node("A").data == 8

