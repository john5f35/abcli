# account-book-cli
A set of command line tools for transaction tracking and budgeting
Ideas are taken from [beancount](http://furius.ca/beancount/)
and [double entry accounting method](https://docs.google.com/document/d/100tGcA4blh6KSXPRGCZpUlyxaRUwFHEvnz_k9DyZFn4/edit).

## `classify.py` -- classify bank csv transactions & initial processing

### CSV format
Currently only exports from Commonwealth Bank is known and supported

Each row in csv has the following fields:

| field   | description                                                     |
| ------- | --------------------------------------------------------------- |
| date    | date of the transaction                                         |
| amount  | amount of this transaction                                      |
| desc    | description (from bank)                                         |
| balance | balance field from bank                                         |
| this    | operating account; can be blank to be specified by other script |
| that    | transaction target account; blank means unclassified            |
| ref     | a ref tag for merging related transactions                      |
| tags    | other tags for this transaction (unprocessed)                   |

#### this & that account
`this` account is what _amount_ and _balance_ apply to.
`that` account is the transaction target account.

Both fields be customised into Python dictionary strings, so to split the transaction into finer postings.
This can help dealing with aggregated transactions, allowing them to be tracked separately.

E.g.:
```csv
date,amount,desc,balance,this,that,ref,tags
02/02/2019,-123.00,some description,+5789,,"{'Expenses:category1': -23.00, 'Expenses:category2': -100.00}",,
...
02/02/2019,+1000.00,some description,+5673,"{'Income:category1': +200.00, 'Income:category2': +800.00}",,,
```

#### Rulebook
A yaml file that allow keyword or regex matching on transaction description.
The rule value is the `that` account.

`this` account overwrite is supported through dictionary.

E.g.
```yaml
keyword:
    Dinner: "Expenses:Food&Drink:Restaurants"
    food reimb:
        this: "Income:Reimbursements"
        that: "Expenses:Misc:Lent"
regex:
    .*(Comm|Net)Bank.*: "Assets:Bank:Savings"
```
