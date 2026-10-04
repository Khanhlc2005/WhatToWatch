"""Đóng gói checkpoint và cache để gửi; không lấy .env, API key hoặc log."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import zipfile

from catalog_inventory import fingerprint
from catalog_lock import catalog_lock


def package(root, target):
    processed = root / 'data/processed'
    database = processed / 'catalog.sqlite'
    if target.exists():
        raise FileExistsError('Không ghi đè bộ bàn giao đã tồn tại')
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.zip.tmp')
    modules = ['full_catalog.py', 'catalog_lock.py', 'catalog_inventory.py',
               'clean_movies.py', 'embedding_template.py', 'validate_catalog.py']
    with catalog_lock(database.with_suffix('.lock')), tempfile.TemporaryDirectory() as directory:
        snapshot = Path(directory) / 'catalog.sqlite'
        with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as source:
            with sqlite3.connect(snapshot) as dest:
                source.backup(dest)
            statuses = dict(source.execute('SELECT status,count(*) FROM results GROUP BY status'))
            eligible = source.execute('SELECT count(*) FROM catalog').fetchone()[0]
        files = [(root / 'data/scripts/run_shared_catalog.py', 'script.py'),
                 (root / 'data/scripts/start_catalog.sh', 'script.sh'),
                 (root / 'data/scripts/requirements-catalog.txt', 'requirements-catalog.txt'),
                 (root / 'docs/catalog_handoff_vi.md', 'hướng dẫn.md'),
                 (snapshot, 'data/processed/catalog.sqlite'),
                 (root / 'data/seeds/movies_cleaned_sample.jsonl', 'data/seeds/movies_cleaned_sample.jsonl')]
        files.extend((root / 'data/scripts' / name, 'scripts/' + name) for name in modules)
        files.extend((p, p.relative_to(root).as_posix())
                     for p in sorted((processed / 'tmdb_cache').rglob('*.json')) if p.is_file())
        manifest = dict(created_at=datetime.now(timezone.utc).isoformat(), eligible_rows=eligible,
                        checkpoint_statuses=statuses, files=[])
        try:
            with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
                for source, relative in files:
                    if source.is_symlink():
                        raise ValueError('Không đóng gói symlink')
                    info = fingerprint(source)
                    manifest['files'].append(dict(path=relative, bytes=info['bytes'], sha256=info['sha256']))
                    archive.write(source, 'catalog_handoff/' + relative)
                archive.writestr('catalog_handoff/MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2))
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    result = fingerprint(target)
    target.with_suffix('.sha256').write_text(result['sha256'] + '  ' + target.name + '\n')
    return dict(archive=result, checkpoint_statuses=statuses, eligible_rows=eligible)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(Path(__file__).resolve().parents[2], args.output.resolve())))
