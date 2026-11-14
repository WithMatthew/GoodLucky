"""W07D04: compare observed rows with an independently specified date reference.

Default command audits only the existing five-row NAV sample. No network, return
calculation, input mutation, filling or deletion. Prints a JSON quality report.
"""

from collections import Counter
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
import platform

from src.read_nav_sample import load_rows


ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_dates(calendar, start, end):
    start, end = date.fromisoformat(start), date.fromisoformat(end)
    if not (date.fromisoformat(calendar['valid_start']) <= start <= end
            <= date.fromisoformat(calendar['valid_end'])):
        raise ValueError('Range outside verified calendar coverage')
    closed = [date.fromisoformat(day) for day in calendar['closures']]
    if len(closed) != len(set(closed)) or any(day.weekday() >= 5 for day in closed):
        raise ValueError('Invalid or duplicate full-day closure')
    closed = set(closed)
    return [start + timedelta(days=i) for i in range((end - start).days + 1)
            if (start + timedelta(days=i)).weekday() < 5
            and start + timedelta(days=i) not in closed]


def inspect_dates(rows, expected, fields):
    """Count-based output only; never print prices, dates of bad test prices or returns."""
    expected = list(expected)
    if not expected or len(expected) != len(set(expected)):
        raise ValueError('Expected dates must be nonempty and unique')
    counts = Counter(row['date'] for row in rows)
    actual = set(counts)
    missing_values = {field: sum(row[field] is None for row in rows) for field in fields}
    invalid_values = {}
    for field in fields:
        count = 0
        for row in rows:
            value = row[field]
            if value is None:
                continue
            valid = (not isinstance(value, bool) and isinstance(value, (int, float))
                     and math.isfinite(value))
            if valid:
                valid = value >= 0 and int(value) == value if field == 'volume' else value > 0
            count += not valid
        invalid_values[field] = count
    result = {
        'expected_rows': len(expected), 'actual_rows': len(rows),
        'unique_dates': len(actual),
        'missing_date_count': len(set(expected) - actual),
        'unexpected_date_count': len(actual - set(expected)),
        'duplicate_date_count': sum(count > 1 for count in counts.values()),
        'extra_duplicate_rows': sum(count - 1 for count in counts.values()),
        'out_of_order_pairs': sum(a['date'] > b['date'] for a, b in zip(rows, rows[1:])),
        'missing_values': missing_values, 'invalid_values': invalid_values,
    }
    result['passed'] = not any([
        result['missing_date_count'], result['unexpected_date_count'],
        result['duplicate_date_count'], result['out_of_order_pairs'],
        *missing_values.values(), *invalid_values.values(),
    ])
    return result


def nav_audit():
    metadata = json.loads((ROOT / 'data/derived/spy_nav_2024-01-02_2024-01-08.metadata.json').read_text(encoding='utf-8'))
    calendar_path = ROOT / 'configs/nyse-dates-2020-2025.json'
    calendar = json.loads(calendar_path.read_text(encoding='utf-8'))
    rows = load_rows(ROOT / metadata['sample_file'])
    result = inspect_dates(rows, expected_dates(calendar, metadata['sample_start'], metadata['sample_end']), ['nav'])
    result['raw_hash_matches'] = sha256(ROOT / metadata['raw_file']) == metadata['raw_sha256']
    result['sample_hash_matches'] = sha256(ROOT / metadata['sample_file']) == metadata['sample_sha256']
    result['passed'] &= result['raw_hash_matches'] and result['sample_hash_matches']
    return {'scope': 'SPY published NAV, 2024-01-02..08 only; sorted in memory',
            'python_version': platform.python_version(),
            'calendar_sha256': sha256(calendar_path), 'quality': result}


if __name__ == '__main__':
    print(json.dumps(nav_audit(), ensure_ascii=False, indent=2))
