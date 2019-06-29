from abcli.utils.model import AccountTree


def test_account_tree():
    tree = AccountTree('A')
    tree.add('A:B', 15.0)
    assert tree.get('A:B').amount == 15.0
    assert tree.get('A').amount == 15.0
    assert tree.get("") is None

    tree.add("A:B:C", -10)
    assert tree.get("A:B:C").amount == -10
    assert tree.get("A:B").amount == 5
    assert tree.get("A").amount == 5

    tree.add("A:D", 3)
    assert tree.get('A').amount == 8
