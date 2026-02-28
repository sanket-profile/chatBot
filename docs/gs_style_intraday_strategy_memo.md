# Goldman Sachs-Style Quantitative Strategy Memo

## Strategy Name
**India-Crypto Intraday Regime-Adaptive Momentum Mean-Reversion Hybrid (IC-RAMMRH)**

## Portfolio Context
- **Capital base:** ₹20,000
- **Holding horizon:** Intraday (5-minute bars)
- **Markets:** NSE liquid equities/ETFs + liquid INR-quoted crypto pairs (or USDT proxies converted to INR)
- **Daily risk tolerance:** 5–6% portfolio loss cap

---

## 1) Strategy Thesis
The strategy exploits two short-horizon inefficiencies that repeatedly appear in Indian cash equities and crypto microstructure:

1. **Opening momentum continuation under high relative volume** (institutional order-flow imbalance and delayed price discovery).
2. **Intraday volatility overreaction mean-reversion** after statistically extreme moves away from VWAP.

A market-state classifier routes capital between those two motifs:

- **Trend regime:** trade momentum breakout pullbacks.
- **Range regime:** trade VWAP reversion from statistically stretched prices.

This hybrid structure lowers edge cyclicality because momentum and reversion have low contemporaneous signal correlation.

---

## 2) Universe Selection

### Indian leg (NSE cash/ETF)
- Select instruments with:
  - 20-day median traded value ≥ ₹50 crore.
  - Median bid-ask spread ≤ 15 bps.
  - Consistent intraday prints (few missing bars).
- Practical shortlist: NIFTY50 names + NIFTYBEES / BANKBEES for high fill quality.

### Crypto leg
- Liquid, low-fee symbols: BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT (mapped to INR notionally).
- Minimum 30-day hourly ADV threshold to avoid slippage shocks.

### Why this mix
- Indian equities provide cleaner open-auction signals.
- Crypto provides 24/7 diversification and more frequent volatility dislocations.
- Cross-market blending reduces single-session idle capital.

---

## 3) Signal Generation Logic (Mathematical)

Let price bars be indexed by time \(t\).

### Core features
- Log return: \(r_t = \ln(P_t/P_{t-1})\)
- Intraday VWAP: \(\text{VWAP}_t = \frac{\sum_{i=1}^{t} p_i v_i}{\sum_{i=1}^{t} v_i}\)
- Relative volume: \(\text{RVOL}_t = \frac{V_t}{\text{SMA}_{20}(V)_t}\)
- Volatility: \(\sigma_t = \text{STD}_{20}(r)_t\)
- Short trend: \(\mu_t = \text{EMA}_{12}(P)_t - \text{EMA}_{26}(P)_t\)
- Stretch z-score: \(z_t = \frac{P_t - \text{VWAP}_t}{\text{STD}_{60}(P-\text{VWAP})_t}\)

### Regime filter
Define trend score:
\[
\text{TS}_t = \frac{|\mu_t|}{P_t \cdot \sigma_t + \epsilon}
\]
- **Trend regime:** \(\text{TS}_t > 1.2\)
- **Range regime:** \(\text{TS}_t \leq 1.2\)

### Directional alpha score
\[
\alpha_t =
\begin{cases}
+1 & \text{if Trend regime and } P_t > \text{VWAP}_t,\ \text{RVOL}_t > 1.3,\ r_t > 0 \\
-1 & \text{if Trend regime and } P_t < \text{VWAP}_t,\ \text{RVOL}_t > 1.3,\ r_t < 0 \\
-\text{sign}(z_t) & \text{if Range regime and } |z_t| > 1.8 \\
0 & \text{otherwise}
\end{cases}
\]

Signal confidence:
\[
c_t = \min\left(1,\ \frac{|z_t|}{3}\right)\cdot 0.5 + \min\left(1,\ \frac{\text{RVOL}_t}{2}\right)\cdot 0.5
\]

---

## 4) Entry Rules
A position is opened only if all are true:

1. Session time is tradable window:
   - India cash: 09:25–15:10 IST
   - Crypto overlay: any time, but avoid ±5 minutes around hourly close if spread spikes.
2. \(\alpha_t \in \{-1, +1\}\)
3. Expected edge net of friction is positive:
   - \(E[R_{t+1}] = \alpha_t \cdot (0.35\sigma_t + 0.15|z_t|\sigma_t)\)
   - Require \(E[R_{t+1}] > \text{fees} + \text{slippage buffer}\)
4. Portfolio daily loss < 4.5% (soft-stop gating before hard kill-switch).
5. Correlation gate: no new position if projected pairwise correlation to open book exceeds 0.8 and same direction risk increases.

---

## 5) Exit Rules

Each position is exited on first trigger:

1. **Stop loss:**
   - \(\text{SL} = 1.2 \times \text{ATR}_{14}\)
2. **Take profit:**
   - \(\text{TP} = 1.8 \times \text{ATR}_{14}\)
3. **Time stop:**
   - Exit after 18 bars (~90 minutes on 5m bars) if TP/SL not hit.
4. **Signal reversal:**
   - Exit if \(\alpha_t\) flips sign.
5. **End-of-session flattening (equities):**
   - Force close by 15:15 IST.
6. **Portfolio hard stop:**
   - If realized + unrealized P&L <= -5.8% of start-of-day equity, flatten all and disable trading for day.

---

## 6) Position Sizing Model

Risk-per-trade budget (fractional volatility targeting):
\[
R^* = \min(0.0075,\ 0.06 / N_{max})
\]
For max concurrent positions \(N_{max}=6\), \(R^*=0.75\%\) of capital per trade.

Notional per trade:
\[
Q_t = \frac{C \cdot R^* \cdot (0.5 + c_t)}{\text{SL\_distance\_pct}_t}
\]
where \(C\) is current capital.

Bounds:
- Minimum ticket: ₹1,000
- Maximum per position: 25% of capital
- Total gross exposure cap: 140% of capital (allowing hedged long/short in synthetic contexts)

For ₹20,000 capital, typical initial notional per trade is ₹2,000–₹5,000 depending on volatility.

---

## 7) Risk Parameters

| Risk Dimension | Rule |
|---|---|
| Daily max drawdown | Hard kill at -5.8%; soft throttle starts at -4.5% |
| Per-trade risk | 0.75% of capital at entry |
| Max concurrent positions | 6 |
| Single-position cap | 25% capital |
| Sector cap (India equities) | 35% gross per sector |
| Asset-class cap | 60% India equities, 40% crypto (intraday dynamic) |
| Correlation cap | No add if corr > 0.80 and same sign beta |
| Slippage assumption | India 8–15 bps, crypto 5–20 bps by pair |

---

## 8) Backtesting Framework

### Data requirements
- 5-minute OHLCV with corporate action-adjusted equities.
- L2/L1 proxy slippage model (if no order book: quadratic impact proxy on ADV participation).

### Simulation standards
1. Walk-forward structure:
   - Train/optimize: 6 months
   - Test: next 1 month
   - Roll forward monthly
2. Include realistic frictions:
   - Brokerage, exchange fees, STT/turnover where applicable.
3. Intrabar execution model:
   - Entry/exit at next bar open + slippage.
4. Survivorship-bias free universe reconstruction.
5. Capacity checks via participation rate constraints (e.g., <=2% 5-minute bar volume per order).

### Metrics
- CAGR, Sharpe, Sortino, Calmar
- Hit rate and payoff ratio
- Tail risk: CVaR(95)
- Turnover and implementation shortfall
- Regime-conditional P&L attribution (trend vs range)

---

## 9) Benchmark Selection

Use a blended benchmark to reflect the hybrid allocation:

\[
B_t = 0.6 \cdot \text{NIFTY50\_TR}_t + 0.4 \cdot \text{BTCINR}_t
\]

Also maintain execution benchmark:
- **Intraday benchmark:** session VWAP slippage vs fills.

Rationale:
- Strategy allocates across both India and crypto sleeves.
- A single-index benchmark would misstate opportunity cost and beta-adjusted alpha.

---

## 10) Edge Decay Monitoring

Implement a production health dashboard with the following alerts:

1. **Rolling Information Ratio degradation**
   - Alert if 20-day IR < 0 for 2 consecutive windows.
2. **Population Stability Index (PSI) on features**
   - Alert if PSI > 0.25 for RVOL, z-score, ATR buckets.
3. **Hit-rate break test**
   - Binomial test vs backtest baseline; alert at p < 0.05.
4. **Execution drift**
   - Live slippage exceeds modeled slippage by >40% for 10 sessions.
5. **Regime mismatch**
   - If one regime contributes <10% of expected alpha for 1 month, lower its allocation or retrain thresholds.

---

## 11) Pseudocode

```text
for each bar t for each symbol s:
    update indicators: EMA12, EMA26, VWAP, RVOL, ATR14, zscore
    compute trend_score TS
    if TS > 1.2:
        alpha = trend_signal_based_on_price_vs_vwap_and_rvol
    else:
        alpha = mean_reversion_signal_based_on_zscore

    if no position and alpha != 0 and risk_gates_pass:
        compute stop_distance = 1.2 * ATR14
        compute confidence c
        compute quantity using risk budget and confidence
        place order next bar open

    if position exists:
        if stop_hit or take_profit_hit or time_stop or alpha flips:
            close position

if day_pnl <= -5.8%:
    flatten_all
    disable_new_entries
```

---

## 12) Reference Implementation
See: `src/quant/intraday_india_crypto_strategy.py`

This implementation includes:
- Signal calculation
- Intraday backtest engine with fees/slippage
- Position sizing and risk kill-switch
- Performance summary for quick validation
