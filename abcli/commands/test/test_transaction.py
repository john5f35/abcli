from datetime import date

from pony import orm

from abcli.commands.transaction import get_posts_between_period
from abcli.model import init_orm


def test_get_posts_between_period():
    orm.set_sql_debug(True)
    db = orm.Database(provider='sqlite', filename=':memory:', create_db=True)
    init_orm(db)

    with orm.db_session:
        db.Post(date_occurred=date(2019, 1, 2), date_resolved=date(2019, 1, 4), account=db.Account(name='A'), amount=123)

        def captured_post(date_from, date_to, include_nonresolved):
            return len(get_posts_between_period(db, date_from, date_to, include_nonresolved)) == 1

        assert captured_post(date(2019, 1, 1), date(2019, 1, 5), False)
        assert captured_post(date(2019, 1, 1), date(2019, 1, 5), True)

        assert captured_post(date(2019, 1, 1), date(2019, 1, 4), False)
        assert captured_post(date(2019, 1, 1), date(2019, 1, 4), True)
        assert captured_post(date(2019, 1, 2), date(2019, 1, 4), False)
        assert captured_post(date(2019, 1, 2), date(2019, 1, 4), True)

        assert not captured_post(date(2019, 1, 1), date(2019, 1, 3), False)
        assert captured_post(date(2019, 1, 1), date(2019, 1, 3), True)

        assert not captured_post(date(2019, 1, 2), date(2019, 1, 3), False)
        assert captured_post(date(2019, 1, 2), date(2019, 1, 3), True)

        assert not captured_post(date(2019, 1, 3), date(2019, 1, 3), False)
        assert captured_post(date(2019, 1, 3), date(2019, 1, 3), True)

