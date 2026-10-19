import numpy as np
import pandas as pd
import pytest

import stock_analysis as sa

DAYS = pd.bdate_range("2023-01-02", periods=300)


def series(values, name="X"):
    return pd.Series(values, index=DAYS[: len(values)], name=name, dtype=float)


def zigzag(start, step, n=300):
    """A price that moves up and down by `step` (a fraction) on alternate days."""
    out = [start]
    for i in range(1, n):
        out.append(out[-1] * (1 + step if i % 2 else 1 - step))
    return series(out)


def test_daily_and_cumulative_returns():
    c = series([100, 110, 99])
    assert sa.daily_returns(c).round(10).tolist() == [0.1, -0.1]
    assert sa.cumulative_return(c).round(10).tolist() == [0.0, 0.1, -0.01]


def test_annualised_volatility_of_a_known_series():
    r = pd.Series([0.01, -0.01] * 126)  # 252 days of +1% and -1%
    # sample std of +-0.01 over n values is 0.01 * sqrt(n / (n - 1)); a year is sqrt(252) days
    assert sa.annualised_volatility(r) == pytest.approx(0.01 * np.sqrt(252 / 251) * np.sqrt(252))


def test_volatility_does_not_depend_on_the_share_price():
    cheap, dear = zigzag(40, 0.03), zigzag(400, 0.01)
    assert sa.annualised_volatility(sa.daily_returns(cheap)) > sa.annualised_volatility(sa.daily_returns(dear))
    # The first version's measure, a 20-day rolling std of the price in dollars, says the opposite.
    first = lambda c: c.rolling(20).std().mean()  # noqa: E731
    assert first(dear) > first(cheap)


def test_moving_average_of_a_straight_line_is_its_midpoint():
    c = series(np.arange(1, 301))
    ma = sa.moving_averages(c)
    assert ma["50-day MA"].iloc[-1] == pytest.approx(np.mean(np.arange(251, 301)))
    assert ma["200-day MA"].isna().sum() == 199


def test_annualised_return_doubles_in_a_year():
    idx = pd.to_datetime(["2023-01-01", "2024-01-01"])
    assert sa.annualised_return(pd.Series([50.0, 100.0], index=idx)) == pytest.approx(2 ** (365.25 / 365) - 1, rel=1e-3)


def test_summary_sorts_by_volatility():
    close = pd.DataFrame({"CHEAP": zigzag(40, 0.03), "DEAR": zigzag(400, 0.01)})
    table = sa.summary(close)
    assert list(table.index) == ["CHEAP", "DEAR"]


def prices():
    close = pd.DataFrame({"A": zigzag(100, 0.02), "B": zigzag(50, 0.01)})
    volume = pd.DataFrame({"A": np.full(300, 5e8), "B": np.full(300, 2e7)}, index=close.index)
    return sa.Prices(close=close, volume=volume, start=close.index[0], end=close.index[-1])


def test_company_chart_keeps_volume_off_the_price_axis():
    fig = sa.plot_company(prices(), "A")
    price_ax, volume_ax = fig.axes
    assert price_ax.get_ylim()[1] < 1000  # the first version's one axis reached past 1e8
    assert volume_ax.get_ylabel() == "Volume (millions)"


def test_titles_name_the_period():
    p = prices()
    assert "02 Jan 2023" in sa.plot_total_change(p).axes[0].get_title()
    assert sa.period_label(p).startswith("02 Jan 2023 to ")


def test_spread_labels_keeps_order_and_gap():
    ys = sa.spread_labels([10.0, 10.5, 11.0, 50.0], min_gap=2)
    assert list(np.diff(ys[:3])) == [2, 2] and ys[3] == 50


def test_empty_download_is_a_clear_error(monkeypatch):
    import yfinance as yf

    monkeypatch.setattr(yf, "download", lambda *a, **k: pd.DataFrame())
    with pytest.raises(sa.DownloadError, match="No prices came back for AAPL"):
        sa.download(["AAPL"], "2020-01-01", "2020-02-01")


def test_a_ticker_with_no_prices_is_named(monkeypatch):
    import yfinance as yf

    cols = pd.MultiIndex.from_product([["Close", "Volume"], ["AAPL", "NOPE"]])
    raw = pd.DataFrame([[1.0, np.nan, 10, np.nan]] * 3, columns=cols, index=DAYS[:3])
    monkeypatch.setattr(yf, "download", lambda *a, **k: raw)
    with pytest.raises(sa.DownloadError, match="NOPE"):
        sa.download(["AAPL", "NOPE"], "2023-01-02", "2023-01-05")
