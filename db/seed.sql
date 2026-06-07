-- Add some test users
INSERT INTO users (name, email) VALUES
    ('Simon',  'simon@example.com'),
    ('Alex',   'alex@example.com'),
    ('Maria',  'maria@example.com');

-- Populate available genres
INSERT INTO genres (name) VALUES
    ('Action'),
    ('Drama'),
    ('Sci-Fi'),
    ('Comedy'),
    ('Thriller'),
    ('Animation'),
    ('Crime'),
    ('Romance');

-- Insert initial film catalogue
INSERT INTO movies (title, year, description) VALUES
    ('Blade Runner 2049', 2017, 'A young blade runner uncovers a secret that could plunge what is left of society into chaos.'),
    ('The Grand Budapest Hotel', 2014, 'A concierge and his protege become embroiled in the theft of a priceless painting.'),
    ('Parasite', 2019, 'A poor family schemes to become employed by a wealthy household.'),
    ('Mad Max: Fury Road', 2015, 'On a post-apocalyptic desert, a woman rebels against a tyrannical ruler.'),
    ('Her', 2013, 'A lonely writer develops a relationship with an operating system.'),
    ('Spirited Away', 2001, 'A girl wanders into a world of spirits and must find a way to free her family.'),
    ('Whiplash', 2014, 'A young drummer enrolls at a conservatory under a ruthless instructor.'),
    ('Arrival', 2016, 'A linguist is recruited to communicate with extraterrestrial visitors.'),
    ('No Country for Old Men', 2007, 'Violence and chaos follow a hunter who stumbles upon drug-deal money.'),
    ('La La Land', 2016, 'A jazz musician and an aspiring actress fall in love in Los Angeles.'),
    ('Dune', 2021, 'A noble family becomes embroiled in a war over a desert planet and its precious resource.'),
    ('The Social Network', 2010, 'The founding of a social-networking website and the lawsuits that followed.');

-- Connect movies to genres using titles and names instead of hardcoded IDs
INSERT INTO movie_genres (movie_id, genre_id)
SELECT m.movie_id, g.genre_id
FROM (VALUES
    ('Blade Runner 2049',        'Sci-Fi'),
    ('Blade Runner 2049',        'Thriller'),
    ('The Grand Budapest Hotel', 'Comedy'),
    ('The Grand Budapest Hotel', 'Drama'),
    ('Parasite',                 'Thriller'),
    ('Parasite',                 'Drama'),
    ('Mad Max: Fury Road',       'Action'),
    ('Mad Max: Fury Road',       'Sci-Fi'),
    ('Her',                      'Drama'),
    ('Her',                      'Romance'),
    ('Her',                      'Sci-Fi'),
    ('Spirited Away',            'Animation'),
    ('Whiplash',                 'Drama'),
    ('Arrival',                  'Sci-Fi'),
    ('Arrival',                  'Drama'),
    ('No Country for Old Men',   'Crime'),
    ('No Country for Old Men',   'Thriller'),
    ('La La Land',               'Romance'),
    ('La La Land',               'Drama'),
    ('Dune',                     'Sci-Fi'),
    ('Dune',                     'Action'),
    ('The Social Network',       'Drama')
) AS link(title, gname)
JOIN movies m ON m.title = link.title
JOIN genres g ON g.name  = link.gname;

-- Add initial movie ratings (the trigger updates movies.avg_rating automatically)
INSERT INTO ratings (user_id, movie_id, score)
SELECT u.user_id, m.movie_id, r.score
FROM (VALUES
    ('Simon', 'Blade Runner 2049',        9),
    ('Alex',  'Blade Runner 2049',        8),
    ('Maria', 'Parasite',                10),
    ('Simon', 'Parasite',                 9),
    ('Alex',  'Whiplash',                10),
    ('Maria', 'Spirited Away',            9),
    ('Simon', 'Dune',                      8),
    ('Alex',  'La La Land',                7),
    ('Maria', 'Arrival',                   8)
) AS r(uname, title, score)
JOIN users  u ON u.name  = r.uname
JOIN movies m ON m.title = r.title;

-- Add sample user reviews
INSERT INTO reviews (user_id, movie_id, text)
SELECT u.user_id, m.movie_id, rv.text
FROM (VALUES
    ('Simon', 'Blade Runner 2049', 'Stunning visuals and a haunting score.'),
    ('Maria', 'Parasite',          'Razor-sharp and unpredictable from start to finish.'),
    ('Alex',  'Whiplash',          'Tense, brutal, and completely gripping.')
) AS rv(uname, title, text)
JOIN users  u ON u.name  = rv.uname
JOIN movies m ON m.title = rv.title;

-- Add movies to sample watchlists
INSERT INTO watchlist_entries (user_id, movie_id)
SELECT u.user_id, m.movie_id
FROM (VALUES
    ('Simon', 'Dune'),
    ('Simon', 'Arrival'),
    ('Alex',  'Her')
) AS w(uname, title)
JOIN users  u ON u.name  = w.uname
JOIN movies m ON m.title = w.title;
