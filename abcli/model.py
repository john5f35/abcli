from datetime import date as Date, timedelta as TimeDelta
from decimal import Decimal
from dataclasses import dataclass

from pony import orm
from treelib import Tree

from abcli.utils import format_date


ACCOUNT_TYPES = ('Income', 'Expenses', 'Assets', 'Liabilities')


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

    class Balance(db.Entity, DictConversionMixin):
        account = orm.PrimaryKey(Account)
        amount = orm.Required(Decimal, precision=16, scale=2)
        date_eod = orm.Required(Date)

    class Post(db.Entity, DictConversionMixin):
        account = orm.Required(Account)
        amount = orm.Required(Decimal, precision=16, scale=2)
        date_occurred = orm.Required(Date)
        date_resolved = orm.Required(Date)
        transaction = orm.Optional(lambda: Transaction)

    class Transaction(db.Entity, DictConversionMixin):
        uid = orm.PrimaryKey(str, auto=True)
        min_date_occurred = orm.Required(Date)
        max_date_resolved = orm.Required(Date)
        description = orm.Optional(str)
        ref = orm.Optional(str)
        posts = orm.Set(Post)

    db.generate_mapping(create_tables=True)
