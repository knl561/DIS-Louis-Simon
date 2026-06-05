"""
Movie Explorer — a small Flask web-app on top of PostgreSQL.

Demonstrates, as required by the project brief:
  * SQL interaction (SELECT / INSERT / UPDATE)
  * Regular-expression matching (PostgreSQL POSIX `~*`, see /search)
  * Bonus: a view (movie_overview), a trigger + stored function (avg_rating)

There is no login system. Instead a "current user" is kept in the session
and can be switched from the header — enough to make ratings, reviews and
watchlists meaningful without building authentication.
"""
import re
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, abort
)

import db

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"  # only used for flash + session


# ----------------------------------------------------------------------
#  Current-user helpers (stand-in for real authentication)
# ----------------------------------------------------------------------
def current_user_id():
    """The active user id, defaulting to the first user in the database."""
    uid = session.get("user_id")
    if uid is None:
        row = db.query_one("SELECT user_id FROM users ORDER BY user_id LIMIT 1")
        uid = row["user_id"] if row else None
        session["user_id"] = uid
    return uid


@app.context_processor
def inject_users():
    """Make the user list + current user available to every template."""
    users = db.query("SELECT user_id, name FROM users ORDER BY name")
    return {"all_users": users, "current_user_id": current_user_id()}


@app.route("/switch-user", methods=["POST"])
def switch_user():
    session["user_id"] = int(request.form["user_id"])
    return redirect(request.referrer or url_for("index"))


# ----------------------------------------------------------------------
#  Browse / search / filter  (SELECT + regex)
# ----------------------------------------------------------------------
@app.route("/")
def index():
    q = (request.args.get("q") or "").strip()
    genre_id = request.args.get("genre")
    year = request.args.get("year")

    where = []
    params = []
    regex_error = None

    # --- Regular-expression matching on the title ---
    # The search box is treated as a POSIX regular expression and matched
    # case-insensitively with PostgreSQL's `~*` operator. We validate the
    # pattern in Python first so a bad pattern gives a friendly message
    # instead of a database error.
    if q:
        try:
            re.compile(q)
            where.append("mo.title ~* %s")
            params.append(q)
        except re.error as exc:
            regex_error = f"Invalid search pattern: {exc}"

    if genre_id:
        where.append(
            "EXISTS (SELECT 1 FROM movie_genres mg "
            "WHERE mg.movie_id = mo.movie_id AND mg.genre_id = %s)"
        )
        params.append(int(genre_id))

    if year:
        where.append("mo.year = %s")
        params.append(int(year))

    sql = "SELECT * FROM movie_overview mo"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY mo.title"

    movies = [] if regex_error else db.query(sql, params)

    genres = db.query("SELECT genre_id, name FROM genres ORDER BY name")
    years = db.query(
        "SELECT DISTINCT year FROM movies WHERE year IS NOT NULL ORDER BY year DESC"
    )

    return render_template(
        "index.html",
        movies=movies,
        genres=genres,
        years=years,
        q=q,
        selected_genre=int(genre_id) if genre_id else None,
        selected_year=int(year) if year else None,
        regex_error=regex_error,
    )


# ----------------------------------------------------------------------
#  Movie detail
# ----------------------------------------------------------------------
@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    movie = db.query_one(
        "SELECT * FROM movie_overview WHERE movie_id = %s", (movie_id,)
    )
    if movie is None:
        abort(404)

    reviews = db.query(
        """SELECT r.text, r.created_at, u.name AS author
             FROM reviews r JOIN users u ON u.user_id = r.user_id
            WHERE r.movie_id = %s
            ORDER BY r.created_at DESC""",
        (movie_id,),
    )

    my_rating = db.query_one(
        "SELECT score FROM ratings WHERE movie_id = %s AND user_id = %s",
        (movie_id, current_user_id()),
    )

    on_watchlist = db.query_one(
        "SELECT 1 FROM watchlist_entries WHERE movie_id = %s AND user_id = %s",
        (movie_id, current_user_id()),
    ) is not None

    return render_template(
        "movie.html",
        movie=movie,
        reviews=reviews,
        my_rating=my_rating["score"] if my_rating else None,
        on_watchlist=on_watchlist,
    )


# ----------------------------------------------------------------------
#  Write operations: rate / review / watchlist  (INSERT + UPDATE)
# ----------------------------------------------------------------------
@app.route("/movie/<int:movie_id>/rate", methods=["POST"])
def rate_movie(movie_id):
    score = int(request.form["score"])
    # One rating per (user, movie): INSERT, or UPDATE if it already exists.
    db.execute(
        """INSERT INTO ratings (user_id, movie_id, score)
                VALUES (%s, %s, %s)
           ON CONFLICT (user_id, movie_id)
                DO UPDATE SET score = EXCLUDED.score""",
        (current_user_id(), movie_id, score),
    )
    flash(f"Your rating ({score}/10) was saved.")
    return redirect(url_for("movie_detail", movie_id=movie_id))


@app.route("/movie/<int:movie_id>/review", methods=["POST"])
def review_movie(movie_id):
    text = (request.form.get("text") or "").strip()
    if text:
        db.execute(
            "INSERT INTO reviews (user_id, movie_id, text) VALUES (%s, %s, %s)",
            (current_user_id(), movie_id, text),
        )
        flash("Your review was posted.")
    return redirect(url_for("movie_detail", movie_id=movie_id))


@app.route("/movie/<int:movie_id>/watchlist", methods=["POST"])
def toggle_watchlist(movie_id):
    uid = current_user_id()
    exists = db.query_one(
        "SELECT 1 FROM watchlist_entries WHERE movie_id = %s AND user_id = %s",
        (movie_id, uid),
    )
    if exists:
        db.execute(
            "DELETE FROM watchlist_entries WHERE movie_id = %s AND user_id = %s",
            (movie_id, uid),
        )
        flash("Removed from your watchlist.")
    else:
        db.execute(
            "INSERT INTO watchlist_entries (user_id, movie_id) VALUES (%s, %s)",
            (uid, movie_id),
        )
        flash("Added to your watchlist.")
    return redirect(request.referrer or url_for("movie_detail", movie_id=movie_id))


# ----------------------------------------------------------------------
#  Watchlist page
# ----------------------------------------------------------------------
@app.route("/watchlist")
def watchlist():
    movies = db.query(
        """SELECT mo.*, w.added_at
             FROM watchlist_entries w
             JOIN movie_overview mo ON mo.movie_id = w.movie_id
            WHERE w.user_id = %s
            ORDER BY w.added_at DESC""",
        (current_user_id(),),
    )
    return render_template("watchlist.html", movies=movies)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, port=port)
