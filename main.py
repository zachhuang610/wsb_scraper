import praw
import re
import pandas as pd
import config
import discord
import time
import robin_stocks
from rich.traceback import install
install()


def get_stock_list():
    ticker_dict = {}
    filelist = ["input/list1.csv", "input/list2.csv", "input/list3.csv"]
    for file in filelist:
        tl = pd.read_csv(file, skiprows=0, skip_blank_lines=True)
        tl = tl[tl.columns[0]].tolist()
        for ticker in tl:
            ticker_dict[ticker] = 1
    return ticker_dict


def get_prev_tickers():
    prev = open("output/prev.txt", "r")
    prevTickers = prev.readlines()
    prev.close()
    return prevTickers


def get_tickers(sub, stockList, prevTickers):
    reddit = praw.Reddit(
        client_id=config.reddit_id,
        client_secret=config.reddit_secret,
        user_agent="WSB Scraping",
    )
    weeklyTickers = {}

    regexPattern = r'\b([A-Z]+)\b'
    tickerDict = stockList
    blacklist = ["A", "I", "DD", "WSB", "YOLO", "RH", "EV", "PE", "ETH", "BTC", "E"]
    for submission in reddit.subreddit(sub).top("week"):
        strings = [submission.title]
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            strings.append(comment.body)
        for s in strings:
            for phrase in re.findall(regexPattern, s):
                if phrase not in blacklist:
                    if phrase in tickerDict:
                        if phrase not in weeklyTickers:
                            weeklyTickers[phrase] = 1
                        else:
                            weeklyTickers[phrase] += 1
    topTickers = sorted(weeklyTickers, key=weeklyTickers.get, reverse=True)[:5]
    topTickers = [ticker + '\n' for ticker in topTickers]

    toBuy = []
    toSell = []
    for new in topTickers:
        if new not in prevTickers:
            toBuy.append(new)
    for old in prevTickers:
        if old not in topTickers:
            toSell.append(old)

    write_to_file('output/'+sub+'.txt', toBuy, toSell)
    return toBuy, toSell


def write_to_file(file, toBuy, toSell):
    f = open(file, "w")
    f.write("BUY:\n")
    f.writelines(toBuy)
    f.write("\nSELL:\n")
    to_sell = [ticker+'\n' for ticker in toSell]
    f.writelines(to_sell)
    f.close()


def stf(subs):
    files = []
    for sub in subs:
        fp = 'output/'+sub+'.txt'
        file = discord.File(fp=fp, filename=fp, spoiler=False)
        files.append(file)
    return files


def discordbot(files):
    client = discord.Client()

    @client.event
    async def on_ready():
        channel = client.get_channel(config.channel_id)
        await channel.send(files=files)
        await client.close()
        time.sleep(1)

    client.run(config.discord_token)


def robinbot(buy, sell):
    login = robin_stocks.login(config.robin_user, config.robin_pwd)

    holdings = robin_stocks.build_holdings()
    for stock in sell:
        if stock in holdings:
            quantity = holdings[stock]["quantity"]
            robin_stocks.order_sell_fractional_by_quantity(stock, quantity, 'gtc')

    bp = robin_stocks.load_account_profile(info="buying_power")
    if bp > 0:
        bpps = bp/len(buy)
        for stock in buy:
            robin_stocks.order_buy_fractional_by_price(stock, bpps, 'gtc')
    else:
        print("not enough buying power")
    robin_stocks.logout()


def main():
    prevTickers = get_prev_tickers()
    subs = ["wallstreetbets", "stocks", "investing", "smallstreetbets"]
    stockList = get_stock_list()
    buyPos = []
    sellPos = []
    for sub in subs:
        toBuy, toSell = get_tickers(sub, stockList, prevTickers)
        for stock in toBuy:
            if stock not in buyPos:
                buyPos.append(stock)
        for stock in toSell:
            if stock not in sellPos:
                sellPos.append(stock)

    robinbot(buyPos, sellPos)
    prev = open("output/prev.txt", "w")
    prev.writelines(buyPos)
    prev.close()
    files = stf(subs)
    discordbot(files)


if __name__ == '__main__':
    main()
