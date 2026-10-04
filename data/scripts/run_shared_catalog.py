"""Một lệnh: thiết lập môi trường, tiếp tục tải, làm sạch, xuất và kiểm tra."""
import argparse
import getpass
import math
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import venv


TARGET_SUCCESSES = 100_000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rate', type=float, default=2, help='Số request/giây; mặc định 2')
    parser.add_argument('--offline', action='store_true', help='Chỉ xuất và kiểm tra checkpoint, không gọi TMDB')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not math.isfinite(args.rate) or args.rate <= 0:
        parser.error('--rate phải là số dương hữu hạn')
    if sys.version_info < (3, 10):
        parser.error('Cần Python 3.10 trở lên')
    script = Path(__file__).resolve()
    bundled = (script.parent / 'scripts').is_dir()
    root = script.parent if bundled else script.parents[2]
    scripts = root / 'scripts' if bundled else script.parent
    sys.path.insert(0, str(scripts))
    os.chdir(root)
    database = root / 'data/processed/catalog.sqlite'
    if not database.is_file():
        parser.error('Thiếu data/processed/catalog.sqlite: hãy giải nén đầy đủ bộ bàn giao.')
    if not args.worker and not args.offline:
        environment = root / '.catalog-venv'
        python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        if not python.exists():
            print('Đang tạo môi trường Python riêng...', flush=True)
            venv.EnvBuilder(with_pip=True).create(environment)
        check = subprocess.run([str(python), '-c', 'import requests, dotenv'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if check.returncode:
            subprocess.run([str(python), '-m', 'pip', 'install',
                            'requests==2.31.0', 'python-dotenv==1.0.1'], check=True)
        # Replace the launcher: Ctrl+C reaches the worker without a second process.
        os.execv(str(python), [str(python), str(script), '--worker', '--rate', str(args.rate)])

    from catalog_lock import catalog_lock
    from full_catalog import Client, FetchError, atomic_json, export, run
    from validate_catalog import validate

    if not args.offline and not os.environ.get('TMDB_API'):
        os.environ['TMDB_API'] = getpass.getpass('Nhập TMDB API key (v3, không hiển thị): ').strip()
    def stop(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    output = database.parent
    cache = output / 'tmdb_cache'
    with catalog_lock(database.with_suffix('.lock')):
        db = sqlite3.connect(database)
        stopped = None
        try:
            if not args.offline:
                client = Client(args.rate)
                client.get('configuration')
                print('Kết nối thành công. Tiếp tục đến 100.000 phim sạch tổng cộng; Ctrl+C để lưu và dừng.', flush=True)
                run(db, cache, client, prioritize_votes=True, progress_every=100, target_successes=TARGET_SUCCESSES)
                print('Thử lại các bản ghi lỗi một lượt...', flush=True)
                run(db, cache, client, retry_failed=True, prioritize_votes=True, progress_every=100, target_successes=TARGET_SUCCESSES)
        except FetchError as error:
            stopped = str(error)
            print('Đã dừng:', stopped, '— chạy lại cùng lệnh để tiếp tục.', flush=True)
        except KeyboardInterrupt:
            stopped = 'interrupted'
            print('Đang lưu dữ liệu. Vui lòng chờ, không đóng cửa sổ.', flush=True)
        finally:
            report = export(db, output)
            db.close()

        print('Đã xuất JSONL. Đang đối chiếu dữ liệu với checkpoint và raw cache...', flush=True)
        validation = validate(output / 'movies_cleaned_full.jsonl', database, cache,
                              root / 'data/seeds/movies_cleaned_sample.jsonl', report['complete'])
        atomic_json(output / 'validation.json', validation)
        target_reached = report['output_rows'] >= TARGET_SUCCESSES
        summary = dict(target_successes=TARGET_SUCCESSES, target_reached=target_reached,
                       remaining_to_target=max(0, TARGET_SUCCESSES - report['output_rows']),
                       eligible_rows=report['eligible_imdb_rows'], accepted_rows=report['output_rows'],
                       unmatched_rows=report['unmatched_tmdb_rows'], rejected_rows=report['rejected_rows'],
                       pending_rows=report['pending_rows'], complete=report['complete'],
                       validation_passed=validation['passed'], validation_scope=validation['scope'],
                       stop_reason=stopped, artifact=validation['artifact'])
        atomic_json(output / 'run_summary.json', summary)
        atomic_json(output / 'catalog_scope.json', dict(
            scope='checkpoint_only' if args.offline else 'target_100000_requested', **summary))
        print(f"Kết quả: {report['output_rows']:,} phim sạch; {report['pending_rows']:,} chưa xử lý; "
              f"{report['rejected_rows']:,} lỗi; {report['unmatched_tmdb_rows']:,} không mapping.", flush=True)
        print('File dữ liệu:', output / 'movies_cleaned_full.jsonl', flush=True)
        print('Báo cáo:', output / 'run_summary.json', flush=True)
        return 0 if target_reached and validation['passed'] else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, sqlite3.Error, subprocess.CalledProcessError) as error:
        print('Không thể tiếp tục:', type(error).__name__,
              '— kiểm tra dung lượng ổ đĩa, Python/pip, hoặc cửa sổ chạy trùng.', file=sys.stderr)
        raise SystemExit(2)
