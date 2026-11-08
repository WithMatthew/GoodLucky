"""日期与缺失边界；只用虚构记录，不联网或修改真实数据。"""

from copy import deepcopy
from datetime import date
import unittest

from src.read_nav_sample import inspect_rows, parse_rows


class NavSampleTests(unittest.TestCase):
    def test_sort_keeps_missing_and_original_input(self):
        raw = [{"date": "2024-01-08", "nav": "102", "source_row": "1"},
               {"date": "2024-01-02", "nav": "", "source_row": "2"}]
        original = deepcopy(raw)
        rows = parse_rows(raw)
        self.assertEqual(rows[0]["date"], date(2024, 1, 2))
        self.assertIsNone(rows[0]["nav"])
        self.assertEqual(raw, original)
        self.assertEqual(inspect_rows(rows)["missing_nav_dates"], ["2024-01-02"])

    def test_invalid_calendar_date_and_wrong_format_are_rejected(self):
        for text in ["2024-02-30", "20240102", "02/01/2024"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_rows([{"date": text, "nav": "100", "source_row": "1"}])

    def test_weekend_is_valid_date_not_proof_of_trading(self):
        rows = parse_rows([{"date": "2024-01-06", "nav": "100", "source_row": "1"}])
        self.assertEqual(rows[0]["date"].weekday(), 5)

    def test_duplicates_are_reported_without_choosing_a_price(self):
        for other in ["100", "101"]:
            with self.subTest(other=other):
                rows = parse_rows([
                    {"date": "2024-01-02", "nav": "100", "source_row": "1"},
                    {"date": "2024-01-02", "nav": other, "source_row": "2"}])
                self.assertEqual(inspect_rows(rows)["duplicate_dates"], {"2024-01-02": 2})
                self.assertEqual(len(rows), 2)

    def test_nonfinite_or_nonpositive_nav_is_rejected(self):
        for nav in ["nan", "inf", "0", "-1", "unknown"]:
            with self.subTest(nav=nav), self.assertRaises(ValueError):
                parse_rows([{"date": "2024-01-02", "nav": nav, "source_row": "1"}])


if __name__ == "__main__":
    unittest.main()
