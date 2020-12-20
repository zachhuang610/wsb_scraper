# wsb_scraper
scrapes WSB for top 5 stocks each week. Keeps track of previous week's top 5. If a stock stays in the top 5, we hold, If it leaves the top 5, we sell. If a stock enters the top 5, we buy. 


Files:

list1.csv, list2.csv, list3.csv: CSV files for list of tickers

prev: previous week's top 5 stocks

main: central python script