
import praw
import re
import pandas as pd
import config
def get_tickers():
    reddit = praw.Reddit(
        client_id= config.api_id,
        client_secret= config.api_secret,
        user_agent="WSB Scraping",
    )
    to_buy = []
    to_sell = []
    prev = open("prev.txt", "w+")
    prev_tickers = prev.readlines()
    prev_tickers = [x.strip() for x in prev_tickers]
    weekly_tickers = {}
    regex_pattern = r'\b([A-Z]+)\b'
    phrases = {}
    ticker_dict = {}
    filelist = ["list1.csv", "list2.csv", "list3.csv"]
    for file in filelist:
        tl = pd.read_csv(file, skiprows=0, skip_blank_lines=True)
        tl = tl[tl.columns[0]].tolist()
        for ticker in tl:
            ticker_dict[ticker] = 1
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
    for new in top_tickers:
        if new not in prev_tickers:
            to_buy.append(new+'\n')
    for old in prev_tickers:
        if old not in top_tickers:
            to_sell.append(old+'\n')

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
