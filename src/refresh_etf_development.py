"""独立重建2020—2024开发快照；不读取或下载最终测试，无交易。

python -m src.refresh_etf_development --download
python -m src.refresh_etf_development --baseline <snapshot_id>
导入不联网；下载前落盘配置和哈希，失败尝试保留，绝不覆写旧快照。
"""

import argparse
import csv
from datetime import date, datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import platform
import re
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from src.buy_hold_baseline import normalize_adjusted_path, summarize_path, validate_scope
from src.check_data_quality import expected_dates, sha256
from src.prepare_etf_research import (
    FIELDS, chart_url, inspect_prices, parse_chart, save_json, timestamp_now, write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
STUDY = 'etf-development-v2'
SYMBOLS = ['SPY', 'DIA', 'QQQ']
BOUNDS = {'start': '2020-01-01', 'end': '2024-12-31'}
CONFIG = 'configs/etf-development-v2.json'
BASELINE_CONFIG = 'configs/buy-hold-baseline-v2.json'
SUPPORT = [CONFIG, BASELINE_CONFIG, 'configs/etf-research-v1.json',
           'configs/nyse-dates-2020-2025.json', 'reports/etf-research-v1/manifest.json',
           'src/refresh_etf_development.py', 'src/prepare_etf_research.py',
           'src/check_data_quality.py', 'src/buy_hold_baseline.py',
           'tests/test_refresh_etf_development.py', 'tests/test_buy_hold_baseline.py',
           'requirements-data.txt']


def validate_plan(plan):
    expected = {'study_id': STUDY, 'parent_study': 'etf-research-v1',
                'symbols': SYMBOLS, 'development': BOUNDS, 'interval': '1d',
                'timezone': 'America/New_York', 'currency': 'USD',
                'calendar_file': 'configs/nyse-dates-2020-2025.json',
                'original_manifest': 'reports/etf-research-v1/manifest.json',
                'final_test_download': False, 'final_test_read': False}
    if any(key not in plan or plan[key] != value for key, value in expected.items()):
        raise ValueError('Refresh must keep the authorized development-only scope')
    if 'final_test' in plan:
        raise ValueError('No final-test partition is accepted by this entry point')


def check_snapshot_id(snapshot_id):
    if not isinstance(snapshot_id, str) or not re.fullmatch(r'\d{8}T\d{12}Z', snapshot_id):
        raise ValueError('Invalid snapshot identifier')
    return snapshot_id


def safe_path(root, relative):
    root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or path.relative_to(root).as_posix() != relative:
        raise ValueError('Path redirects outside its declared location')
    return path


def data_path(root, snapshot_id, symbol, raw=False):
    check_snapshot_id(snapshot_id)
    if symbol not in SYMBOLS:
        raise ValueError('Symbol is outside the authorized universe')
    category = 'raw/yahoo' if raw else 'derived'
    extension = 'json' if raw else 'csv'
    return safe_path(root, f'data/{category}/{STUDY}/{snapshot_id}/development/{symbol}.{extension}')


def record(path, root=ROOT):
    return {'path': path.relative_to(root).as_posix(), 'sha256': sha256(path),
            'bytes': path.stat().st_size}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def new_id():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')


def download_bytes(url):
    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30) as response:
        return response.read()


def acquire(root=ROOT):
    plan = read_json(root / CONFIG)
    validate_plan(plan)
    original_plan = read_json(root / 'configs/etf-research-v1.json')
    settings = read_json(root / BASELINE_CONFIG)
    validate_scope(settings, original_plan)
    zone = ZoneInfo(plan['timezone'])
    calendar = read_json(root / plan['calendar_file'])
    expected = expected_dates(calendar, **BOUNDS)
    old = read_json(root / plan['original_manifest'])
    support = [record(safe_path(root, relative), root) for relative in SUPPORT]
    snapshot_id = new_id()
    report = safe_path(root, f'reports/{STUDY}/{snapshot_id}')
    report.mkdir(parents=True, exist_ok=False)
    decision = {'recorded_at_utc': timestamp_now(), 'snapshot_id': snapshot_id,
                'plan': plan, 'calculation_settings': settings, 'supporting_files': support,
                'recorded_before_download': True, 'final_test_requested': False}
    decision_path = report / 'pre-download-decision.json'
    save_json(decision_path, decision)
    manifest = {'study_id': STUDY, 'snapshot_id': snapshot_id, 'status': 'incomplete',
                'started_at_utc': timestamp_now(), 'plan': plan,
                'python_version': platform.python_version(), 'tzdata_version': version('tzdata'),
                'supporting_files': support, 'pre_download': record(decision_path, root),
                'snapshots': [], 'final_test_requested': False, 'final_test_read': False}
    try:
        for symbol in SYMBOLS:
            url = chart_url(symbol, BOUNDS, zone)
            raw, derived = data_path(root, snapshot_id, symbol, True), data_path(root, snapshot_id, symbol)
            if raw.exists() or derived.exists():
                raise FileExistsError('Refusing to overwrite data')
            payload = download_bytes(url)
            raw.parent.mkdir(parents=True, exist_ok=True)
            with raw.open('xb') as handle:
                handle.write(payload)
            entry = {'symbol': symbol, 'partition': 'development', 'requested_bounds': BOUNDS,
                     'source_url': url, 'downloaded_at_utc': timestamp_now(), 'raw': record(raw, root)}
            manifest['snapshots'].append(entry)
            # parse_chart only inspects required identity fields and requested bars,
            # never prints or uses unrelated current quotes in the raw metadata.
            rows = parse_chart(json.loads(payload), symbol, BOUNDS, zone)
            quality = inspect_prices(rows, expected)
            write_csv(derived, rows)
            old_entry = next(item for item in old['snapshots']
                             if item['partition'] == 'development' and item['symbol'] == symbol)
            entry.update({'derived': record(derived, root), 'quality': quality,
                          'matches_original_derived_hash': sha256(derived) == old_entry['derived']['sha256']})
            print(json.dumps({'snapshot_id': snapshot_id, 'symbol': symbol, 'quality': quality}, ensure_ascii=False), flush=True)
            if not quality['passed']:
                raise ValueError('Quality checks failed; raw and derived evidence retained')
        manifest['status'] = 'ready'
    except Exception as error:
        manifest['failure_type'] = type(error).__name__
        raise
    finally:
        manifest['recorded_at_utc'] = timestamp_now()
        save_json(report / 'manifest.json', manifest)
    print(json.dumps({'snapshot_id': snapshot_id, 'status': manifest['status'],
                      'manifest': f'reports/{STUDY}/{snapshot_id}/manifest.json',
                      'final_test_requested': False}, ensure_ascii=False))
    return manifest


def read_manifest(snapshot_id, root=ROOT):
    check_snapshot_id(snapshot_id)
    manifest = read_json(safe_path(root, f'reports/{STUDY}/{snapshot_id}/manifest.json'))
    if (manifest['study_id'] != STUDY or manifest['snapshot_id'] != snapshot_id
            or manifest['status'] != 'ready' or manifest['final_test_read'] is not False
            or manifest['final_test_requested'] is not False):
        raise ValueError('Snapshot is not a ready development-only version')
    validate_plan(manifest['plan'])
    support = manifest['supporting_files']
    if [entry['path'] for entry in support] != SUPPORT:
        raise ValueError('Unexpected supporting files')
    for entry in support:
        if sha256(safe_path(root, entry['path'])) != entry['sha256']:
            raise ValueError('Snapshot supporting version changed: ' + entry['path'])
    decision_path = safe_path(root, f'reports/{STUDY}/{snapshot_id}/pre-download-decision.json')
    if (manifest['pre_download']['path'] != decision_path.relative_to(root).as_posix()
            or sha256(decision_path) != manifest['pre_download']['sha256']):
        raise ValueError('Pre-download record changed')
    if [entry['symbol'] for entry in manifest['snapshots']] != SYMBOLS:
        raise ValueError('Snapshot universe/order is not the declared one')
    return manifest


def load_development(snapshot_id, symbol, root=ROOT):
    path = data_path(root, snapshot_id, symbol)
    manifest = read_manifest(snapshot_id, root)
    entry = next(item for item in manifest['snapshots'] if item['symbol'] == symbol)
    if (entry['partition'] != 'development' or entry['requested_bounds'] != BOUNDS
            or entry['derived']['path'] != path.relative_to(root).as_posix()
            or not entry['quality']['passed']):
        raise ValueError('Data record is outside the declared scope or failed quality')
    if sha256(path) != entry['derived']['sha256']:
        raise ValueError('Development CSV hash mismatch')
    with path.open(encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError('Unexpected CSV fields')
        rows = [{'date': date.fromisoformat(row['date']),
                 **{field: (None if row[field] == '' else int(row[field]) if field == 'volume'
                            else float(row[field])) for field in FIELDS[1:]}} for row in reader]
    calendar = read_json(root / manifest['plan']['calendar_file'])
    quality = inspect_prices(rows, expected_dates(calendar, **BOUNDS))
    if not quality['passed']:
        raise ValueError('Development data quality failed')
    return rows


def run_baseline(snapshot_id, root=ROOT):
    manifest = read_manifest(snapshot_id, root)
    settings = read_json(root / BASELINE_CONFIG)
    validate_scope(settings, read_json(root / 'configs/etf-research-v1.json'))
    run_dir = safe_path(root, 'reports/buy-hold-baseline-v2/runs/' + new_id())
    run_dir.mkdir(parents=True, exist_ok=False)
    save_json(run_dir / 'pre-run.json', {
        'recorded_at_utc': timestamp_now(), 'recorded_before_reading_prices': True,
        'snapshot_id': snapshot_id, 'settings': settings,
        'source_manifest': record(root / f'reports/{STUDY}/{snapshot_id}/manifest.json', root),
        'supporting_files': manifest['supporting_files'], 'python_version': platform.python_version(),
        'tzdata_version': version('tzdata'), 'data_partition': 'development', 'final_test_read': False})
    summaries, previews, outputs = {}, {}, []
    for symbol in SYMBOLS:
        rows = load_development(snapshot_id, symbol, root)
        path = normalize_adjusted_path(rows, settings['initial_model_value'])
        summaries[symbol] = summarize_path(path, settings['annualization_sessions'], settings['daily_risk_free_rate'])
        previews[symbol] = path[:3]
        output = run_dir / f'{symbol}.csv'
        with output.open('x', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(path[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(path)
        outputs.append(record(output, root))
    result = {'status': 'complete', 'snapshot_id': snapshot_id, 'settings': settings,
              'summaries': summaries, 'first_three_rows': previews, 'outputs': outputs,
              'data_partition': 'development', 'final_test_read': False,
              'pre_run': record(run_dir / 'pre-run.json', root),
              'metric_notes': 'Sample daily std (ddof=1); 252 sessions; daily risk-free=0; positive drawdown from prior peaks. No modeled orders or turnover.'}
    save_json(run_dir / 'summary.json', result)
    print(json.dumps({'run_directory': run_dir.relative_to(root).as_posix(), **result}, ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--download', action='store_true')
    action.add_argument('--baseline', metavar='SNAPSHOT_ID')
    arguments = parser.parse_args()
    if arguments.download:
        acquire()
    else:
        run_baseline(arguments.baseline)
