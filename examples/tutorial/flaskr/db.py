import re

import mysql.connector as mysql
import click
from flask import current_app
from flask import g
from flask.cli import with_appcontext


def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:
        g.db =  mysql.connect(host='localhost',
                              port='3306',
                              user='root',
                              password='8CgNkES97Zu19eix077O7t5qgDrMkXj@',
                              database='example',
                              use_pure=True)

    return g.db


def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()


def execute_sql_from_file(cnx, f):
    """Executing SQL Statements from a Text File."""
    cur = cnx.cursor(buffered=True)
    lines = f.read().decode('utf-8').split('\n')
    statement = ""

    for line in lines:
        if re.match(r'--', line) or line == '\n': # ignore sql comment lines
            continue
        if not re.search(r';$', line): # keep appending lines that don't end in ';'
            statement += line
        else:
            statement += line
            try:
                cur.execute(statement)
            except Exception as e:
                print("Error during execute statement.\n{0}".format(str(e.args)))
                break
            statement = ""

        cnx.commit()
    return


def init_db():
    """Clear existing data and create new tables."""
    cnx = get_db()

    with current_app.open_resource("schema.sql") as f:
        execute_sql_from_file(cnx, f)

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
