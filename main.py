import praw
import re
import pandas as pd
import config


def get_stock_list():
    ticker_dict = {}
    filelist = ["list1.csv", "list2.csv", "list3.csv"]
    for file in filelist:
        tl = pd.read_csv(file, skiprows=0, skip_blank_lines=True)
        tl = tl[tl.columns[0]].tolist()
        for ticker in tl:
            ticker_dict[ticker] = 1
    return ticker_dict


def get_prev_tickers():
    prev = open("prev.txt", "w+")
    prev_tickers = prev.readlines()
    prev_tickers = [x.strip() for x in prev_tickers]
    return prev, prev_tickers


def get_tickers():
    reddit = praw.Reddit(
        client_id=config.api_id,
        client_secret=config.api_secret,
        user_agent="WSB Scraping",
    )
    prev, prev_tickers = get_prev_tickers()
    weekly_tickers = {}

    regex_pattern = r'\b([A-Z]+)\b'
    ticker_dict = get_stock_list()
    blacklist = ["A", "I", "DD", "WSB", "YOLO", "RH"]
    for submission in reddit.subreddit("wallstreetbets").top("week"):
        strings = [submission.title]
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            strings.append(comment.body)
        for s in strings:
            for phrase in re.findall(regex_pattern, s):
                if phrase not in blacklist:
                    if ticker_dict.get(phrase) == 1:
                        if weekly_tickers.get(phrase) is None:
                            weekly_tickers[phrase] = 1
                        else:
                            weekly_tickers[phrase] += 1
    top_tickers = sorted(weekly_tickers, key=weekly_tickers.get, reverse=True)[:5]
    top_tickers = [ticker + '\n' for ticker in top_tickers]

    to_buy = []
    to_sell = []
    for new in top_tickers:
        if new not in prev_tickers:
            to_buy.append(new)
    for old in prev_tickers:
        if old not in top_tickers:
            to_sell.append(old)

    prev.writelines(top_tickers)
    prev.close()
    return to_buy, to_sell


def main():
    to_buy, to_sell = get_tickers()
    buy = open("toBuy.txt", "w")
    sell = open("toSell.txt", "w")
    buy.writelines(to_buy)
    sell.writelines(to_sell)
    buy.close()
    sell.close()


if __name__ == '__main__':
    main()
