# Movie Explorer

A small web-app for browsing films and managing personal ratings, reviews and
watchlists, built for the DIS database project. Stack: **Python + Flask +
PostgreSQL** (the recommended stack from the lecture slides).

Users can:

- browse the film catalogue
- search titles (with **regular-expression matching**)
- filter by genre or year
- rate films (1–10)
- write reviews
- save films to a personal watchlist

---

## E/R model

The schema implements the project's E/R diagram directly:

| Entity / relationship | Table                |
|-----------------------|----------------------|
| User                  | `users`              |
| Movie                 | `movies`             |
| Genre                 | `genres`             |
| MovieGenre            | `movie_genres`       |
| Review                | `reviews`            |
| Rating                | `ratings`            |
| WatchlistEntry        | `watchlist_entries`  |

See `db/schema.sql`.

---

## Prerequisites

- PostgreSQL 16 (with `psql` and `createdb` on your PATH)
- Python 3.10+

---

## 1. Compile / set up

```bash
# from the project root
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Initialise the database

Make sure PostgreSQL is running, then:

```bash
bash scripts/init_db.sh
```

This creates a database called `movie_explorer` and loads `db/schema.sql`
followed by `db/seed.sql`. To use different connection details:

```bash
DB_NAME=movie_explorer PGUSER=postgres PGHOST=localhost bash scripts/init_db.sh
```

(You can also run the two SQL files by hand:
`psql -d movie_explorer -f db/schema.sql` then `... -f db/seed.sql`.)

## 3. Run

```bash
# tell the app how to reach the database (adjust user/password as needed)
export DATABASE_URL="postgresql://postgres@localhost:5432/movie_explorer"

python app.py
```

Then open <http://localhost:5001>.

## 4. Interact

- **Browse** — the home page lists every film.
- **Search** — type in the search box. The input is a POSIX regular
  expression matched case-insensitively against the title, e.g.
  `^The` (titles starting with "The"), `Dune|Her`, `20(1[5-9]|2.)`.
- **Filter** — pick a genre and/or year and press *Apply*.
- **Rate / review / watchlist** — open a film and use the buttons.
- **Viewing as** — switch the active user from the header (no login system;
  this stand-in keeps ratings/reviews/watchlists per-user).

---

## Where each requirement is met

- **SQL interaction** — `SELECT` throughout (`app.py` + the `movie_overview`
  view), `INSERT` for reviews/ratings/watchlist, and `UPDATE` via the
  `INSERT … ON CONFLICT … DO UPDATE` on `ratings` (re-rating a film).
- **Regular-expression matching** — the search route validates the pattern in
  Python (`re.compile`) and matches it in PostgreSQL with the `~*` operator
  (`app.py`, `index()`).
- **Bonus — view:** `movie_overview` (`db/schema.sql`).
- **Bonus — stored function + trigger:** `recompute_avg_rating()` and
  `trg_ratings_avg` keep `movies.avg_rating` in sync automatically whenever a
  rating is inserted, updated or deleted (`db/schema.sql`).

---

## Project layout

```
movie-explorer/
├── app.py                # Flask routes
├── db.py                 # database connection + query helpers
├── requirements.txt
├── db/
│   ├── schema.sql        # tables, view, trigger, function
│   └── seed.sql          # sample data
├── scripts/
│   └── init_db.sh        # create db + load schema + seed
├── templates/            # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   ├── movie.html
│   └── watchlist.html
└── static/
    └── style.css
```

---

## AI declaration

This project was developed with assistance from an AI assistant (Anthropic's
Claude). AI was used to help scaffold the Flask application structure, the
PostgreSQL schema, and the HTML/CSS, based on the group's E/R model and
project idea. All AI-assisted code was reviewed and tested by the group.

<!-- Adjust this declaration to reflect your group's actual usage before
     submitting. If no AI was used on a part, say so; the brief requires the
     declaration either way. -->
