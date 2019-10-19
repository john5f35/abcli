# abcli
A command line tool for transaction tracking and budgeting.

Ideas are taken from [beancount](http://furius.ca/beancount/)
and [double entry accounting method](https://docs.google.com/document/d/100tGcA4blh6KSXPRGCZpUlyxaRUwFHEvnz_k9DyZFn4/edit).

**NOTE**: Currently only CSVs exported from Commonwealth Bank of Australia are supported.

## Requirements

- Python 3.6+;
- `pipenv`;
- database back-end (e.g. Postgres)

## Install

```
$ git clone git@github.com:john5f35/account-book-cli.git
$ cd account-book-cli
$ pipenv install
```

## Usage
### Config JSON
First set up a config file:

SQLite:
```json
{
  "db": {
    "provider": "sqlite",
    "filename": "accbook-sqlite.db",
    "create_db": true
  }
}
```

Postgres:
```json
{
  "db": {
    "provider": "postgres",
    "database": "accbook",
    "user": "johnz",
    "host": "localhost",
    "port": 5432
  }
}
```

See [PonyORM Doc - Supported databases](https://docs.ponyorm.org/api_reference.html#supported-databases)
for supported database and relevant arguments in config file.

SQLite DB file can be created anew; other DBs will need the DB setup and running for abcli to connect to it.

```
$ pipenv run python abcli
Loading .env environment variables…
Usage: abcli [OPTIONS] COMMAND [ARGS]...

Options:
  --log-level [CRITICAL|FATAL|ERROR|WARN|WARNING|INFO|DEBUG|NOTSET]
                                  Set the root logger level
  -c, --config PATH               Path to config JSON file
  --help                          Show this message and exit.

Commands:
  account
  balance
  budget
  csv
  transaction
```
### Commands

#### CSV -- classifying and importing transaction CSVs
##### Prep
Use `ablic csv prep` to reformat the CSV for classification.

```
python abcli csv prep --help                                                                                                                                                                                                     [INSERT]
Usage: abcli csv prep [OPTIONS] CSVPATH

Options:
  -a, --this TEXT  The operating account name  [required]
  --help           Show this message and exit.
```
The prepared CSV will have the column format:

|      field       |                                                                description                                                                |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `date_occurred`  | The date on which the transaction occurred (enter into pending state)                                                                     |
| `date_resolved`  | The date on which the transaction resolved (pending -> resolved)                                                                          |
| `amount`         | The amount of the transfer                                                                                                                |
| `description`    | The description from the bank                                                                                                             |
| `balance`        | Balance in the operating account after the transaction                                                                                    |
| `this`           | The account from which the transaction originates; should just be the operating account                                                   |
| `that_auto`      | The automatically classified destination (category) account of the transaction                                                            |
| `that_overwrite` | Overriding the automated classification; can be the name of the account, or a [split dictionary](#split-dictionary) for transaction split |
| `ref`            | A `@` prefixed reference tag to merge relevant transactions in later processing                                                           |

##### Classify
Use `abcli csv classify` to classify prepared transaction CSVs according to a [rulebook](#rulebook):
```
python abcli csv classify --help                                                                                                                                                                                                 [INSERT]
Usage: abcli csv classify [OPTIONS] CSVPATH

Options:
  -r, --rulebook FILE  Rule book JSON file for assigning accounts/categories;
                       default can be specified in config.json
  --help               Show this message and exit.
```
###### split dictionary

Both fields be customised into Python dictionary strings, so to split the transaction into finer postings.
This can help dealing with aggregated transactions, allowing them to be tracked separately.

E.g.:
```csv
date_occurred,date_resolved,amount,description,balance,this,that_auto,that_overwrite,ref
23/06/2019,26/06/2019,-52.50,Group Dine Out,...,Assets:Bank:Commonwealth:Checking,,"{'Expenses:Food&Drink:Restaurant': 15.00, 'Expenses:Misc:Lent': 37.50}",@dinout23jun
```

The group dine out transaction of `$52.50` is split into personal spending of `$15.00` in `Expenses:Food&Drink:Restaurant` category account, and "lent" spending of `$37.50`.
The reference tag `@dinout23jun` is attached to this and other pay-back transactions to resolve the `$37.50` lent money.

#### Rulebook
A yaml file that allow keyword or regex matching on transaction description.

Keywords are searched in top-down, first-match fashion.
The matched value will be written to the transaction's `that_auto` field.

A rule can also override `this` field in the CSV as well:
```yaml
keyword:
    Dinner: "Expenses:Food&Drink:Restaurants"
    food reimb:
        this: "Income:Reimbursements"
        that_auto: "Expenses:Misc:Lent"
regex:
    .*(Comm|Net)Bank.*: "Assets:Bank:Savings"
```

#### Transaction -- import and summarise transactions

Once `abcli csv classify` says it's 100% classified, you can run `abcli transaction import` to import the classified csv file into your database.
Then you can query it using the `summary` and `show` command:

```
$ python abcli transaction summary -m 04/2018 -d 2
account                 amount    % of parent
-------------------  ---------  -------------
Income               -$5432.00
├── Work1            -$3521.00         64.82%
└── Work2            -$1911.00         35.18%
Expenses              $3681.26
├── Food&Drink         $700.39         19.03%
├── Charity             $92.00          2.50%
├── Transport           $78.85          2.14%
├── Personal           $151.86          4.13%
├── Bills&Utilities    $128.91          3.50%
├── Misc                $83.39          2.27%
├── Housing            $640.00         17.39%
├── Government        $1595.00         43.33%
├── Healthcare          $72.00          1.96%
└── Hobbies            $138.86          3.77%
```

#### Budget -- show progress of budget

You can write up a budget in YAML format, and run `abcli budget progress` to get the progress report on the budget:
```
$ cat testbudget.yaml
date_from: 01/04/2018
date_to:   30/04/2018
items:
  'Expenses:Food&Drink': 4000
  'Expenses:Bills&Utilities': 130
  'Expenses:Transport': 60
  'Expenses:Bills&Utilities:Phone': 120
  'Expenses:Bills&Utilities:Internet': 20

$ python abcli budget progress testbudget.yaml
account_name           budgeted    % of parent    consumed  progress
-------------------  ----------  -------------  ----------  ----------
Income
Expenses               $4330.00                   $3681.26  85.02%
├── Food&Drink         $4000.00         92.38%     $700.39  17.51%
├── Bills&Utilities     $270.00          6.24%     $128.91  47.74%
│   ├── Phone           $120.00         44.44%     $120.51  100.43%
│   └── Internet         $20.00          7.41%      $20.00  100.00%
└── Transport            $60.00          1.39%      $78.85  131.42%
Assets
Liabilities
```

As the accounts are presented in trees, sub-categories are summed at parent level.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)