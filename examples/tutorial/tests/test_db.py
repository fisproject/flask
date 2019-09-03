import mysql.connector as mysql

import pytest

from flaskr.db import get_db


def test_get_close_db(app):
    with app.app_context():
        cnx = get_db()
        assert cnx is get_db()

    with pytest.raises(mysql.errors.OperationalError) as e:
        cur = cnx.cursor(buffered=True)
        cur.execute("SELECT 1")
        cnx.close()

    assert "MySQL Connection not available." in str(e.value)


def test_init_db_command(runner, monkeypatch):
    class Recorder(object):
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr("flaskr.db.init_db", fake_init_db)
    result = runner.invoke(args=["init-db"])
    assert "Initialized" in result.output
    assert Recorder.called
