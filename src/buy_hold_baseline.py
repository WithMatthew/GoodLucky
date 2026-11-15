"""W09D03-B2：只用既定开发数据构建供应商复权口径参考，无订单。

运行：python -X utf8 -B -m src.buy_hold_baseline
每次产生新的本地运行目录，不覆写快照。标准库，无导入时IO或联网。
首行没有单期收益；不按表现选择日期、标的或字段，不追加分红现金。
"""

import csv
from datetime import date, datetime, timezone
import json
from math import isfinite, sqrt
from pathlib import Path
import platform
from statistics import mean, stdev

from src.check_data_quality import expected_dates, sha256
from src.prepare_etf_research import load_development


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "configs/buy-hold-baseline-v1.json"
RESEARCH_PLAN = ROOT / "configs/etf-research-v1.json"
MANIFEST = ROOT / "reports/etf-research-v1/manifest.json"
SYMBOLS = ["SPY", "DIA", "QQQ"]
BOUNDS = {"start": "2020-01-01", "end": "2024-12-31"}


def _positive(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and isfinite(value) and value > 0)


def normalize_adjusted_path(rows, initial_value=1000):
    """日期严格递增，不填补/排序/删行；返回比例曲线，不生成真实份数。"""
    rows = list(rows)
    if not rows or not _positive(initial_value):
        raise ValueError("需要非空观测和有限正数的模型起点")
    previous_day = None
    for row in rows:
        day = row["date"]
        if type(day) is not date or (previous_day is not None and day <= previous_day):
            raise ValueError("日期必须严格递增且不重复")
        if not _positive(row["adj_close"]):
            raise ValueError("调整值必须为有限正数；不填补缺失")
        previous_day = day

    anchor = rows[0]["adj_close"]
    previous_price = None
    path = []
    for row in rows:
        value = row["adj_close"]
        normalized_value = value / anchor
        model_value = initial_value * normalized_value
        period_return = None if previous_price is None else value / previous_price - 1
        if not all(isfinite(v) for v in [normalized_value, model_value]
                   + ([] if period_return is None else [period_return])):
            raise ValueError("归一化结果超出有限数值范围")
        path.append({"date": row["date"].isoformat(),
                     "normalized_value": normalized_value,
                     "model_value": model_value,
                     "period_return": period_return,
                     "cumulative_return": normalized_value - 1})
        previous_price = value
    return path


def summarize_path(path, sessions=252, daily_risk_free=0):
    """风险指标仅描述当前参考曲线；样本标准差ddof=1，夏普无风险日收益为0。"""
    if not path:
        raise ValueError("参考曲线不可为空")
    returns = [row["period_return"] for row in path[1:]]
    deviation = stdev(returns) if len(returns) >= 2 else None
    peak, maximum_drawdown = path[0]["normalized_value"], 0.0
    for row in path:
        value = row["normalized_value"]
        peak = max(peak, value)
        maximum_drawdown = max(maximum_drawdown, 1 - value / peak)
    return {
        "observations": len(path), "return_intervals": len(returns),
        "first_date": path[0]["date"], "last_date": path[-1]["date"],
        "final_normalized_value": path[-1]["normalized_value"],
        "final_model_value": path[-1]["model_value"],
        "cumulative_return": path[-1]["cumulative_return"],
        "maximum_drawdown": maximum_drawdown,
        "annualized_volatility": None if deviation is None else deviation * sqrt(sessions),
        "sharpe_rf_zero": (None if not deviation else
                           (mean(returns) - daily_risk_free) / deviation * sqrt(sessions)),
        "executed_trade_count": None, "executed_turnover": None,
        "execution_note": "No orders modeled; trade count and executed turnover are not available.",
    }


def validate_scope(settings, plan):
    """此入口只允许已记录的教学范围，修改设置不能开启封存区间。"""
    versions = {"buy-hold-baseline-v1": "etf-research-v1",
                "buy-hold-baseline-v2": "etf-development-v2"}
    experiment = settings.get("experiment_id")
    if experiment not in versions:
        raise ValueError("未知参考实验版本")
    expected = {"experiment_id": experiment, "source_study": versions[experiment],
                "symbols": SYMBOLS, "development": BOUNDS, "field": "adj_close",
                "frequency": "1d", "timezone": "America/New_York", "currency": "USD",
                "method": "provider_adjusted_close_ratio", "initial_model_value": 1000.0,
                "cash_weight": 0.0, "cash_interest": 0.0, "external_flows": False,
                "additional_trading_costs": 0.0, "investor_tax": 0.0,
                "orders_modeled": False, "annualization_sessions": 252,
                "daily_risk_free_rate": 0.0, "volatility_ddof": 1, "first_period_return": None}
    if any(settings.get(key) != value for key, value in expected.items()):
        raise ValueError("设置偏离预先记录的开发参考口径；请另建明确研究版本")
    if (plan["study_id"] != "etf-research-v1" or plan["symbols"] != SYMBOLS
            or plan["development"] != BOUNDS or plan["interval"] != "1d"
            or plan["currency"] != "USD" or plan["timezone"] != "America/New_York"):
        raise ValueError("原研究范围与本课预定范围不符")


def guarded_development_path(root, symbol, entry):
    """在任何数据读取前拒绝封存路径、目录跳转和软链接重定向。"""
    if symbol not in SYMBOLS or entry["partition"] != "development" or entry["symbol"] != symbol:
        raise ValueError("只允许既定开发标的")
    relative = f"data/derived/etf-research-v1/development/{symbol}.csv"
    if entry["derived"]["path"] != relative:
        raise ValueError("开发数据路径不符合既定目录")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path.relative_to(root.resolve()).as_posix() != relative:
        raise ValueError("开发数据路径重定向；停止读取")
    return path


def save_json(path, payload):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def file_record(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}


def run():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    if settings.get("experiment_id") != "buy-hold-baseline-v1":
        raise ValueError("旧入口只读取原v1；新快照请用refresh_etf_development入口")
    plan = json.loads(RESEARCH_PLAN.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validate_scope(settings, plan)
    if manifest.get("status") != "sealed_for_teaching":
        raise ValueError("原研究快照状态不符")
    support = {item["path"]: item for item in manifest["supporting_files"]}
    # 只核对这些非行情支持文件；绝不调用会枚举封存行情的全局verify。
    support_names = ["configs/etf-research-v1.json", "configs/nyse-dates-2020-2025.json",
                     "src/prepare_etf_research.py", "src/check_data_quality.py"]
    for relative in support_names:
        if sha256(ROOT / relative) != support[relative]["sha256"]:
            raise ValueError(f"原支持文件版本变化：{relative}")
    entries, missing = {}, []
    for symbol in SYMBOLS:
        matches = [item for item in manifest["snapshots"]
                   if item["partition"] == "development" and item["symbol"] == symbol]
        if len(matches) != 1:
            raise ValueError("开发快照元数据应唯一")
        data_path = guarded_development_path(ROOT, symbol, matches[0])
        if not data_path.is_file():
            missing.append(data_path.relative_to(ROOT).as_posix())
        entries[symbol] = matches[0]
    if missing:
        raise FileNotFoundError("缺少原开发快照；恢复相同版本后重试：" + ", ".join(missing))
    calendar_path = ROOT / "configs/nyse-dates-2020-2025.json"
    calendar = json.loads(calendar_path.read_text(encoding="utf-8"))
    expected = expected_dates(calendar, **BOUNDS)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = ROOT / "reports/buy-hold-baseline-v1/runs" / stamp
    run_dir.mkdir(parents=True, exist_ok=False)
    # 在读取或比较开发行情表现前落盘，后续不覆写。
    provenance = {
        "run_id": stamp, "recorded_before_reading_prices": True,
        "python_version": platform.python_version(), "settings": settings,
        "inputs": [entries[symbol]["derived"] for symbol in SYMBOLS],
        "code_and_config": [file_record(ROOT / relative) for relative in
                            support_names + ["src/buy_hold_baseline.py",
                                             "tests/test_buy_hold_baseline.py",
                                             "configs/buy-hold-baseline-v1.json"]],
        "source_manifest": file_record(MANIFEST),
        "calendar_scope": calendar["scope"],
        "data_partition": "development", "final_test_read": False,
    }
    save_json(run_dir / "pre-run.json", provenance)
    summaries, preview, outputs = {}, {}, []
    for symbol in SYMBOLS:
        # 复用原开发入口及其哈希验证；不传任意路径或最终测试选择器。
        rows = load_development(symbol)
        if [row["date"] for row in rows] != expected:
            raise ValueError("开发日期与既定日历不完全一致；不排序、填补或删行")
        path = normalize_adjusted_path(rows, settings["initial_model_value"])
        summaries[symbol] = summarize_path(path, settings["annualization_sessions"],
                                           settings["daily_risk_free_rate"])
        output = run_dir / f"{symbol}.csv"
        with output.open("x", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(path[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(path)
        outputs.append(file_record(output))
        preview[symbol] = path[:3]
    result = {"run_id": stamp, "status": "complete", "data_partition": "development",
              "final_test_read": False, "summaries": summaries, "first_three_rows": preview,
              "outputs": outputs, "settings": settings,
              "metric_notes": "Volatility: sample daily std × sqrt(252). Sharpe: mean daily return / sample std × sqrt(252), risk-free=0. Drawdown is a positive fraction from prior running peaks. No trade/turnover model; not zero trading evidence.",
              "pre_run": file_record(run_dir / "pre-run.json")}
    save_json(run_dir / "summary.json", result)
    print(json.dumps({"run_directory": run_dir.relative_to(ROOT).as_posix(),
                      "summary": summaries, "final_test_read": False},
                     ensure_ascii=False, indent=2, allow_nan=False))
    return result


if __name__ == "__main__":
    run()
