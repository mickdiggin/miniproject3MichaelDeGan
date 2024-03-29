from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    entries = db.execute(
        'SELECT e.id, title, release_year, starring, synopsis, edited, author_id, username'
        ' FROM entry e JOIN user u ON e.author_id = u.id'
        ' ORDER BY edited DESC'
    ).fetchall()
    return render_template('blog/index.html', entries=entries)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        releaseYr = request.form['release_year']
        starring = request.form['starring']
        synopsis = request.form['synopsis']
        error = None

        if not title:
            error = 'Title is required.'
        if not synopsis:
            error = 'Synopsis is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO entry (title, release_year, starring, synopsis, author_id)'
                ' VALUES (?, ?, ?, ?, ?)',
                (title, releaseYr, starring, synopsis, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_entry(id, check_author=False):
    entry = get_db().execute(
        'SELECT e.id, title, release_year, starring, synopsis, edited, author_id, username'
        ' FROM entry e JOIN user u ON e.author_id = u.id'
        ' WHERE e.id = ?',
        (id,)
    ).fetchone()

    if entry is None:
        abort(404, f"Post id {id} doesn't exist.")

    return entry


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    entry = get_entry(id)

    if request.method == 'POST':
        title = request.form['title']
        release_year = request.form['release_year']
        starring = request.form['starring']
        synopsis = request.form['synopsis']
        error = None

        if not title:
            error = 'Title is required.'
        if not synopsis:
            error = 'Synopsis is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE entry SET title = ?, release_year = ?, starring = ?, synopsis = ?, author_id = ?'
                ' WHERE id = ?',
                (title, release_year, starring, synopsis, g.user['id'], id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', entry=entry)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_entry(id)
    db = get_db()
    db.execute('DELETE FROM entry WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))