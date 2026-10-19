# Stock Market Analysis

Daily returns, volatility, moving averages and growth for a set of stocks, from Yahoo Finance via
`yfinance`, as a table and as charts. Written in December 2024 and revised in October 2026; the
original script is the tag `first-version`.

## Running it

```bash
pip install -r requirements.txt
python Stock_Market_Analysis_Tool.py                      # summary table, ten companies, last five years
python Stock_Market_Analysis_Tool.py --chart NVDA AAPL    # price, 50/200-day averages and volume
python Stock_Market_Analysis_Tool.py --compare            # total change and growth for every company
python Stock_Market_Analysis_Tool.py --tickers AAPL MSFT --start 2020-01-01 --end 2024-06-30 --save charts/
pytest                                                     # 11 tests on made-up prices, under a second
```

The default companies are Apple, Microsoft, Alphabet, Amazon, NVIDIA, Meta, Tesla, Berkshire
Hathaway, Johnson & Johnson and JPMorgan Chase. Prices are adjusted for splits and dividends.
Every table and chart covers the same period, and says which.

## What it reports

For each company: total and annualised return, **annualised volatility** (the standard deviation of
daily returns, times the square root of 252 trading days), the average and spread of daily returns,
and the latest close with its 50- and 200-day moving averages. The table is sorted from the most
volatile to the least.

For 2 January 2020 to 28 June 2024 (the first version's window):

| | Total return | Annualised return | Annualised volatility |
|---|---|---|---|
| TSLA | +589.9% | +53.8% | 66.6% |
| NVDA | +1968.1% | +96.4% | 54.1% |
| META | +140.9% | +21.6% | 46.3% |
| AMZN | +103.6% | +17.2% | 36.5% |
| JPM | +63.7% | +11.6% | 33.1% |
| GOOGL | +166.5% | +24.4% | 33.0% |
| AAPL | +188.7% | +26.6% | 32.7% |
| MSFT | +189.8% | +26.8% | 31.4% |
| BRK-B | +78.1% | +13.7% | 22.2% |
| JNJ | +13.3% | +2.8% | 20.1% |

## What changed from the first version

- **Volatility was measured in dollars.** "Average Volatility" was the 20-day rolling standard
  deviation of the share price, so it ranked stocks by how expensive their shares were. Over the
  period above it rated NVIDIA the least volatile of the ten (1.59) when its daily returns were the
  second most volatile (54% a year), and put Microsoft third and Berkshire fourth where they rank
  eighth and ninth. It is now measured on daily returns.
- **The company chart showed trading volume, not price.** It plotted every column on one axis, and
  volume, in the hundreds of millions, flattened the prices to a line at zero. The chart now has the
  price with its moving averages, and volume in a panel of its own.
- **Two periods, both called "the past 5 years".** The per-company figures covered a fixed
  2020-01-01 to 2024-06-30 (four and a half years), while the comparison charts covered the five years
  before the day the script was run. One period now covers everything, set by `--start` and `--end`.
- **A failed download crashed later, unexplained.** With no prices, the script stopped on
  `IndexError: single positional indexer is out-of-bounds`, which is what the December 2024 `yfinance`
  now gets from Yahoo. It now says which tickers came back empty.
- **Ten prompts per run.** It asked yes or no for each company in turn; tickers, dates and charts are
  now command-line options.
- Smaller: `fillna(value=True)` discarded its result (and would have filled gaps with 1.0); the ten
  end labels on the growth chart sat on top of each other and are now spread apart; dependencies are
  pinned to a `yfinance` that still downloads.

## Tests

`tests/` uses made-up prices with known answers: returns of 100, 110, 99; the annualised volatility of
alternating +1% and -1% days; a $40 stock moving 3% a day ranked more volatile than a $400 stock moving
1% (the first version's measure ranks them the other way round); a moving average of a straight line;
the company chart's price axis free of volume; titles naming the period; and a failed download raising
a clear error that names the ticker.
