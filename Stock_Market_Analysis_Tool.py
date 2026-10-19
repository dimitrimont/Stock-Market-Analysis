# <Dimitri Montgomery>
"""Stock market analysis for a set of companies, from the command line.

    python Stock_Market_Analysis_Tool.py                      # summary table, 10 companies, last 5 years
    python Stock_Market_Analysis_Tool.py --chart NVDA AAPL    # price, averages and volume for each
    python Stock_Market_Analysis_Tool.py --compare            # total change and growth, all companies
    python Stock_Market_Analysis_Tool.py --start 2020-01-01 --end 2024-06-30 --save charts/

Every figure and number covers the same stated period. The first version asked yes or no once per
company; tickers, dates and charts are now options.
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

import stock_analysis as sa


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--tickers", nargs="+", default=sa.TOP_10, help="default: the ten companies below")
    today = date.today()
    p.add_argument("--start", default=str(today - timedelta(days=round(5 * 365.25))), help="YYYY-MM-DD, default five years ago")
    p.add_argument("--end", default=str(today), help="YYYY-MM-DD, default today")
    p.add_argument("--chart", nargs="*", metavar="TICKER", help="price, moving averages and volume for these tickers")
    p.add_argument("--compare", action="store_true", help="total change and cumulative growth for every ticker")
    p.add_argument("--save", metavar="DIR", help="save charts as PNG files here instead of opening windows")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    tickers = [t.upper() for t in args.tickers]
    chart = [t.upper() for t in (args.chart or [])]
    try:
        prices = sa.download(sorted(set(tickers + chart), key=(tickers + chart).index), args.start, args.end)
    except sa.DownloadError as e:
        sys.exit(f"error: {e}")

    print(f"{len(prices.close.columns)} companies, {sa.period_label(prices)} ({len(prices.close)} trading days)\n")
    table = sa.summary(prices.close[tickers])
    fmt = {c: "{:+.1%}".format for c in ["total return", "annualised return"]}
    fmt.update({"annualised volatility": "{:.1%}".format, "average daily return": "{:+.3%}".format,
                "std of daily returns": "{:.2%}".format})
    fmt.update({c: "{:,.2f}".format for c in ["latest close", "latest 50-day MA", "latest 200-day MA"]})
    print(table.to_string(formatters=fmt))

    figures = [(f"{t}_chart", sa.plot_company(prices, t)) for t in chart]
    if args.compare:
        figures += [("total_change", sa.plot_total_change(prices)), ("cumulative_returns", sa.plot_cumulative(prices))]
    if not figures:
        return
    import matplotlib.pyplot as plt

    if args.save:
        out = Path(args.save)
        out.mkdir(parents=True, exist_ok=True)
        for name, fig in figures:
            fig.savefig(out / f"{name}.png", dpi=120)
            print(f"saved {out / (name + '.png')}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
