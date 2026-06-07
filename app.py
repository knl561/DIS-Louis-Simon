"""
This is our Flask app for Movie Explorer running on top of PostgreSQL.

It shows off the course requirements:
  * SQL actions like SELECT, INSERT, and UPDATE.
  * Regex search using Postgres POSIX (~* operator).
  * Bonus items like our view (movie_overview) and the rating trigger.

We didn't build a full login system with passwords. Instead, we just track the 
active user in the session. You can swap users in the header to test ratings and watchlists.
"""
import re
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, abort
)

import db

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"  # only used for flash + session


def current_user_id():
    """
    Finds the active user ID. If nobody is picked yet, it just defaults 
    to the first user in the database so the app doesn't break.
    """
    uid = session.get("user_id")
    if uid is None:
        row = db.query_one("SELECT user_id FROM users ORDER BY user_id LIMIT 1")
        uid = row["user_id"] if row else None
        session["user_id"] = uid
    return uid


@app.context_processor
def inject_users():
    """Makes sure all templates can see the user list and who is active."""
    users = db.query("SELECT user_id, name FROM users ORDER BY name")
    return {"all_users": users, "current_user_id": current_user_id()}


@app.route("/switch-user", methods=["POST"])
def switch_user():
    """Saves the newly picked user to the session and reloads the page."""
    session["user_id"] = int(request.form["user_id"])
    return redirect(request.referrer or url_for("index"))


@app.route("/")
def index():
    """Handles the main browse page, including text searches and dropdown filters."""
    q = (request.args.get("q") or "").strip()
    genre_id = request.args.get("genre")
    year = request.args.get("year")

    where = []
    params = []
    regex_error = None

    """
    Checks the search box text against the title using Postgres regex (~*).
    We test it in Python first so a typo in the regex shows a nice message 
    instead of crashing the database.
    """
    if q:
        try:
            re.compile(q)
            where.append("mo.title ~* %s")
            params.append(q)
        except re.error as exc:
            regex_error = f"Invalid search pattern: {exc}"

    if genre_id:
        """Filters the movie list by checking if the genre connection exists."""
        where.append(
            "EXISTS (SELECT 1 FROM movie_genres mg "
            "WHERE mg.movie_id = mo.movie_id AND mg.genre_id = %s)"
        )
        params.append(int(genre_id))

    if year:
        """Filters movies by the exact release year."""
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


@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    """Loads the specific page for a single film along with its reviews and user status."""
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


@app.route("/movie/<int:movie_id>/rate", methods=["POST"])
def rate_movie(movie_id):
    """Saves a score. Uses an ON CONFLICT upsert so users update their old score instead of duplicating rows."""
    score = int(request.form["score"])
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
    """Saves a text review for the movie as long as the comment box wasn't empty."""
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
    """Flips the watchlist button. Removes the film if it's there, adds it if it isn't."""
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


@app.route("/watchlist")
def watchlist():
    """Gathers and shows all the films saved by the active user, sorting by newest additions first."""
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
