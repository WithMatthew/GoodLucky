import io
import unittest
import zipfile

from src.cross_asset_data import check_snapshot_id, parse_french_rf, validate_plan


def make_zip(text):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('F-F_Research_Data_Factors_daily.CSV', text)
    return buffer.getvalue()


SAMPLE = """This file was created using the 202510 CRSP database.

,Mkt-RF,SMB,HML,RF
20070531,   0.50,  -0.10,   0.20,   0.019
20070601,   0.30,   0.05,  -0.10,   0.020
20241231,  -0.40,   0.10,   0.00,   0.017
20250102,   9.99,   9.99,   9.99,   9.999

Copyright 2025 Eugene F. Fama and Kenneth R. French
"""


class ParseFrenchRfTest(unittest.TestCase):
    def test_window_and_units(self):
        rf = parse_french_rf(make_zip(SAMPLE), '2007-06-01', '2024-12-31')
        self.assertEqual([d.strftime('%Y-%m-%d') for d in rf.index], ['2007-06-01', '2024-12-31'])
        # 0.020 percent/day -> 0.00020 decimal/day
        self.assertAlmostEqual(rf.iloc[0], 0.00020)
        self.assertAlmostEqual(rf.iloc[1], 0.00017)
        self.assertTrue((rf < 0.001).all())  # 2025 的 9.999 未被读入

    def test_empty_window_raises(self):
        with self.assertRaises(ValueError):
            parse_french_rf(make_zip(SAMPLE), '1990-01-01', '1990-12-31')


MONTHLY = """This file was created using the 202510 CRSP database.

,Mkt-RF,SMB,HML,RF
200705,   3.00,   0.10,   0.20,   0.41
200706,  -1.00,   0.05,  -0.10,   0.40
202412,  -3.00,  -2.00,  -3.00,   0.37
202501,   9.99,   9.99,   9.99,   9.99

 Annual Factors: January-December
,Mkt-RF,SMB,HML,RF
  2007,   1.00,   1.00,   1.00,   4.40
"""


class ParseFrenchMonthlyTest(unittest.TestCase):
    def test_monthly_window_stops_before_annual(self):
        rf = parse_french_rf(make_zip(MONTHLY), '2007-06-01', '2024-12-31', freq='monthly')
        self.assertEqual([str(p) for p in rf.index], ['2007-06', '2024-12'])
        self.assertAlmostEqual(rf.iloc[0], 0.0040)
        self.assertAlmostEqual(rf.iloc[1], 0.0037)


class GuardTest(unittest.TestCase):
    def test_snapshot_id_rejects_paths(self):
        with self.assertRaises(ValueError):
            check_snapshot_id('../sealed')

    def test_plan_rejects_final_test(self):
        with self.assertRaises(ValueError):
            validate_plan({'study_id': 'cross-asset-dev-v1', 'final_test_read': True})


if __name__ == '__main__':
    unittest.main()
