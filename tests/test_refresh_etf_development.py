"""开发快照更新的离线测试；网络由虚构响应替代，不接触封存数据。"""

from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from src import refresh_etf_development as refresh
from src.buy_hold_baseline import validate_scope
from src.check_data_quality import expected_dates
from src.prepare_etf_research import inspect_prices, parse_chart


SNAPSHOT = '20261115T090000000000Z'


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.plan = refresh.read_json(refresh.ROOT / refresh.CONFIG)
        self.zone = ZoneInfo('America/New_York')

    def fixture(self, root):
        for relative in refresh.SUPPORT:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((refresh.ROOT / relative).read_bytes())

    def response(self, url):
        symbol = urlparse(url).path.rsplit('/', 1)[-1]
        calendar = refresh.read_json(refresh.ROOT / self.plan['calendar_file'])
        days = expected_dates(calendar, **refresh.BOUNDS)
        stamps = [int(datetime(day.year, day.month, day.day, 9, 30, tzinfo=self.zone).timestamp())
                  for day in days]
        return json.dumps({'chart': {'error': None, 'result': [{
            'meta': {'symbol': symbol, 'currency': 'USD', 'exchangeTimezoneName': self.zone.key,
                     'instrumentType': 'ETF', 'regularMarketPrice': 999999},
            'timestamp': stamps,
            'indicators': {'quote': [{'open': [100] * len(days), 'high': [101] * len(days),
                                     'low': [99] * len(days), 'close': [100] * len(days),
                                     'volume': [1000] * len(days)}],
                           'adjclose': [{'adjclose': [100] * len(days)}]}
        }]}}).encode()

    def test_scope_rejects_final_test_and_changed_universe(self):
        refresh.validate_plan(self.plan)
        for key, value in [('development', {'start': '2025-01-01', 'end': '2025-12-31'}),
                           ('symbols', ['QQQ']), ('final_test_read', True),
                           ('final_test_download', True), ('final_test', {})]:
            plan = deepcopy(self.plan)
            plan[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                refresh.validate_plan(plan)

    def test_paths_and_ids_cannot_redirect_to_sealed_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for bad in ['../sealed', '2025', '', 'data/sealed/etf-research-v1']:
                with self.subTest(snapshot=bad), self.assertRaises(ValueError):
                    refresh.data_path(root, bad, 'SPY')
            with self.assertRaises(ValueError):
                refresh.data_path(root, SNAPSHOT, '../QQQ')
            with self.assertRaises(ValueError):
                refresh.safe_path(root, '../outside.csv')
            self.assertIn('/development/SPY.csv', refresh.data_path(root, SNAPSHOT, 'SPY').as_posix())

    def test_parser_rejects_out_of_window_and_wrong_identity(self):
        payload = json.loads(self.response('https://example.test/SPY'))
        payload['chart']['result'][0]['timestamp'][-1] = int(datetime(2025, 1, 2, 16, tzinfo=self.zone).timestamp())
        with self.assertRaises(ValueError):
            parse_chart(payload, 'SPY', refresh.BOUNDS, self.zone)
        payload = json.loads(self.response('https://example.test/SPY'))
        payload['chart']['result'][0]['meta']['currency'] = 'EUR'
        with self.assertRaises(ValueError):
            parse_chart(payload, 'SPY', refresh.BOUNDS, self.zone)

    def test_invalid_prices_and_duplicate_dates_fail_quality(self):
        rows = parse_chart(json.loads(self.response('https://example.test/SPY')), 'SPY', refresh.BOUNDS, self.zone)
        expected = [row['date'] for row in rows]
        rows[1]['date'] = rows[0]['date']
        rows[2]['adj_close'] = None
        rows[3]['high'] = 1
        quality = inspect_prices(rows, expected)
        self.assertFalse(quality['passed'])
        self.assertEqual(quality['duplicate_date_count'], 1)
        self.assertEqual(quality['missing_values']['adj_close'], 1)
        self.assertEqual(quality['ohlc_order_failures'], 1)

    def test_new_baseline_requires_matching_version_pair(self):
        settings = refresh.read_json(refresh.ROOT / refresh.BASELINE_CONFIG)
        original = refresh.read_json(refresh.ROOT / 'configs/etf-research-v1.json')
        validate_scope(settings, original)
        settings['source_study'] = 'etf-research-v1'
        with self.assertRaises(ValueError):
            validate_scope(settings, original)

    def test_full_fake_acquisition_baseline_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with patch.object(refresh, 'new_id', return_value=SNAPSHOT), \
                    patch.object(refresh, 'download_bytes', side_effect=self.response) as download, \
                    redirect_stdout(io.StringIO()):
                manifest = refresh.acquire(root)
                result = refresh.run_baseline(SNAPSHOT, root)
            self.assertEqual(manifest['status'], 'ready')
            self.assertEqual(download.call_count, 3)
            self.assertEqual(result['summaries']['SPY']['observations'], 1258)
            self.assertEqual(result['summaries']['SPY']['return_intervals'], 1257)
            for symbol in refresh.SYMBOLS:
                self.assertEqual(result['summaries'][symbol]['final_model_value'], 1000)
                self.assertEqual(result['summaries'][symbol]['cumulative_return'], 0)
                self.assertIsNone(result['first_three_rows'][symbol][0]['period_return'])
            for call in download.call_args_list:
                query = parse_qs(urlparse(call.args[0]).query)
                end = datetime.fromtimestamp(int(query['period2'][0]), self.zone)
                self.assertEqual(end.isoformat(), '2025-01-01T00:00:00-05:00')
            with patch.object(refresh, 'new_id', return_value=SNAPSHOT), \
                    patch.object(refresh, 'download_bytes') as blocked:
                with self.assertRaises(FileExistsError):
                    refresh.acquire(root)
                blocked.assert_not_called()
            derived = refresh.data_path(root, SNAPSHOT, 'SPY')
            with derived.open('ab') as handle:
                handle.write(b'\n')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                refresh.load_development(SNAPSHOT, 'SPY', root)

    def test_network_failure_preserves_predecision_and_failed_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with patch.object(refresh, 'new_id', return_value=SNAPSHOT), \
                    patch.object(refresh, 'download_bytes', side_effect=URLError('offline')):
                with self.assertRaises(URLError):
                    refresh.acquire(root)
            report = root / f'reports/{refresh.STUDY}/{SNAPSHOT}'
            self.assertTrue((report / 'pre-download-decision.json').is_file())
            manifest = refresh.read_json(report / 'manifest.json')
            self.assertEqual(manifest['status'], 'incomplete')
            self.assertEqual(manifest['failure_type'], 'URLError')
            self.assertFalse(manifest['final_test_requested'])
            self.assertFalse((root / 'data/sealed').exists())
            with self.assertRaises(ValueError):
                refresh.read_manifest(SNAPSHOT, root)


if __name__ == '__main__':
    unittest.main()
