"""Chạy catalog trên hotspot với ngân sách MB và tự khôi phục DNS khi dừng.

Theo dõi RX+TX của cả interface (bao gồm ứng dụng khác), cùng response đã giải nén.
Dừng sớm với vùng đệm 5 MB; không phải bộ giới hạn cước của nhà mạng.
"""
import argparse
import fcntl
import json
from pathlib import Path
import signal
import sqlite3
import subprocess
import time

from full_catalog import BudgetStopped, Client, FetchError, atomic_json, export, run


class Budget:
    def __init__(self, device, maximum, state_path):
        if maximum <= 5_000_000:
            raise ValueError('budget_must_exceed_5_MB')
        self.device, self.maximum, self.path = device, maximum, state_path
        current = self.counter()
        if state_path.exists():
            self.state = json.loads(state_path.read_text())
            if self.state['maximum_bytes'] != maximum or self.state['device'] != device:
                raise ValueError('budget_state_configuration_mismatch')
        else:
            self.state = dict(device=device, maximum_bytes=maximum, last_counter=current,
                              interface_bytes=0, decoded_bytes=0, responses=0)
        self.check()

    def counter(self):
        base = Path('/sys/class/net') / self.device / 'statistics'
        return sum(int((base / name).read_text()) for name in ('rx_bytes', 'tx_bytes'))

    def check(self, decoded=0):
        current = self.counter()
        previous = self.state['last_counter']
        if current < previous:
            raise BudgetStopped('interface_counter_reset_requires_review')
        self.state['interface_bytes'] += current - previous
        self.state['last_counter'] = current
        self.state['decoded_bytes'] += decoded
        atomic_json(self.path, self.state)
        if self.state['interface_bytes'] >= self.maximum - 5_000_000:
            raise BudgetStopped('data_budget_reached')


class MeteredSession:
    def __init__(self, session, budget, connection):
        self.session, self.budget, self.connection = session, budget, connection

    def get(self, *args, **kwargs):
        self.budget.check()
        active = subprocess.check_output(
            ['nmcli', '-g', 'GENERAL.CON-UUID', 'device', 'show', self.budget.device], text=True).strip()
        if active != self.connection:
            raise BudgetStopped('active_connection_changed')
        response = self.session.get(*args, **kwargs, stream=True)
        try:
            content = bytearray()
            for chunk in response.iter_content(chunk_size=16384):
                content.extend(chunk)
                self.budget.check(len(chunk))
                if len(content) > 8_000_000:
                    raise FetchError('response_exceeds_8_MB')
            response._content = bytes(content)
            response._content_consumed = True
            self.budget.state['responses'] += 1
            self.budget.check()
            return response
        finally:
            response.close()


def nm(*args):
    return subprocess.check_output(['nmcli', *args], text=True).strip()


def main():
    def stop_on_signal(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop_on_signal)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-mb', type=int, required=True, help='MB thập phân, 1 MB = 1.000.000 bytes')
    parser.add_argument('--connection', required=True)
    parser.add_argument('--device', default='wlo1')
    parser.add_argument('--usage', type=Path, required=True)
    parser.add_argument('--database', type=Path, default=Path('data/processed/catalog.sqlite'))
    parser.add_argument('--cache', type=Path, default=Path('data/processed/tmdb_cache'))
    parser.add_argument('--output', type=Path, default=Path('data/processed'))
    parser.add_argument('--rate', type=float, default=2)
    parser.add_argument('--target-successes', type=int, help='Dừng khi tổng succeeded, gồm checkpoint cũ, đạt mức này')
    args = parser.parse_args()
    if args.target_successes is not None and args.target_successes <= 0:
        parser.error('--target-successes phải dương')
    if nm('-g', 'GENERAL.CON-UUID', 'device', 'show', args.device) != args.connection:
        parser.error('Kết nối active khác --connection')
    if not args.database.is_file():
        parser.error('Database không tồn tại')
    with args.database.with_suffix('.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        budget = Budget(args.device, args.max_mb * 1_000_000, args.usage)
        original = {p: nm('-g', p, 'connection', 'show', args.connection) for p in
                    ('ipv4.dns', 'ipv4.ignore-auto-dns', 'ipv6.dns', 'ipv6.ignore-auto-dns')}
        restore_path = args.usage.with_suffix('.dns.json')
        atomic_json(restore_path, dict(uuid=args.connection, device=args.device, original=original))
        db = sqlite3.connect(args.database)
        try:
            nm('connection', 'modify', args.connection, 'ipv4.dns', '1.1.1.1 1.0.0.1',
               'ipv4.ignore-auto-dns', 'yes', 'ipv6.ignore-auto-dns', 'yes')
            nm('device', 'reapply', args.device)
            time.sleep(1)
            client = Client(args.rate, attempts=1)
            client.session = MeteredSession(client.session, budget, args.connection)
            client.get('configuration')
            print('probe_success', flush=True)
            client.attempts = 4
            print(json.dumps(run(db, args.cache, client, progress_every=25, prioritize_votes=True,
                                 target_successes=args.target_successes)), flush=True)
        except FetchError as error:
            print('stopped:' + str(error), flush=True)
        except KeyboardInterrupt:
            print('stopped:interrupted_checkpoint_preserved', flush=True)
        finally:
            print('Giai đoạn gọi TMDB đã dừng/hoàn thành. Đang khôi phục DNS ban đầu.', flush=True)
            settings = [item for pair in original.items() for item in pair]
            nm('connection', 'modify', args.connection, *settings)
            if nm('-g', 'GENERAL.CON-UUID', 'device', 'show', args.device) == args.connection:
                nm('device', 'reapply', args.device)
                time.sleep(1)
                subprocess.run(['resolvectl', 'status', args.device], check=True)
            atomic_json(restore_path, dict(uuid=args.connection, device=args.device,
                                          original=original, restored=True))
            report = export(db, args.output)
            if args.target_successes is not None:
                atomic_json(args.output / 'catalog_scope.json', dict(
                    scope='partial', target_successes=args.target_successes,
                    target_reached=report['output_rows'] >= args.target_successes,
                    accepted_rows=report['output_rows'], eligible_rows=report['eligible_imdb_rows'],
                    remaining_not_accepted=report['eligible_imdb_rows'] - report['output_rows'],
                    pending_rows=report['pending_rows'], rejected_rows=report['rejected_rows'],
                    note=f'Chỉ thu thập {args.target_successes:,} phim thành công theo yêu cầu; phần còn lại để đợt sau.'))
            db.close()
            print(json.dumps(dict(output_rows=report['output_rows'], pending_rows=report['pending_rows'],
                                  usage=budget.state)), flush=True)


if __name__ == '__main__':
    main()
