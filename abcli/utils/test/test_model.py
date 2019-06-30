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


def test_account_tree_format():
    tree = AccountTree('A')
    tree.add('A:B', 15.0)
    tree.add('A:B:C', -10)
    tree.add('A:D', 3)

    assert tree._dfs(0, False) == [
        ('A', 8.0, 0, False),
        ('B', 5.0, 1, False),
        ('C', -10, 2, True),
        ('D', 3, 1, True)
    ]

    assert tree.format_string(tabular=False) == \
           ("A ($8.00)\n"
            "├── B ($5.00)\n"
            "│   └── C (-$10.00)\n"
            "└── D ($3.00)")

    assert tree.format_string(tabular=True) == \
           ("A            $8.00\n"
            "├── B        $5.00\n"
            "│   └── C  -$10.00\n"
            "└── D        $3.00")
