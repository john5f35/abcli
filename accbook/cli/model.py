from datetime import date as Date, timedelta as TimeDelta, datetime as DateTime
from typing import *
from enum import Enum
import json

from accbook.common import JSON_FORMAT, JSON_FORMAT_DATE

import logging

logger = logging.getLogger()    # Root level logger


class ModelObject:
    @staticmethod
    def from_jsonobj(jsonobj: Dict) -> "ModelObject":
        raise NotImplementedError

    def to_jsonobj(self) -> Dict:
        raise NotImplementedError

    def __str__(self) -> str:
        return json.dumps(self.to_jsonobj(), **JSON_FORMAT)

    def __repr__(self) -> str:
        return str(self)

class PeriodUnits(Enum):
    DAY = 'day'
    MONTH = 'month'
    YEAR = 'year'

class Period(ModelObject):
    def __init__(self, quantity: int, unit: PeriodUnits):
        self.quantity = quantity
        self.unit = unit

    @staticmethod
    def from_jsonobj(jsonobj: List[Any]) -> "Period":
        return Period(jsonobj[0], PeriodUnits(jsonobj[1]))

    def to_jsonobj(self) -> List[Any]:
        return [self.quantity, self.unit.value]

    # TODO: define addition unto Period and Date

class Account(ModelObject):
    # name: str
    def __init__(self, name: str):
        self.name = name

    @staticmethod
    def from_jsonobj(jsonobj: Dict) -> "Account":
        return Account(jsonobj['name'])

    def to_jsonobj(self) -> Dict:
        return { 'name': self.name }

class BalanceAccount(Account):  # for Assets & Liability
    # balance_checks: {date: float}
    def __init__(self, name: str, balance_checks: Dict[Date, float]):
        super(name)
        self.balance_checks = balance_checks

    def to_jsonobj(self) -> Dict:
        return {
            'name': self.name,
            'balance_checks': { date.strftime(JSON_FORMAT_DATE): amount for date, amount in self.balance_checks.items() }
        }

    @staticmethod
    def from_jsonobj(jsonobj: Dict) -> "BalaceAccount":
        checks = { DateTime.strptime(date, JSON_FORMAT_DATE): amount for date, amount in jsonobj['balance_checks'].items() }
        return BalanceAccount(jsonobj['name'], checks)

# DB JSON model:

_list_from_jsonobj = lambda cls, l: list(map(cls.from_jsonobj, l))
_list_to_jsonobj = lambda l: list(map(lambda e: e.to_jsonobj(), l))


class Post(ModelObject):
    # account: Account
    # amount: float
    # description: str # can be None
    def __init__(self, account: Account, amount: float, description: str):
        self.account = account
        self.amount = amount
        self.description = description

    @staticmethod
    def from_jsonobj(jsonobj: Dict) -> "Post":
        try:
            account = Account.from_jsonobj(jsonobj['account'])
            return Post(account, jsonobj['amount'], jsonobj.get('description', None))
        except Exception:
            logger.error(f"Failed to parse JSON object: {jsonobj}")
            raise ValueError(Post)

    def to_jsonobj(self) -> Dict:
        obj = {
            'account': self.account.to_jsonobj(),
            'amount': self.amount,
        }
        if self.description:
            obj['description'] = self.description
        return obj


class Transaction(ModelObject): # uid: str
    # date: Calendar
    # ref: str
    # posts: [Post]
    def __init__(self, uid: str, date: Date, refstr: str, posts: List[Post]):
        self.uid = uid
        self.date = date
        self.refstr = refstr
        self.posts = posts

    @staticmethod
    def from_jsonobj(jsonobj: Dict) -> "Transaction":
        try:
            date = DateTime.strptime(jsonobj['date'], JSON_FORMAT_DATE).date()
            posts = _list_from_jsonobj(Post, jsonobj['posts'])
            return Transaction(jsonobj['uid'], date, jsonobj['refstr'], posts)
        except Exception:
            logger.error(f"Failed to parse JSON object: {jsonobj}")
            raise ValueError(Transaction)

    def to_jsonobj(self) -> Dict:
        return {
            'uid': self.uid,
            'date': self.date.strftime(JSON_FORMAT_DATE),
            'refstr': self.refstr,
            'posts': _list_to_jsonobj(self.posts)
        }


class PeriodicTransaction(Transaction):
    # date_from: date
    # period: datetime.timedelta
    def __init__(self, uid: str, date: Date, refstr: str, posts: List[Post], period: Period):
        super(uid, date, refstr, posts)
        self.period = period

    def to_jsonobj(self) -> Dict:
        txn = super().to_jsonobj()
        txn['period'] = self.period.to_jsonobj()
        return txn

    @staticmethod
    def from_jsonobj(jsonobj: Dict) -> "PeriodicTransaction":
        txn = Transaction.from_jsonobj(jsonobj)
        return PeriodicTransaction(txn.uid, txn.date, txn.refstr, txn.posts, Period.from_jsonobj(jsonobj['period']))


class Budget(ModelObject):
    # date_from: date
    # date_to: date
    # budget: {Account: float}
    def __init__(self, date_from: Date, date_to: Date, budget: Dict[Account, float]):
        self.date_from = date_from
        self.date_to = date_to
        self.budget = budget

    def to_jsonobj(self) -> Dict:
        return {
            'date_from': DateTime.strptime(self.date_from, JSON_FORMAT_DATE),
            'date_to': DateTime.strptime(self.date_to, JSON_FORMAT_DATE),
            'budget': { acc.name: amount for acc, amount in self.budget.items() }
        }

    @staticmethod
    def from_jsonobj(jsonobj: Dict) -> "Budget":
        try:
            return Budget(
                DateTime.strptime(jsonobj['date_from'], JSON_FORMAT_DATE),
                DateTime.strptime(jsonobj['date_to'], JSON_FORMAT_DATE),
                { Account(name): amount for name, amount in jsonobj['budget'].items()}
            )
        except Exception:
            logger.error(f"Failed to parse JSON object: {jsonobj}")
            raise ValueError(Transaction)


class AccountBook(ModelObject):
    # transactions: [Transaction]
    # budgets: [Budget]
    # accounts: [Account]
    # periodics: [PeriodicTransaction]
    def __init__(self, accounts: List[Account],
                    transactions: List[Transaction],
                    budgets: List[Budget],
                    periodics: List[PeriodicTransaction]):
        self.accounts = accounts
        self.transactions = transactions
        self.budgets = budgets
        self.periodics = periodics

    @staticmethod
    def from_jsonobj(jsonobj: Dict) -> "AccountBook":
        return AccountBook(
            _list_from_jsonobj(Account, jsonobj.get('accounts', [])),
            _list_from_jsonobj(Transaction, jsonobj.get('transactions', [])),
            _list_from_jsonobj(Budget, jsonobj.get('budgets', [])),
            _list_from_jsonobj(PeriodicTransaction, jsonobj.get('periodics', []))
        )

    def to_jsonobj(self) -> Dict:
        return {
            'accounts': _list_to_jsonobj(self.accounts),
            'transactions': _list_to_jsonobj(self.transactions),
            'budgets': _list_to_jsonobj(self.budgets),
            'periodicts': _list_to_jsonobj(self.periodics)
        }