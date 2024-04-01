from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

import base64
import imghdr  # Import imghdr module for determining image format

bp = Blueprint('blog', __name__)

# Template function to generate HTML for displaying movie poster
@bp.app_template_global()
def check_movie_poster(image_data):
    if image_data:
        # Determine the image format dynamically
        image_format = imghdr.what(None, h=image_data)
    if image_format:
        return image_format
    else:
        return None


@bp.app_template_global()
def encode_movie_poster(image_data):
    if image_data:
        verified = check_movie_poster(image_data)
        # Convert binary image data to Base64 encoding
        if verified:
            base64_image = base64.b64encode(image_data)

            # Return HTML with embedded Base64-encoded image data and determined image format
            return base64_image
        else:
            return None
    else:
        return None


@bp.app_template_global()
def build_poster_string(image_data):
    verified = check_movie_poster(image_data)
    if verified:
        encoding = encode_movie_poster(image_data)
        if encoding:
            return "<img src=\"data:image/" + verified + ";base64, " + encoding.decode('utf-8') + "\" alt=\"Movie Poster\">"
@bp.route('/')
def index():
    db = get_db()
    entries = db.execute(
        'SELECT e.id, title, release_year, starring, synopsis, data, edited, author_id, username'
        ' FROM entry AS e LEFT JOIN images AS i ON e.id = i.movie_id INNER JOIN user AS u ON e.id = u.id'
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
        poster = request.files['poster']
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
            if poster is not None:
                theEntry = db.execute(
                            'SELECT e.id, author_id, title'
                            ' FROM entry e'
                            ' WHERE e.title = ?', (title,)).fetchone()
                db.execute('INSERT INTO images (filename, data, user_id, movie_id)'
                           ' VALUES (?, ?, ?, ?)',
                           (poster.filename, poster.read(), g.user['id'], theEntry['id'],))
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
        poster = request.files['poster']
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
            if poster is not None:
                theEntry = db.execute(
                    'SELECT e.id, author_id, title'
                    ' FROM entry e'
                    ' WHERE e.title = ?', (title,)).fetchone()
                db.execute('UPDATE images SET filename = ?, data = ?, user_id = ?'
                           ' WHERE id = ?',
                           (poster.filename, poster.read(), g.user['id'], theEntry['id'],))

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