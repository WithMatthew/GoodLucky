"""W11D02：跨资产 7 只 ETF + Ken French 日频 RF 开发快照（2007-06-01..2024-12-31）。

    python -X utf8 -m src.cross_asset_data --download        # 显式联网，生成新快照
    python -X utf8 -m src.cross_asset_data --verify <id>     # 离线核对哈希与行数

导入本模块不联网、不写文件；不请求、不解析 2025 封存区间；不涉及任何交易。
下载前先落盘配置与支持文件哈希；失败的尝试同样保留清单，绝不覆写已有快照。
"""

import argparse
from datetime import date, datetime, timezone
from importlib.metadata import version
import io
import json
from pathlib import Path
import platform
import re
from urllib.request import Request, urlopen
import zipfile
from zoneinfo import ZoneInfo

import pandas as pd

from src.check_data_quality import sha256
from src.prepare_etf_research import chart_url, parse_chart, save_json, timestamp_now

ROOT = Path(__file__).resolve().parents[1]
STUDY = 'cross-asset-dev-v1'
CONFIG = f'configs/{STUDY}.json'
SYMBOLS = ['SPY', 'QQQ', 'EFA', 'TLT', 'IEF', 'GLD', 'BIL']
BOUNDS = {'start': '2007-06-01', 'end': '2024-12-31'}
PRICE_FIELDS = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
SUPPORT = [CONFIG, 'src/cross_asset_data.py', 'src/prepare_etf_research.py',
           'src/check_data_quality.py', 'requirements-research.txt']


# ---------- 纯函数（可离线测试） ----------

def validate_plan(plan):
    expected = {'study_id': STUDY, 'symbols': SYMBOLS, 'development': BOUNDS,
                'interval': '1d', 'timezone': 'America/New_York', 'currency': 'USD',
                'final_test_download': False, 'final_test_read': False}
    if any(plan.get(key) != value for key, value in expected.items()):
        raise ValueError('Plan must keep the authorized development-only scope')


def check_snapshot_id(snapshot_id):
    if not isinstance(snapshot_id, str) or not re.fullmatch(r'\d{8}T\d{12}Z', snapshot_id):
        raise ValueError('Invalid snapshot identifier')
    return snapshot_id


def parse_french_rf(zip_bytes, start, end, freq='daily'):
    """从 Ken French 三因子 zip 中只取 [start, end] 内的 RF。

    源文件单位：百分比/期（daily 为每日，monthly 为每月；0.01 表示 0.01%）。
    返回 Series（小数/期）：daily 用 DatetimeIndex，monthly 用 PeriodIndex('M')。
    窗口外（含 2025 及以后）的行在转成数值前就被跳过。
    注意：日频文件只保留两位小数（0.01%/日 ≈ 年化 2.5% 一档），精度不足，研究用月频。
    """
    digits = {'daily': 8, 'monthly': 6}[freq]
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith('.csv')]
        if len(names) != 1:
            raise ValueError('Expected exactly one CSV inside the French zip')
        text = archive.read(names[0]).decode('latin-1')
    lines = text.splitlines()
    header_at = next(i for i, line in enumerate(lines)
                     if line.replace(' ', '').startswith(',Mkt-RF'))
    columns = [c.strip() for c in lines[header_at].split(',')]
    rf_col = columns.index('RF')
    lo, hi = start.replace('-', '')[:digits], end.replace('-', '')[:digits]
    keys, values = [], []
    for line in lines[header_at + 1:]:
        cells = [c.strip() for c in line.split(',')]
        if not re.fullmatch(rf'\d{{{digits}}}', cells[0]):
            break  # 首个数据块结束（月频文件之后是年度表，不读取）
        if lo <= cells[0] <= hi:
            keys.append(cells[0])
            values.append(float(cells[rf_col]) / 100.0)
    if not keys:
        raise ValueError('No RF rows inside the requested window')
    if freq == 'daily':
        index = pd.to_datetime(keys, format='%Y%m%d')
    else:
        index = pd.PeriodIndex([f'{k[:4]}-{k[4:]}' for k in keys], freq='M')
    return pd.Series(values, index=index, name='rf')


# ---------- 文件与网络（只在显式 --download 时运行） ----------

def snapshot_dir(kind, snapshot_id, root=ROOT):
    check_snapshot_id(snapshot_id)
    base = {'raw': 'data/raw', 'derived': 'data/derived', 'report': 'reports'}[kind]
    return root / base / STUDY / snapshot_id


def record(path, root=ROOT):
    return {'path': path.relative_to(root).as_posix(), 'sha256': sha256(path),
            'bytes': path.stat().st_size}


def download_bytes(url):
    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60) as response:
        return response.read()


def write_new_bytes(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(payload)


def acquire(root=ROOT):
    plan = json.loads((root / CONFIG).read_text(encoding='utf-8'))
    validate_plan(plan)
    zone = ZoneInfo(plan['timezone'])
    snapshot_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    report = snapshot_dir('report', snapshot_id, root)
    report.mkdir(parents=True, exist_ok=False)
    raw_dir, derived_dir = snapshot_dir('raw', snapshot_id, root), snapshot_dir('derived', snapshot_id, root)
    support = [record(root / rel, root) for rel in SUPPORT]
    decision_path = report / 'pre-download-decision.json'
    save_json(decision_path, {'recorded_at_utc': timestamp_now(), 'snapshot_id': snapshot_id,
                              'plan': plan, 'supporting_files': support,
                              'recorded_before_download': True, 'final_test_requested': False})
    manifest = {'study_id': STUDY, 'snapshot_id': snapshot_id, 'status': 'incomplete',
                'started_at_utc': timestamp_now(), 'python_version': platform.python_version(),
                'pandas_version': version('pandas'), 'tzdata_version': version('tzdata'),
                'pre_download': record(decision_path, root), 'files': [],
                'final_test_requested': False, 'final_test_read': False}
    try:
        for symbol in SYMBOLS:
            url = chart_url(symbol, BOUNDS, zone)
            raw = raw_dir / f'{symbol}.json'
            payload = download_bytes(url)
            write_new_bytes(raw, payload)
            entry = {'kind': 'price', 'symbol': symbol, 'source_url': url,
                     'downloaded_at_utc': timestamp_now(), 'raw': record(raw, root)}
            manifest['files'].append(entry)
            rows = parse_chart(json.loads(payload), symbol, BOUNDS, zone)
            frame = pd.DataFrame(rows, columns=['date', *PRICE_FIELDS])
            derived = derived_dir / f'{symbol}.csv'
            derived.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(derived, index=False, mode='x', lineterminator='\n')
            entry.update({'derived': record(derived, root), 'rows': len(frame),
                          'first_date': str(frame['date'].iloc[0]),
                          'last_date': str(frame['date'].iloc[-1])})
            print(json.dumps({'symbol': symbol, 'rows': len(frame)}), flush=True)
        for freq, url_key, raw_name, out_name in [
                ('daily', 'rf_source_url', 'F-F_Research_Data_Factors_daily_CSV.zip', 'rf_daily_french_rounded.csv'),
                ('monthly', 'rf_monthly_source_url', 'F-F_Research_Data_Factors_CSV.zip', 'rf_monthly.csv')]:
            url = plan[url_key]
            payload = download_bytes(url)
            raw = raw_dir / raw_name
            write_new_bytes(raw, payload)
            entry = {'kind': f'rf_{freq}', 'source_url': url, 'downloaded_at_utc': timestamp_now(),
                     'raw': record(raw, root),
                     'note': 'raw zip also covers post-2024 rows; only development rows parsed'}
            manifest['files'].append(entry)
            rf = parse_french_rf(payload, **BOUNDS, freq=freq)
            derived = derived_dir / out_name
            rf.rename_axis('date' if freq == 'daily' else 'month').to_csv(
                derived, mode='x', lineterminator='\n', date_format='%Y-%m-%d')
            entry.update({'derived': record(derived, root), 'rows': len(rf),
                          'first': str(rf.index[0])[:10], 'last': str(rf.index[-1])[:10]})
            print(json.dumps({'series': f'rf_{freq}', 'rows': len(rf)}), flush=True)
        manifest['status'] = 'ready'
    except Exception as error:
        manifest['failure_type'] = type(error).__name__
        raise
    finally:
        manifest['recorded_at_utc'] = timestamp_now()
        save_json(report / 'manifest.json', manifest)
    print(json.dumps({'snapshot_id': snapshot_id, 'status': manifest['status']}))
    return manifest


# ---------- 研究读取入口（离线） ----------

def read_manifest(snapshot_id, root=ROOT):
    path = snapshot_dir('report', snapshot_id, root) / 'manifest.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if manifest['status'] != 'ready' or manifest['final_test_read'] is not False:
        raise ValueError('Snapshot is not ready for development research')
    for entry in manifest['files']:
        for key in ('raw', 'derived'):
            if sha256(root / entry[key]['path']) != entry[key]['sha256']:
                raise ValueError(f"Hash mismatch: {entry[key]['path']}")
    return manifest


def load_prices(snapshot_id, root=ROOT):
    """返回 {symbol: DataFrame(index=DatetimeIndex, columns=PRICE_FIELDS)}，不做任何清洗。"""
    read_manifest(snapshot_id, root)
    out = {}
    for symbol in SYMBOLS:
        path = snapshot_dir('derived', snapshot_id, root) / f'{symbol}.csv'
        frame = pd.read_csv(path, parse_dates=['date']).set_index('date')
        if frame.index.max() > pd.Timestamp(BOUNDS['end']):
            raise ValueError('Development loader refuses rows after 2024-12-31')
        out[symbol] = frame
    return out


def load_rf_monthly(snapshot_id, root=ROOT):
    """月频 1 个月国库券收益（小数/月），PeriodIndex('M')。研究口径的 RF 来源。"""
    read_manifest(snapshot_id, root)
    path = snapshot_dir('derived', snapshot_id, root) / 'rf_monthly.csv'
    frame = pd.read_csv(path, dtype={'month': str})
    return pd.Series(frame['rf'].to_numpy(), index=pd.PeriodIndex(frame['month'], freq='M'), name='rf')


def load_rf_daily_rounded(snapshot_id, root=ROOT):
    """French 日频 RF（两位小数四舍五入版），仅用于对照精度问题，不作研究口径。"""
    read_manifest(snapshot_id, root)
    path = snapshot_dir('derived', snapshot_id, root) / 'rf_daily_french_rounded.csv'
    return pd.read_csv(path, parse_dates=['date']).set_index('date')['rf']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--download', action='store_true')
    group.add_argument('--verify', metavar='SNAPSHOT_ID')
    args = parser.parse_args()
    if args.download:
        acquire()
    else:
        manifest = read_manifest(args.verify)
        print(json.dumps({'snapshot_id': args.verify, 'verified_files': len(manifest['files'])}))


if __name__ == '__main__':
    main()
