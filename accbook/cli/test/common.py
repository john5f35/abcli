from pathlib import Path

from pony.orm import Database

from accbook.cli.model import init_orm

def setup_db(tmp_path: Path):
    tmpfile = tmp_path / 'tmp.db'

    db = Database(provider='sqlite', filename=str(tmpfile), create_db=True)
    init_orm(db)
    return db, tmpfile