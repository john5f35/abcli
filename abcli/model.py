from datetime import date as Date, timedelta as TimeDelta
from decimal import Decimal
from dataclasses import dataclass

from pony import orm
from treelib import Tree

from abcli.utils import format_date


ACCOUNT_TYPES = ('Income', 'Expense', 'Asset', 'Liability')


def account_name_at_depth(name: str, depth: int):
    assert depth >= 1
    return ':'.join(name.split(':')[:depth])


# class AccountTree(Tree):
#     class Amount(float):
#         @property
#         def value(self):
#             return self
#
#     def add_account(self, name: str, amount: float):
#         if name == '':
#             self.create_node(identifier='', data=AccountTree.Amount())
#             return
#         parent = name.rpartition(':')[0]
#         if not self.contains(parent):
#             self.add_account(parent, 0)
#         self.create_node(identifier=name, parent=parent, data=AccountTree.Amount())
#         self.update_node(name, amount=amount)
#
#     def update_node(self, nid, **attrs):
#         amount = attrs['amount']
#         this = self.get_node(nid)
#         super().update_node(nid, data=this.data + attrs['amount'])
#         if nid != '':
#             parent = nid.rpartition(':')[0]
#             self.update_node(parent, amount=amount)


class DictConversionMixin:
    def to_dictrepr(self, simple=True, visited=set()):
        visited.add(self)

        attrs = self.__class__._get_attrs_(with_collections=True)
        dic = self.to_dict(with_collections=True, related_objects=True)
        for attr in attrs:
            val = dic[attr.name]
            if val is None and simple:
                del dic[attr.name]
            elif isinstance(attr, orm.Set):
                res = {}
                for obj in val:
                    if obj not in visited:
                        res[obj.get_pk()] = obj.to_dictrepr(visited)
                if len(res) == 0 and simple:
                    del dic[attr.name]
                    continue
                else:
                    dic[attr.name] = res
            elif isinstance(dic[attr.name], Date):
                dic[attr.name] = format_date(val)
        return dic

def init_orm(db: orm.Database):

    class Account(db.Entity, DictConversionMixin):
        # __slot__ = ('name', 'balance', 'posts', 'budget_items')
        name = orm.PrimaryKey(str)
        balance = orm.Optional(lambda: Balance, cascade_delete=True)
        posts = orm.Set(lambda: Post, cascade_delete=True)
        budget_items = orm.Set(lambda: BudgetItem, cascade_delete=True)

    class Balance(db.Entity, DictConversionMixin):
        account = orm.PrimaryKey(Account)
        amount = orm.Required(Decimal, precision=16, scale=2)
        date = orm.Required(Date)

    class Post(db.Entity, DictConversionMixin):
        account = orm.Required(Account)
        amount = orm.Required(Decimal, precision=16, scale=2)
        description = orm.Optional(str)
        transaction = orm.Optional(lambda: Transaction)

    class Transaction(db.Entity, DictConversionMixin):
        uid = orm.PrimaryKey(str)
        date = orm.Required(Date)
        posts = orm.Set(Post)
        periodical = orm.Optional(lambda: Periodical)

    class Periodical(db.Entity, DictConversionMixin):
        period = orm.Required(TimeDelta)
        transactions = orm.Set(Transaction)

    class Budget(db.Entity, DictConversionMixin):
        date_from = orm.Required(Date)
        date_to = orm.Required(Date)
        items = orm.Set(lambda: BudgetItem)

    class BudgetItem(db.Entity, DictConversionMixin):
        account = orm.Required(Account)
        amount = orm.Required(Decimal, precision=16, scale=2)
        budget = orm.Optional(Budget)

    db.generate_mapping(create_tables=True)


def is_balance_account(account_name: str) -> bool:
    return account_name.startswith("Asset") or account_name.startswith("Liability")
