"""Returns, volatility and moving averages for a set of stocks, and the charts that show them.

Everything here except `download` works on plain pandas data, so it can be tested on made-up prices.

Volatility is measured on daily returns, not on prices. The first version averaged a 20-day
rolling standard deviation of the price in dollars, which ranks stocks by how expensive their
shares are: over 2020-01-01 to 2024-06-30 it rated NVIDIA the least volatile of ten stocks, when
its daily returns were the second most volatile.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS = 252
TOP_10 = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "JNJ", "JPM"]


class DownloadError(RuntimeError):
    """Raised when some tickers came back with no prices, instead of crashing later on an empty table."""


@dataclass
class Prices:
    close: pd.DataFrame  # one column per ticker, adjusted for splits and dividends
    volume: pd.DataFrame
    start: pd.Timestamp
    end: pd.Timestamp


def download(tickers, start, end) -> Prices:
    """Daily prices from Yahoo Finance via yfinance, adjusted for splits and dividends."""
    import yfinance as yf

    raw = yf.download(list(tickers), start=start, end=end, auto_adjust=True, progress=False, group_by="column")
    if raw is None or raw.empty:
        raise DownloadError(f"No prices came back for {', '.join(tickers)} ({start} to {end}). "
                            "Check the connection, the tickers and the dates, and that yfinance is up to date.")
    close, volume = raw["Close"], raw["Volume"]
    if isinstance(close, pd.Series):  # older yfinance, one ticker
        close, volume = close.to_frame(tickers[0]), volume.to_frame(tickers[0])
    missing = [t for t in tickers if t not in close or close[t].dropna().empty]
    if missing:
        raise DownloadError(f"No prices came back for {', '.join(missing)} ({start} to {end}).")
    close = close[list(tickers)].dropna(how="all")
    return Prices(close=close, volume=volume[list(tickers)].loc[close.index], start=close.index[0], end=close.index[-1])


def daily_returns(close: pd.Series) -> pd.Series:
    """Day-on-day change, as a fraction: 100 then 110 is 0.10."""
    return close.pct_change().dropna()


def cumulative_return(close: pd.Series) -> pd.Series:
    """Growth since the first day, as a fraction: 0 on day one, 1.0 once the price has doubled."""
    close = close.dropna()
    return close / close.iloc[0] - 1


def annualised_volatility(returns: pd.Series) -> float:
    """Standard deviation of daily returns, scaled to a year of 252 trading days."""
    return float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS))


def rolling_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
    """The same, over a moving window of trading days."""
    return returns.rolling(window).std(ddof=1) * np.sqrt(TRADING_DAYS)


def moving_averages(close: pd.Series, windows=(50, 200)) -> pd.DataFrame:
    return pd.DataFrame({f"{w}-day MA": close.rolling(w).mean() for w in windows})


def annualised_return(close: pd.Series) -> float:
    """Compound growth per year over the whole period (CAGR), by calendar time."""
    close = close.dropna()
    years = (close.index[-1] - close.index[0]).days / 365.25
    return float((close.iloc[-1] / close.iloc[0]) ** (1 / years) - 1)


def summary(close: pd.DataFrame) -> pd.DataFrame:
    """One row per ticker, sorted from the most volatile to the least."""
    rows = {}
    for t in close.columns:
        c = close[t].dropna()
        r = daily_returns(c)
        ma = moving_averages(c)
        rows[t] = {
            "total return": c.iloc[-1] / c.iloc[0] - 1,
            "annualised return": annualised_return(c),
            "annualised volatility": annualised_volatility(r),
            "average daily return": r.mean(),
            "std of daily returns": r.std(ddof=1),
            "latest close": c.iloc[-1],
            "latest 50-day MA": ma["50-day MA"].iloc[-1],
            "latest 200-day MA": ma["200-day MA"].iloc[-1],
        }
    return pd.DataFrame(rows).T.sort_values("annualised volatility", ascending=False)


def period_label(prices: Prices) -> str:
    return f"{prices.start:%d %b %Y} to {prices.end:%d %b %Y}"


# ---------------------------------------------------------------- charts


def plot_company(prices: Prices, ticker: str):
    """Price with its 50- and 200-day averages on top, volume in its own panel below.

    The first version plotted every column on one axis; volume, in the hundreds of millions,
    flattened the prices to a line at zero.
    """
    import matplotlib.pyplot as plt

    c = prices.close[ticker].dropna()
    ma = moving_averages(c)
    fig, (ax, axv) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax.plot(c.index, c, lw=1.2, color="#1f4e79", label=f"{ticker} close")
    ax.plot(ma.index, ma["50-day MA"], lw=1.2, color="#e07b39", label="50-day average")
    ax.plot(ma.index, ma["200-day MA"], lw=1.2, color="#5a9e6f", label="200-day average")
    ax.set_ylabel("Price (USD, adjusted)")
    vol = annualised_volatility(daily_returns(c))
    ax.set_title(f"{ticker}, {period_label(prices)}: {c.iloc[-1] / c.iloc[0] - 1:+.0%}, volatility {vol:.0%} a year")
    ax.legend(loc="upper left")
    axv.bar(prices.volume.index, prices.volume[ticker] / 1e6, width=1.0, color="#9aa5b1")
    axv.set_ylabel("Volume (millions)")
    fig.tight_layout()
    return fig


def plot_total_change(prices: Prices):
    import matplotlib.pyplot as plt

    change = (prices.close.ffill().iloc[-1] / prices.close.bfill().iloc[0] - 1) * 100
    change = change.sort_values()
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(change.index, change.values, color=["#c0392b" if v < 0 else "#1f4e79" for v in change.values])
    for bar, v in zip(bars, change.values):
        ax.annotate(f"{v:.0f}%", (bar.get_x() + bar.get_width() / 2, v), ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=9)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title(f"Total change, {period_label(prices)}")
    ax.set_ylabel("Change (%)")
    fig.tight_layout()
    return fig


def spread_labels(ys, min_gap):
    """Nudge label positions apart so none sit closer than `min_gap`, keeping their order."""
    order = np.argsort(ys)
    out = np.array(ys, dtype=float)
    for i in range(1, len(order)):
        a, b = order[i - 1], order[i]
        if out[b] - out[a] < min_gap:
            out[b] = out[a] + min_gap
    return out


def plot_cumulative(prices: Prices):
    """Growth since the first day, every ticker, with end labels spread so they do not overlap."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(13, 7))
    ends = {}
    for t in prices.close.columns:
        cr = cumulative_return(prices.close[t]) * 100
        (line,) = ax.plot(cr.index, cr, lw=1.3, label=t)
        ends[t] = (cr.iloc[-1], line.get_color())
    lo, hi = ax.get_ylim()
    ys = spread_labels([v for v, _ in ends.values()], min_gap=(hi - lo) * 0.035)
    x = prices.close.index[-1]
    for (t, (v, colour)), y in zip(ends.items(), ys):
        ax.annotate(f"{t} {v:+.0f}%", xy=(x, v), xytext=(x + pd.Timedelta(days=20), y), fontsize=9, color=colour,
                    ha="left", va="center", annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=colour, lw=0.6))
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title(f"Growth since {prices.start:%d %b %Y}, to {prices.end:%d %b %Y}")
    ax.set_ylabel("Cumulative return (%)")
    fig.subplots_adjust(right=0.86)
    return fig
