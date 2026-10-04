"""Validation JSONL theo luồng, đối chiếu checkpoint/cache; tuyệt đối không gọi mạng."""

import argparse
from collections import Counter
import json
from pathlib import Path
import random
import re
import sqlite3
from tempfile import TemporaryDirectory

from catalog_inventory import fingerprint
from clean_movies import clean_movie, IMDB_ID_PATTERN, MISSING_CHECK_FIELDS
from embedding_template import build_embedding_text, TEXT_TEMPLATE_VERSION
from full_catalog import atomic_json, transform, valid_details


def strict_json(value):
    def reject_constant(value):
        raise ValueError('non_finite_json')
    return json.loads(value, parse_constant=reject_constant)


def validate(path, database, cache, sample, require_complete=False):
    """Return bounded diagnostics and a deterministic reservoir for manual review.

    A passing subset report does not certify full catalog coverage. Raw cache is
    independently transformed and compared against every exported cleaned record.
    """
    examples = [strict_json(line) for line in sample.read_text(encoding='utf-8').splitlines()]
    expected_keys = set(examples[0])
    references = {row['imdb_id']: row for row in examples}
    errors, missing = Counter(), Counter()
    diagnostics, reservoir, comparisons = [], [], {}
    rng = random.Random(20260927)
    rows = valid_rows = 0

    def issue(reason, line, imdb_id=None):
        errors[reason] += 1
        if len(diagnostics) < 100:
            diagnostics.append(dict(line=line, imdb_id=imdb_id, reason=reason))

    with sqlite3.connect(f'{database.resolve().as_uri()}?mode=ro', uri=True) as db, TemporaryDirectory() as folder:
        seen = sqlite3.connect(Path(folder) / 'seen.sqlite')
        try:
            seen.executescript('CREATE TABLE imdb (id TEXT PRIMARY KEY); CREATE TABLE tmdb (id INTEGER PRIMARY KEY);')
            with path.open(encoding='utf-8') as source:
                for line_number, line in enumerate(source, 1):
                    rows += 1
                    try:
                        movie = strict_json(line)
                        if not isinstance(movie, dict):
                            raise ValueError('not_object')
                    except (ValueError, TypeError):
                        issue('invalid_json_object', line_number)
                        continue
                    imdb_id, tmdb_id = movie.get('imdb_id'), movie.get('tmdb_id')
                    if set(movie) != expected_keys:
                        issue('schema_keys_mismatch', line_number, imdb_id)
                    if not isinstance(imdb_id, str) or not IMDB_ID_PATTERN.fullmatch(imdb_id):
                        issue('invalid_imdb_id', line_number)
                        continue
                    if type(tmdb_id) is not int or tmdb_id <= 0:
                        issue('invalid_tmdb_id', line_number, imdb_id)
                        continue
                    for table, value in (('imdb', imdb_id), ('tmdb', tmdb_id)):
                        try:
                            seen.execute(f'INSERT INTO {table} VALUES (?)', (value,))
                        except sqlite3.IntegrityError:
                            issue(f'duplicate_{table}_id', line_number, imdb_id)
                    if line_number % 10000 == 0:
                        seen.commit()
                    try:
                        canonical = clean_movie(movie)
                        if canonical != movie:
                            issue('not_canonical_cleaned_record', line_number, imdb_id)
                        if not movie.get('embedding_text') or movie['embedding_text'] != build_embedding_text(movie):
                            issue('embedding_template_mismatch', line_number, imdb_id)
                        # Numeric values occurring naturally in titles/overviews are allowed;
                        # field injection is detected by exact template equality above.
                        if re.search(r'(?m)^.+: (?:None|null)$', movie.get('embedding_text', '')):
                            issue('placeholder_text_requires_review', line_number, imdb_id)
                    except (ValueError, TypeError, KeyError):
                        issue('invalid_cleaned_fields', line_number, imdb_id)
                    if movie.get('text_template_version') != TEXT_TEMPLATE_VERSION:
                        issue('template_version_mismatch', line_number, imdb_id)
                    if movie.get('movie_id') is not None:
                        issue('unexpected_mysql_movie_id', line_number, imdb_id)
                    missing.update(field for field in MISSING_CHECK_FIELDS if not movie.get(field))
                    entry = db.execute('SELECT imdb_json, tmdb_id FROM catalog WHERE imdb_id=?', (imdb_id,)).fetchone()
                    checkpoint = db.execute('SELECT status, cleaned_json FROM results WHERE imdb_id=?', (imdb_id,)).fetchone()
                    if not checkpoint or checkpoint[0] != 'succeeded' or strict_json(checkpoint[1]) != movie:
                        issue('checkpoint_mismatch', line_number, imdb_id)
                    if not entry or entry[1] != tmdb_id:
                        issue('mapping_mismatch', line_number, imdb_id)
                    else:
                        imdb = strict_json(entry[0])
                        if imdb.get('titleType') not in ('movie', 'tvMovie') or float(imdb.get('numVotes', 0)) < 50:
                            issue('ineligible_imdb', line_number, imdb_id)
                        try:
                            raw = strict_json((cache / 'movie' / f'{tmdb_id}.json').read_text(encoding='utf-8'))
                            if not valid_details(raw, imdb_id, tmdb_id):
                                issue('raw_cache_identity_or_structure_mismatch', line_number, imdb_id)
                            elif clean_movie(transform(imdb, raw)) != movie:
                                issue('raw_cache_transform_mismatch', line_number, imdb_id)
                        except (OSError, ValueError, TypeError, KeyError):
                            issue('raw_cache_missing_or_invalid', line_number, imdb_id)
                    valid_rows += 1
                    if len(reservoir) < 20:
                        reservoir.append(movie)
                    else:
                        position = rng.randrange(valid_rows)
                        if position < 20:
                            reservoir[position] = movie
                    if imdb_id in references:
                        reference = references[imdb_id]
                        comparisons[imdb_id] = dict(title=movie.get('title'),
                            tmdb_id_matches=tmdb_id == reference['tmdb_id'],
                            changed_fields=[key for key in sorted(expected_keys) if movie.get(key) != reference.get(key)])
            eligible = db.execute('SELECT count(*) FROM catalog').fetchone()[0]
            statuses = dict(db.execute('SELECT status, count(*) FROM results GROUP BY status'))
            if require_complete:
                if rows != statuses.get('succeeded', 0):
                    issue('output_count_mismatch', None)
                if statuses.get('failed', 0) or eligible != statuses.get('succeeded', 0) + statuses.get('unmatched', 0):
                    issue('catalog_incomplete', None)
                for imdb_id in references:
                    if imdb_id not in comparisons:
                        issue('required_reference_missing', None, imdb_id)
                if len(reservoir) < 20:
                    issue('manual_sample_less_than_20', None)
            if rows == 0:
                issue('empty_output', None)
        finally:
            seen.close()
    return dict(passed=not errors, scope='full' if require_complete else 'subset',
        rows=rows, eligible_imdb_rows=eligible, checkpoint_statuses=statuses,
        errors=dict(errors), diagnostics=diagnostics,
        missing_by_field={field: missing[field] for field in MISSING_CHECK_FIELDS},
        missing_fraction_by_field={field: missing[field] / rows if rows else None for field in MISSING_CHECK_FIELDS},
        text_template_version=TEXT_TEMPLATE_VERSION, artifact=fingerprint(path),
        sample_comparisons=comparisons, manual_review_completed=False,
        manual_review_sample=reservoir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('data/processed/movies_cleaned_full.jsonl'))
    parser.add_argument('--database', type=Path, default=Path('data/processed/catalog.sqlite'))
    parser.add_argument('--cache', type=Path, default=Path('data/processed/tmdb_cache'))
    parser.add_argument('--sample', type=Path, default=Path('data/seeds/movies_cleaned_sample.jsonl'))
    parser.add_argument('--report', type=Path, default=Path('data/processed/full_validation.json'))
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    protected = [args.input, args.database, args.sample]
    if args.report.resolve() in [p.resolve() for p in protected] or args.cache.resolve() in args.report.resolve().parents:
        parser.error('Report không được ghi đè input/database/sample/cache')
    report = validate(args.input, args.database, args.cache, args.sample, args.require_complete)
    atomic_json(args.report, report)
    print(json.dumps({key: report[key] for key in ('passed', 'scope', 'rows', 'errors')}))
    raise SystemExit(0 if report['passed'] else 1)
