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
