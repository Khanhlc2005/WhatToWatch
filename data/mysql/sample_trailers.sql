-- YouTube trailer keys already present in data/seeds/movies_cleaned_sample.jsonl.
-- Keep any trailer key supplied by a fuller dataset.
UPDATE movies SET trailer_key = 'Ew9ngL1GZvs', trailer_site = 'YouTube', trailer_type = 'Trailer'
WHERE imdb_id = 'tt0068646' AND (trailer_key IS NULL OR trailer_key = '');
UPDATE movies SET trailer_key = 'BdJKm16Co6M', trailer_site = 'YouTube', trailer_type = 'Trailer'
WHERE imdb_id = 'tt0137523' AND (trailer_key IS NULL OR trailer_key = '');
UPDATE movies SET trailer_key = 'zSWdZVtXT7E', trailer_site = 'YouTube', trailer_type = 'Trailer'
WHERE imdb_id = 'tt0816692' AND (trailer_key IS NULL OR trailer_key = '');
