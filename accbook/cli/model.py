from datetime import date as Date, timedelta as TimeDelta, datetime as DateTime
from decimal import Decimal
import json

from accbook.cli import db

from pony.orm import *


class DictConversionMixin:
    def to_dictrepr(self, visited=set()):
        visited.add(self)

        attrs = self.__class__._get_attrs_(with_collections=True)
        dic = self.to_dict(with_collections=True, related_objects=True)
        for attr in attrs:
            if isinstance(attr, Set):
                attr_set = dic[attr.name]
                res = {}
                for obj in attr_set:
                    if obj not in visited:
                        res[obj.get_pk()] = obj.to_dictrepr(visited)
                dic[attr.name] = res
        return dic


class Account(db.Entity, DictConversionMixin):
    name = PrimaryKey(str)
    posts = Set(lambda: Post)
    budget_items = Set(lambda: BudgetItem)


class BalanceAccount(Account):
    date = Required(Date)
    balance = Required(Decimal, precision=16, scale=2)


class Post(db.Entity, DictConversionMixin):
    account = Required(Account)
    amount = Required(Decimal, precision=16, scale=2)
    description = Optional(str)
    transaction = Optional(lambda: Transaction)


class Transaction(db.Entity, DictConversionMixin):
    uid = PrimaryKey(str)
    date = Required(Date)
    posts = Set(Post)


class PeriodicTransaction(Transaction):
    date_from = Required(Date)
    period = Required(TimeDelta)


class Budget(db.Entity, DictConversionMixin):
    date_from = Required(Date)
    date_to = Required(Date)
    items = Set(lambda: BudgetItem)

class BudgetItem(db.Entity, DictConversionMixin):
    account = Required(Account)
    amount = Required(Decimal, precision=16, scale=2)
    budget = Optional(Budget)