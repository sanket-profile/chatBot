"""Intraday India + Crypto hybrid strategy reference implementation.

This module provides:
- Feature engineering for 5-minute OHLCV data
- Regime-adaptive signal generation
- Single-symbol backtesting with fees/slippage
- Basic risk controls aligned to a 5-6% daily loss tolerance

Input dataframe schema:
    timestamp, open, high, low, close, volume, symbol

Timestamps should be timezone-aware for production systems. For simple
research workflows, naive timestamps are accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd


@dataclass
class StrategyConfig:
    initial_capital: float = 20_000.0
    risk_per_trade: float = 0.0075
    max_position_fraction: float = 0.25
    daily_hard_stop_fraction: float = 0.058
    daily_soft_stop_fraction: float = 0.045
    fee_rate: float = 0.0005
    slippage_rate: float = 0.0008
    atr_stop_multiple: float = 1.2
    atr_take_multiple: float = 1.8
    max_holding_bars: int = 18
    trend_score_threshold: float = 1.2
    rvol_threshold: float = 1.3
    zscore_threshold: float = 1.8


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute indicators required by the strategy."""
    data = df.copy().sort_values("timestamp").reset_index(drop=True)

    data["ret"] = np.log(data["close"] / data["close"].shift(1)).fillna(0.0)
    data["ema12"] = data["close"].ewm(span=12, adjust=False).mean()
    data["ema26"] = data["close"].ewm(span=26, adjust=False).mean()
    data["mu"] = data["ema12"] - data["ema26"]

    vol_sma20 = data["volume"].rolling(20, min_periods=5).mean()
    data["rvol"] = data["volume"] / vol_sma20.replace(0, np.nan)
    data["rvol"] = data["rvol"].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    cumulative_pv = (data["close"] * data["volume"]).cumsum()
    cumulative_v = data["volume"].cumsum().replace(0, np.nan)
    data["vwap"] = cumulative_pv / cumulative_v

    data["sigma20"] = data["ret"].rolling(20, min_periods=10).std().fillna(0.0)
    spread = data["close"] - data["vwap"]
    spread_std = spread.rolling(60, min_periods=20).std().replace(0, np.nan)
    data["zscore"] = (spread / spread_std).replace([np.inf, -np.inf], np.nan).fillna(0.0)

    prev_close = data["close"].shift(1)
    tr_components = pd.concat(
        [
            data["high"] - data["low"],
            (data["high"] - prev_close).abs(),
            (data["low"] - prev_close).abs(),
        ],
        axis=1,
    )
    data["tr"] = tr_components.max(axis=1)
    data["atr14"] = data["tr"].rolling(14, min_periods=5).mean().bfill()

    eps = 1e-8
    data["trend_score"] = (data["mu"].abs()) / (data["close"] * data["sigma20"] + eps)

    return data


def compute_alpha(row: pd.Series, cfg: StrategyConfig) -> int:
    """Return {-1, 0, +1} directional signal."""
    trend_regime = row["trend_score"] > cfg.trend_score_threshold

    if trend_regime:
        if row["close"] > row["vwap"] and row["rvol"] > cfg.rvol_threshold and row["ret"] > 0:
            return 1
        if row["close"] < row["vwap"] and row["rvol"] > cfg.rvol_threshold and row["ret"] < 0:
            return -1
        return 0

    if abs(row["zscore"]) > cfg.zscore_threshold:
        return -int(np.sign(row["zscore"]))

    return 0


def confidence(row: pd.Series) -> float:
    """Conviction score in [0,1]."""
    z_leg = min(1.0, abs(float(row["zscore"])) / 3.0)
    v_leg = min(1.0, float(row["rvol"]) / 2.0)
    return 0.5 * z_leg + 0.5 * v_leg


def position_notional(capital: float, row: pd.Series, cfg: StrategyConfig) -> float:
    """Risk-targeted notional sizing with hard caps."""
    atr = max(float(row["atr14"]), 1e-6)
    stop_distance_pct = (cfg.atr_stop_multiple * atr) / max(float(row["close"]), 1e-6)
    raw = capital * cfg.risk_per_trade * (0.5 + confidence(row)) / max(stop_distance_pct, 1e-4)

    capped = min(raw, capital * cfg.max_position_fraction)
    return max(1_000.0, capped)


def backtest_single_symbol(df: pd.DataFrame, cfg: StrategyConfig | None = None) -> Dict[str, float]:
    """Backtest one symbol on intraday OHLCV bars.

    Execution model:
    - Enter/exit at current close adjusted for slippage.
    - Fees charged on both entry and exit.
    """
    cfg = cfg or StrategyConfig()
    data = add_features(df)

    capital = cfg.initial_capital
    start_of_day_capital = cfg.initial_capital
    position = 0
    units = 0.0
    entry_price = 0.0
    holding_bars = 0
    trade_pnls: List[float] = []

    for _, row in data.iterrows():
        px = float(row["close"])
        alpha = compute_alpha(row, cfg)

        if capital <= start_of_day_capital * (1.0 - cfg.daily_hard_stop_fraction):
            if position != 0:
                exit_px = px * (1 - cfg.slippage_rate if position > 0 else 1 + cfg.slippage_rate)
                gross = (exit_px - entry_price) * units * position
                fees = cfg.fee_rate * (abs(units * entry_price) + abs(units * exit_px))
                pnl = gross - fees
                capital += pnl
                trade_pnls.append(pnl)
                position = 0
                units = 0.0
            continue

        if position == 0:
            if capital <= start_of_day_capital * (1.0 - cfg.daily_soft_stop_fraction):
                continue

            if alpha == 0:
                continue

            notional = position_notional(capital, row, cfg)
            fill_px = px * (1 + cfg.slippage_rate if alpha > 0 else 1 - cfg.slippage_rate)
            qty = notional / max(fill_px, 1e-6)
            fees = cfg.fee_rate * notional

            capital -= fees
            position = alpha
            units = qty
            entry_price = fill_px
            holding_bars = 0
            continue

        holding_bars += 1
        atr = max(float(row["atr14"]), 1e-6)
        stop = cfg.atr_stop_multiple * atr
        take = cfg.atr_take_multiple * atr

        hit_stop = (px <= entry_price - stop) if position > 0 else (px >= entry_price + stop)
        hit_take = (px >= entry_price + take) if position > 0 else (px <= entry_price - take)
        time_exit = holding_bars >= cfg.max_holding_bars
        reversal = alpha == -position and alpha != 0

        if hit_stop or hit_take or time_exit or reversal:
            exit_px = px * (1 - cfg.slippage_rate if position > 0 else 1 + cfg.slippage_rate)
            gross = (exit_px - entry_price) * units * position
            fees = cfg.fee_rate * (abs(units * entry_price) + abs(units * exit_px))
            pnl = gross - fees
            capital += pnl
            trade_pnls.append(pnl)
            position = 0
            units = 0.0

    total_return = (capital / cfg.initial_capital) - 1.0
    wins = sum(1 for x in trade_pnls if x > 0)
    trades = len(trade_pnls)
    win_rate = (wins / trades) if trades else 0.0

    return {
        "final_capital": round(capital, 2),
        "total_return": round(total_return, 4),
        "trades": trades,
        "win_rate": round(win_rate, 4),
        "avg_trade_pnl": round(float(np.mean(trade_pnls)) if trade_pnls else 0.0, 2),
    }


def run_from_csv(path: str) -> Dict[str, float]:
    """Convenience runner for quick experimentation."""
    df = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    return backtest_single_symbol(df)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backtest intraday India+Crypto hybrid strategy")
    parser.add_argument("csv_path", type=str, help="Path to OHLCV CSV with timestamp/open/high/low/close/volume")
    args = parser.parse_args()

    result = run_from_csv(args.csv_path)
    print(result)
