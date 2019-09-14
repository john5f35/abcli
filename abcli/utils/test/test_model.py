from abcli.utils.model import AccountTree, format_monetary


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


def test_account_tree_format():
    tree = AccountTree('A')
    tree.add('A:B', 15.0)
    tree.add('A:B:C', -10)
    tree.add('A:D', 3)
    tree.add('A:D:E', 5)

    callback = lambda tree: (f"({format_monetary(tree.amount)})", )
    assert tree.get_format_tuples(callback=callback, indent="") == [
        ("A", "($13.00)"),
        ("├── B", "($5.00)"),
        ("│   └── C", "(-$10.00)"),
        ("└── D", "($8.00)"),
        ("    └── E", "($5.00)")
    ]
