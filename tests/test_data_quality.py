"""Small synthetic boundaries: a count match must not hide missing dates or leakage."""

from copy import deepcopy
from datetime import date, datetime
import json
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo

from src.check_data_quality import expected_dates, inspect_dates
from src.prepare_etf_research import inspect_prices, parse_chart, validate_partitions


ROOT = Path(__file__).resolve().parents[1]


class DataQualityTests(unittest.TestCase):
    def test_same_row_count_can_hide_duplicate_and_missing_day(self):
        expected = [date(2024, 1, 2), date(2024, 1, 3)]
        rows = [{'date': expected[0], 'nav': 100}, {'date': expected[0], 'nav': 101}]
        original = deepcopy(rows)
        report = inspect_dates(rows, expected, ['nav'])
        self.assertEqual(report['actual_rows'], report['expected_rows'])
        self.assertEqual(report['missing_date_count'], 1)
        self.assertEqual(report['duplicate_date_count'], 1)
        self.assertFalse(report['passed'])
        self.assertEqual(rows, original)

    def test_null_is_not_a_missing_row_and_weekend_is_unexpected(self):
        day = date(2024, 1, 2)
        report = inspect_dates([{'date': day, 'nav': None}, {'date': date(2024, 1, 6), 'nav': 100}], [day], ['nav'])
        self.assertEqual(report['missing_date_count'], 0)
        self.assertEqual(report['missing_values']['nav'], 1)
        self.assertEqual(report['unexpected_date_count'], 1)
        self.assertFalse(report['passed'])

    def test_calendar_includes_early_close_and_excludes_special_closure(self):
        calendar = json.loads((ROOT / 'configs/nyse-dates-2020-2025.json').read_text(encoding='utf-8'))
        days = expected_dates(calendar, '2025-01-01', '2025-12-31')
        self.assertNotIn(date(2025, 1, 9), days)
        self.assertIn(date(2025, 7, 3), days)
        self.assertEqual(len(days), 250)
        self.assertIn(date(2021, 12, 31), expected_dates(calendar, '2021-12-30', '2022-01-03'))
        with self.assertRaises(ValueError):
            expected_dates(calendar, '2019-12-31', '2020-01-03')

    def test_invalid_prices_and_volume_fail_without_price_output(self):
        day = date(2024, 1, 2)
        row = {'date': day, 'open': 100, 'high': 99, 'low': 98, 'close': 100,
               'adj_close': float('nan'), 'volume': -1}
        report = inspect_prices([row], [day])
        self.assertFalse(report['passed'])
        self.assertEqual(report['invalid_values']['adj_close'], 1)
        self.assertEqual(report['invalid_values']['volume'], 1)
        self.assertEqual(report['ohlc_order_failures'], 1)
        self.assertNotIn('close', report)

    def test_overlap_and_reversed_partitions_rejected(self):
        for dev_end in ['2025-01-01', '2025-12-31']:
            with self.subTest(dev_end=dev_end), self.assertRaises(ValueError):
                validate_partitions({'symbols': ['SPY'], 'development': {'start': '2020-01-01', 'end': dev_end},
                                     'final_test': {'start': '2025-01-01', 'end': '2025-12-31'}})

    def test_timestamp_uses_new_york_date_and_does_not_drop_outside_rows(self):
        zone = ZoneInfo('America/New_York')
        stamp = int(datetime.fromisoformat('2024-01-03T00:30:00+00:00').timestamp())
        result = {'meta': {'symbol': 'SPY', 'currency': 'USD', 'exchangeTimezoneName': zone.key, 'instrumentType': 'ETF'},
                  'timestamp': [stamp], 'indicators': {'quote': [{field: [100] for field in ['open', 'high', 'low', 'close', 'volume']}],
                                                     'adjclose': [{'adjclose': [100]}]}}
        payload = {'chart': {'error': None, 'result': [result]}}
        rows = parse_chart(payload, 'SPY', {'start': '2024-01-02', 'end': '2024-01-02'}, zone)
        self.assertEqual(rows[0]['date'], date(2024, 1, 2))
        with self.assertRaises(ValueError):
            parse_chart(payload, 'SPY', {'start': '2024-01-03', 'end': '2024-01-03'}, zone)


if __name__ == '__main__':
    unittest.main()
