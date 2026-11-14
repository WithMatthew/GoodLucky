"""W07D04: acquire separate research snapshots, then verify their procedural seal.

python -m src.prepare_etf_research --download  # explicit one-time network action
python -m src.prepare_etf_research             # offline hashes only

No import-time network or writes. No orders, return calculations or price output.
Windows zoneinfo uses the tzdata dependency recorded in requirements-data.txt.
"""

import argparse
import csv
from datetime import date, datetime, timedelta, timezone
from importlib.metadata import version
import json
from pathlib import Path
import platform
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from src.check_data_quality import expected_dates, inspect_dates, sha256


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'configs/etf-research-v1.json'
MANIFEST = ROOT / 'reports/etf-research-v1/manifest.json'
FIELDS = ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']


def timestamp_now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(content, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def validate_partitions(plan):
    dev, test = plan['development'], plan['final_test']
    if not (date.fromisoformat(dev['start']) <= date.fromisoformat(dev['end'])
            < date.fromisoformat(test['start']) <= date.fromisoformat(test['end'])):
        raise ValueError('Development must precede final test, with no overlap')
    if not plan['symbols'] or len(plan['symbols']) != len(set(plan['symbols'])):
        raise ValueError('Symbols must be nonempty and unique')


def chart_url(symbol, bounds, zone):
    start = datetime.combine(date.fromisoformat(bounds['start']), datetime.min.time(), zone)
    end = datetime.combine(date.fromisoformat(bounds['end']) + timedelta(days=1), datetime.min.time(), zone)
    params = {'period1': int(start.timestamp()), 'period2': int(end.timestamp()),
              'interval': '1d', 'events': 'div,splits,capitalGains',
              'includePrePost': 'false', 'includeAdjustedClose': 'true'}
    return 'https://query1.finance.yahoo.com/v8/finance/chart/' + symbol + '?' + urlencode(params)


def parse_chart(payload, symbol, bounds, zone):
    chart = payload['chart']
    if chart.get('error') or not chart.get('result') or len(chart['result']) != 1:
        raise ValueError('Chart response failed; raw snapshot retained without printing it')
    result = chart['result'][0]
    meta = result['meta']
    if (meta.get('symbol') != symbol or meta.get('currency') != 'USD'
            or meta.get('exchangeTimezoneName') != zone.key or meta.get('instrumentType') != 'ETF'):
        raise ValueError('Unexpected symbol, currency, timezone or instrument type')
    timestamps = result['timestamp']
    quotes = result['indicators']['quote'][0]
    values = {field: quotes[field] for field in ['open', 'high', 'low', 'close', 'volume']}
    values['adj_close'] = result['indicators']['adjclose'][0]['adjclose']
    if not timestamps or any(len(column) != len(timestamps) for column in values.values()):
        raise ValueError('Empty response or unequal column lengths')
    start, end = date.fromisoformat(bounds['start']), date.fromisoformat(bounds['end'])
    rows = []
    for i, stamp in enumerate(timestamps):
        day = datetime.fromtimestamp(stamp, zone).date()
        if not start <= day <= end:
            raise ValueError('Response includes a date outside requested partition')
        rows.append({'date': day, **{field: column[i] for field, column in values.items()}})
    return rows


def inspect_prices(rows, expected):
    result = inspect_dates(rows, expected, FIELDS[1:])
    bad_order = 0
    for row in rows:
        prices = [row[field] for field in ['open', 'high', 'low', 'close']]
        if all(isinstance(value, (int, float)) for value in prices):
            bad_order += not (row['low'] <= min(row['open'], row['close'])
                              <= max(row['open'], row['close']) <= row['high'])
    result['ohlc_order_failures'] = bad_order
    result['passed'] &= bad_order == 0
    return result


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def file_record(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha256(path),
            'bytes': path.stat().st_size}


def acquire():
    if MANIFEST.exists():
        raise FileExistsError('Manifest exists; use offline verification, never overwrite a snapshot')
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    validate_partitions(plan)
    calendar_path = ROOT / plan['calendar_file']
    calendar = json.loads(calendar_path.read_text(encoding='utf-8'))
    zone = ZoneInfo(plan['timezone'])
    # These input hashes and the decision timestamp are saved BEFORE any research download.
    decision = {'recorded_at_utc': timestamp_now(), 'plan': file_record(PLAN),
                'calendar': file_record(calendar_path), 'plan_content': plan}
    decision_path = MANIFEST.parent / 'pre-download-decision.json'
    save_json(decision_path, decision)
    manifest = {'study_id': plan['study_id'], 'started_at_utc': timestamp_now(),
                'python_version': platform.python_version(), 'tzdata_version': version('tzdata'),
                'status': 'acquisition_incomplete', 'snapshots': [],
                'supporting_files': [file_record(PLAN), file_record(calendar_path),
                                    file_record(decision_path), file_record(Path(__file__)),
                                    file_record(ROOT / 'src/check_data_quality.py')]}
    try:
        for partition in ['development', 'final_test']:
            bounds = plan[partition]
            expected = expected_dates(calendar, bounds['start'], bounds['end'])
            for symbol in plan['symbols']:
                if partition == 'final_test':
                    raw = ROOT / plan['test_directory'] / 'raw' / (symbol + '.json')
                    derived = ROOT / plan['test_directory'] / (symbol + '.csv')
                else:
                    raw = ROOT / 'data/raw/yahoo/etf-research-v1/development' / (symbol + '.json')
                    derived = ROOT / plan['default_research_input'] / (symbol + '.csv')
                if raw.exists() or derived.exists():
                    raise FileExistsError('Refusing to overwrite research data')
                url = chart_url(symbol, bounds, zone)
                with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30) as response:
                    payload = response.read()
                raw.parent.mkdir(parents=True, exist_ok=True)
                with raw.open('xb') as handle:
                    handle.write(payload)
                entry = {'symbol': symbol, 'partition': partition, 'requested_bounds': bounds,
                         'source_url': url, 'downloaded_at_utc': timestamp_now(), 'raw': file_record(raw)}
                manifest['snapshots'].append(entry)
                rows = parse_chart(json.loads(payload), symbol, bounds, zone)
                quality = inspect_prices(rows, expected)
                write_csv(derived, rows)
                entry.update({'derived': file_record(derived), 'quality': quality})
                print(json.dumps({'symbol': symbol, 'partition': partition, 'quality': quality}))
        manifest['status'] = ('sealed_for_teaching' if all(entry['quality']['passed'] for entry in manifest['snapshots'])
                              else 'snapshots_saved_quality_issues_require_review')
    finally:
        manifest['recorded_at_utc'] = timestamp_now()
        save_json(MANIFEST, manifest)
    return manifest['status']


def verify():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if manifest['status'] != 'sealed_for_teaching':
        raise ValueError('Acquisition/seal is incomplete; inspect metadata before proceeding')
    files = manifest['supporting_files'] + [entry[key] for entry in manifest['snapshots'] for key in ['raw', 'derived']]
    changed = [entry['path'] for entry in files if not (ROOT / entry['path']).is_file()
               or sha256(ROOT / entry['path']) != entry['sha256']]
    if changed:
        raise ValueError('Missing or changed sealed inputs: ' + ', '.join(changed))
    print(json.dumps({'status': 'hashes_verified', 'files': len(files),
                      'price_or_return_output': False, 'test_release': 'W21 after W16 freeze'}))


def load_development(symbol):
    """The ordinary research entry point has no final-test selector."""
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    if symbol not in plan['symbols']:
        raise ValueError('Symbol is outside the fixed study universe')
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if manifest.get('status') != 'sealed_for_teaching' or sha256(PLAN) != manifest['supporting_files'][0]['sha256']:
        raise ValueError('Seal is incomplete or plan has changed')
    entry = next(item for item in manifest['snapshots'] if item['partition'] == 'development' and item['symbol'] == symbol)
    path = ROOT / entry['derived']['path']
    if sha256(path) != entry['derived']['sha256']:
        raise ValueError('Development file changed')
    with path.open(encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError('Unexpected research columns')
        return [{'date': date.fromisoformat(row['date']),
                 **{field: (None if row[field] == '' else int(row[field]) if field == 'volume' else float(row[field]))
                    for field in FIELDS[1:]}} for row in reader]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    if args.download:
        print(acquire())
    else:
        verify()
