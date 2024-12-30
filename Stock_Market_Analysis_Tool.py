#<Dimitri Montgomery>


import numpy as np
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt



def companyStockChange(top_10_companies):
    for i in top_10_companies:
        askCompany = str(input(f"Enter 'yes' if you would like to see the stock data from company: {i}"))
        if askCompany == "Yes" or askCompany == "yes" or askCompany == "y" or askCompany == "Y":
            stock_data = yf.download(i, start = "2020-01-01", end = "2024-06-30")
            stock_data.fillna(value = True)
    
            stock_data['Daily Return'] = stock_data['Close'].pct_change()
            stock_data['50-Day MA'] = stock_data['Close'].rolling(window = 50).mean()
            stock_data['200-Day MA'] = stock_data['Close'].rolling(window = 200).mean()
            stock_data['Volatility'] = stock_data['Close'].rolling(window = 20).std()
    
            #print(stock_data.columns)
    
            avg_daily_return = stock_data['Daily Return'].mean()
            std_daily_return = stock_data['Daily Return'].std()
            print(f"Average Daily Return: {avg_daily_return:.5f}")
            print(f"Standard Deviation of Daily Returns: {std_daily_return:.5f}")
    
    
            latest_50_day_ma = stock_data['50-Day MA'].iloc[-1]
            latest_200_day_ma = stock_data['200-Day MA'].iloc[-1]
            print(f"Latest 50-Day MA: {latest_50_day_ma:.2f}")
            print(f"Latest 200-Day MA: {latest_200_day_ma:.2f}")
    
            avg_volatility = stock_data['Volatility'].mean()
            print(f"Average Volatility: {avg_volatility:.5f}")
    

            stock_data['Cumulative Return'] = (1 + stock_data['Daily Return']).cumprod()
            print(stock_data[['Cumulative Return']].tail())
    

            plt.figure(figsize = (10, 6))
            plt.title('Stock Change in Past 5 years')
            plt.xlabel(f"{i}")
            plt.ylabel('Stock Change')

            plt.plot(stock_data)
            plt.show();
        else:
            continue




def percentChange(top_10_companies, adj_close):
    total_change = ((adj_close.iloc[-1] - adj_close.iloc[0]) / adj_close.iloc[0]) * 100

    #Plot bar
    plt.figure(figsize = (10, 6))
    bars = total_change.sort_values().plot(kind = 'bar', color = 'red')
    plt.title('Total Percentage Change in Past 5 years')
    plt.xlabel('Company')
    plt.ylabel('Total Percentage Change')

    #Annotate
    for bar in bars.patches:
        bars.annotate(f'{bar.get_height():.2f}%',
                  ( bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha='center', va='bottom')

    plt.show()






def cumlReturns(top_10_companies, cumulative_returns):
    #Plot the cumulative returns
    plt.figure(figsize=(14, 8))
    for company in top_10_companies:
        plt.plot(cumulative_returns[company], label = company)

    #Annotate
    for company in top_10_companies:
        y = cumulative_returns[company].iloc[-1]
        plt.annotate(f'{y*100:.2f}%',
                    xy = (cumulative_returns.index[-1], y),
                    xytext = (10, 0),
                    textcoords = 'offset points',
                    horizontalalignment = 'left', verticalalignment = 'center',
                    fontsize = 9, bbox = dict(facecolor = 'gray', edgecolor = 'blue', alpha = 0.7))


    plt.title('Cumulative Returns in the Past 5 years')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.legend()
    plt.show()





if __name__ == "__main__":
    top_10_companies = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'JNJ', 'JPM']

    #past 5 years price data
    data = yf.download(top_10_companies, period = '5y')

    #adjusted close prices
    adj_close = data['Close']

    cumulative_returns = (adj_close / adj_close.iloc[0]) - 1


    askStockChange = str(input(f"Enter 'yes' if you would like to see the stock data from the top 10 companies: "))
    if askStockChange == "Yes" or askStockChange == "yes" or askStockChange == "y" or askStockChange == "Y":
        companyStockChange(top_10_companies)
    else:
        print("Next Stat")
        



    askPercentChange = str(input(f"Enter 'yes' if you would like to see the percent change for the top 10 companies: "))
    if askPercentChange == "Yes" or askPercentChange == "yes" or askPercentChange == "y" or askPercentChange == "Y":
        percentChange(top_10_companies, adj_close)
    else:
        print("Next Stat")
        



    askCumlReturns = str(input(f"Enter 'yes' if you would like to see the cumulative returns from the top 10 companies: "))
    if askCumlReturns == "Yes" or askCumlReturns == "yes" or askCumlReturns == "y" or askCumlReturns == "Y":
        cumlReturns(top_10_companies, cumulative_returns)
        print("All stats viewed")
    else:
        print("All stats viewed")


#work on easier way of going through the charts




