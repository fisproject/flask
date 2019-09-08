from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
from memory_profiler import profile

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("blog", __name__)


@bp.route("/")
@profile(precision=4)
def index():
    """Show all the posts, most recent first."""
    cur = get_db().cursor(buffered=True)
    cur.execute(
        "SELECT p.id, title, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    )
    resp = cur.fetchall()

    keys = ['id', 'title', 'body', 'created', 'author_id', 'username']
    posts = []
    for tup in resp:
        post = {}
        for k, v in zip(keys, tup):
            post[k] = v
        posts.append(post)

    return render_template("blog/index.html", posts=posts)


@profile(precision=4)
def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    cur = get_db().cursor(buffered=True)
    cur.execute(
        "SELECT p.id, title, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " WHERE p.id = %s",
        (id,),)
    resp = cur.fetchone()

    if resp is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    keys = ['id', 'title', 'body', 'created', 'author_id', 'username']
    post = {}
    for k, v in zip(keys, resp):
        post[k] = v

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
@profile(precision=4)
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            cnx = get_db()
            cur = cnx.cursor(buffered=True)
            cur.execute(
                "INSERT INTO post (title, body, author_id) VALUES (%s, %s, %s)",
                (title, body, g.user["id"]),
            )
            cnx.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
@profile(precision=4)
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            cnx = get_db()
            cur = cnx.cursor(buffered=True)
            cur.execute(
                "UPDATE post SET title = %s, body = %s WHERE id = %s", (title, body, id)
            )
            cnx.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    cnx = get_db()
    cur = cnx.cursor(buffered=True)
    cur.execute("DELETE FROM post WHERE id = %s", (id,))
    cnx.commit()
    return redirect(url_for("blog.index"))
