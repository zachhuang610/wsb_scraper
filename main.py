import praw
import re
import pandas as pd
import config
import discord
import time
import robin_stocks
from rich.traceback import install
import pyotp
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


def get_tickers(sub, stockList):
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
    return weeklyTickers


def write_to_file(file, toBuy, toSell):
    f = open(file, "w")
    f.write("BUY:\n")
    toBuy = [buy + '\n' for buy in toBuy]
    f.writelines(toBuy)
    f.write("\nSELL:\n")
    toSell = [sell + '\n' for sell in toSell]
    f.writelines(toSell)
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
    totp = pyotp.TOTP(config.robin_totp).now()
    print("Current OTP: ", totp)
    login = robin_stocks.login(config.robin_user, config.robin_pwd, mfa_code=totp)

    holdings = robin_stocks.get_open_stock_positions()
    print(buy)
    print(sell)
    for stock in sell:
        stock = stock.strip()
        if stock in holdings:
            quantity = holdings[stock]["quantity"]
            robin_stocks.order_sell_fractional_by_quantity(stock, quantity, 'gfd')

    acc = robin_stocks.load_account_profile()
    print(acc)
    bp = acc["portfolio_cash"]
    print(bp)
    bp = float(bp)
    if bp > 0:
        bpps = bp/len(buy)
        print(bpps)
        for stock in buy:
            order = robin_stocks.order_buy_fractional_by_price(stock, bpps, 'gfd')
            print(order)
    else:
        print("not enough buying power")
    robin_stocks.logout()


def main():
    prevTickers = get_prev_tickers()
    subs = ["wallstreetbets", "stocks", "investing", "smallstreetbets"]
    stockList = get_stock_list()
    topTickers = {}
    for sub in subs:
        weeklyTickers = get_tickers(sub, stockList)
        for ticker in weeklyTickers.keys():
            if ticker in topTickers:
                topTickers[ticker] += weeklyTickers[ticker]
            else:
                topTickers[ticker] = weeklyTickers[ticker]

    top5 = sorted(topTickers, key=topTickers.get, reverse=True)[:5]
    toBuy = []
    toSell = []
    for top in top5:
        if top not in prevTickers:
            toBuy.append(top)
    for prev in prevTickers:
        prev = prev.strip()
        if prev not in top5:
            toSell.append(prev)

    write_to_file("output/actions.txt", toBuy, toSell)
    robinbot(toBuy, toSell)
    prev = open("output/prev.txt", "w")
    toBuy = [buy+'\n' for buy in toBuy]
    prev.writelines(toBuy)
    prev.close()
    discordbot(stf(["actions"]))


if __name__ == '__main__':
    main()
