"""Validate and resumably index a mapped catalog; never delete existing points."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
from qdrant_client import QdrantClient, models

import index_sample_movies as common

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'data/scripts'))
from validate_movie_links import audit_links


INDEX_FIELDS = {
    'movie_id', 'imdb_id', 'tmdb_id', 'title', 'genres', 'keywords', 'release_date',
    'imdb_year', 'imdb_rating', 'original_language', 'production_countries',
    'runtime_minutes', 'adult', 'status', 'text_template_version', 'embedding_text',
}


def load_index_movies(path):
    # Full cast/crew/overview data is unnecessary once canonical text exists.
    # Project each row while reading to keep laptop RAM available for the model.
    movies = []
    with path.open(encoding='utf-8') as source:
        for line in source:
            if line.strip():
                movie = json.loads(line)
                movies.append({key: value for key, value in movie.items() if key in INDEX_FIELDS})
    return movies


def pending_movies(client, collection, movies):
    expected = {common.point_id(m['imdb_id']): m for m in movies}
    present = set()
    offset = None
    while True:
        points, offset = client.scroll(collection, limit=128, offset=offset, with_payload=True, with_vectors=True)
        for point in points:
            key = str(point.id)
            if key not in expected:
                raise ValueError(f'Unexpected existing point: {key}; use a separate collection')
            if point.payload != common.make_payload(expected[key]):
                raise ValueError(f'Existing payload conflicts: {key}; refusing overwrite')
            vectors = point.vector or {}
            dense = np.asarray(vectors.get('dense', []))
            sparse = vectors.get('sparse')
            sparse_valid = (sparse is not None and bool(sparse.indices)
                            and len(sparse.indices) == len(sparse.values)
                            and len(set(sparse.indices)) == len(sparse.indices)
                            and all(type(i) is int and i >= 0 for i in sparse.indices)
                            and np.isfinite(sparse.values).all())
            if dense.shape != (1024,) or not np.isfinite(dense).all() or np.linalg.norm(dense) == 0 or not sparse_valid:
                raise ValueError(f'Invalid existing vectors: {key}')
            present.add(key)
        if offset is None:
            break
    return [m for m in movies if common.point_id(m['imdb_id']) not in present]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--url', default=os.getenv('QDRANT_URL', 'http://localhost:6335'))
    parser.add_argument('--collection', default=os.getenv('QDRANT_COLLECTION', 'movies'))
    parser.add_argument('--device', default=os.getenv('EMBEDDING_DEVICE', 'cpu'))
    parser.add_argument('--model-path', default=os.getenv('EMBEDDING_MODEL_PATH'),
                        help='Local BGE-M3 snapshot, avoiding optional ONNX downloads')
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--chunk-size', type=int, default=16)
    parser.add_argument('--max-length', type=int, default=512)
    parser.add_argument('--preflight-only', action='store_true')
    parser.add_argument('--limit', type=int, help='Explicit smoke-test limit; not a complete catalog run')
    args = parser.parse_args()
    if min(args.batch_size, args.chunk_size, args.max_length) < 1 or (args.limit is not None and args.limit < 1):
        parser.error('Sizes and limit must be positive')
    common.COLLECTION = args.collection
    common.EMBEDDING_VERSION = f'bge-m3_movie_text_v1_len{args.max_length}_v1'
    movies = load_index_movies(args.input)
    errors = audit_links(movies)['issues']
    if errors:
        raise ValueError(f'Invalid mapped input: {errors[:5]}')
    # Validate all token lengths before any vector writes; do not silently truncate.
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_path or common.MODEL_NAME)
    oversized = []
    maximum = 0
    for start in range(0, len(movies), 256):
        chunk = movies[start:start + 256]
        texts = [m['embedding_text'] for m in chunk]
        if not all(isinstance(t, str) and t.strip() for t in texts):
            raise ValueError('Empty embedding text')
        lengths = [len(ids) for ids in tokenizer(texts, truncation=False)['input_ids']]
        maximum = max(maximum, max(lengths))
        oversized.extend((m['imdb_id'], n) for m, n in zip(chunk, lengths) if n > args.max_length)
    print(json.dumps({'stage': 'preflight', 'input_count': len(movies), 'max_tokens': maximum,
                      'max_length': args.max_length, 'oversized': len(oversized), 'examples': oversized[:5]}), flush=True)
    if oversized:
        raise ValueError('Texts exceed max length; explicitly choose a larger max-length/version')
    if args.preflight_only:
        return
    with closing(QdrantClient(url=args.url, timeout=120)) as client:
        common.ensure_collection(client, 1024)
        pending = pending_movies(client, args.collection, movies)
        remaining = len(pending)
        if args.limit:
            pending = pending[:args.limit]
        print(json.dumps({'stage': 'resume', 'total': len(movies), 'already_indexed': len(movies)-remaining,
                          'to_index': len(pending)}), flush=True)
        if pending:
            from FlagEmbedding import BGEM3FlagModel
            import torch
            torch.set_num_threads(min(4, os.cpu_count() or 1))
            model = BGEM3FlagModel(args.model_path or common.MODEL_NAME, devices=args.device, use_fp16=args.device.startswith('cuda'))
            started = time.monotonic()
            for start in range(0, len(pending), args.chunk_size):
                chunk = pending[start:start + args.chunk_size]
                encoded = model.encode([m['embedding_text'] for m in chunk], batch_size=args.batch_size,
                                       max_length=args.max_length, return_dense=True, return_sparse=True,
                                       return_colbert_vecs=False)
                dense = np.asarray(encoded['dense_vecs'], dtype=np.float32)
                if dense.shape != (len(chunk), 1024) or not np.isfinite(dense).all() or np.any(np.linalg.norm(dense, axis=1) == 0):
                    raise ValueError('Invalid dense vectors')
                if len(encoded['lexical_weights']) != len(chunk):
                    raise ValueError('Sparse vector count mismatch')
                points = [models.PointStruct(id=common.point_id(m['imdb_id']), payload=common.make_payload(m),
                          vector={'dense': dense[i].tolist(), 'sparse': common.sparse_vector(encoded['lexical_weights'][i])})
                          for i, m in enumerate(chunk)]
                client.upsert(args.collection, points=points, wait=True)
                print(json.dumps({'stage': 'indexed', 'completed_this_run': start+len(chunk),
                                  'planned_this_run': len(pending), 'elapsed_seconds': round(time.monotonic()-started, 2)}), flush=True)
        missing = pending_movies(client, args.collection, movies)
        print(json.dumps({'stage': 'verified', 'total': len(movies), 'remaining': len(missing),
                          'status': 'PASS' if not missing else 'PARTIAL'}), flush=True)
        if missing and not args.limit:
            raise ValueError('Incomplete catalog')


if __name__ == '__main__':
    main()
