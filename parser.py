from datetime import date, timedelta
import pandas as pd
import requests
import numpy as np

API_URL = "http://iss.moex.com"
HISTORY_URL = API_URL + "/iss/history/engines/stock/markets/shares/securities"

TODAY = date.today()
YESTERDAY = date.today() - timedelta(days=1)

tickers = ['YNDX', 'VKCO', 'TCSG', 'POLY', 'OZON', 'OKEY', 'MDMG', 'QIWI', 'SFTL', 'HHRU', 'POSI', 'WUSH', 'GLTR',
           'GEMC', 'FIXP', 'FIVE', 'ETLN', 'CIAN', 'AGRO', 'UPRO', 'SFIN', 'ENPG', 'ENRU', 'PHOR', 'TRNFP', 'TGKA',
           'TATNP', 'TATH', 'FLOT', 'AFKS', 'SELG', 'SGZH', 'CHMF', 'SBERP', 'SBER', 'SMLT', 'RNFT', 'HYDR', 'RUAL',
           'RTKMP', 'RTKM', 'FEES', 'ROSN', 'RENI', 'PLZL', 'PIKK', 'NVTK', 'NLMK', 'MTSS', 'MOEX', 'MAGN', 'CBOM',
           'MTLRP', 'MTLR', 'MGNT', 'MVID', 'LKOH', 'LSRG', 'LENT', 'IRAO', 'DSKY', 'GMKN', 'GAZP', 'VTBR',
           'BELU', 'AFLT', 'ALRS', 'MSNG']
tickers.sort()


def get_html_tables(url):
    return pd.read_html(requests.get(url).text)


def get_ticker_data(ticker):
    ticker_url = f"{HISTORY_URL}/{ticker}.html"
    total_rows = get_html_tables(ticker_url)[1]["TOTAL (int64)"][0]

    dfs = []
    i = total_rows - 100
    while True:
        df = get_html_tables(f"{ticker_url}?start={i}")[0]
        dfs.append(df)
        i -= 100

        min_date = date.fromisoformat(df.head(1)["TRADEDATE (date:10)"][0])
        if date.today().year - min_date.year > 1:
            break

    df = pd.concat(dfs, ignore_index=True)
    df.rename(columns=lambda it: it.split()[0].lower(), inplace=True)
    df.rename(columns={"tradedate": "date"}, inplace=True)
    df = df[df.boardid.map(lambda it: "QBR" in it)]
    df.drop(
        columns=df.columns.difference(["date", "close"]),
        inplace=True,
    )
    df.close = df.close.astype(np.float64)
    df.date = pd.to_datetime(df.date)
    df.set_index("date", inplace=True)
    df.sort_index(inplace=True)

    df = df.reindex(pd.date_range(date(TODAY.year - 1, 1, 1), YESTERDAY))
    df = df.resample('D').mean().interpolate(limit_direction="both")

    return df


df = None
for ticker in tickers:
    try:
        next_df = get_ticker_data(ticker)
    except ValueError:
        continue
    next_df.rename(columns={"close": ticker}, inplace=True)
    if df is None:
        df = next_df
    else:
        df = pd.concat([df, next_df], axis=1)

df.to_sql(
    "quotes",
    "postgresql://postgres:infin@postgres/postgres",
    if_exists="replace",
)
