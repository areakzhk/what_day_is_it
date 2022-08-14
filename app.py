import os
import re
import requests
from datetime import datetime, timezone, timedelta
from cs50 import SQL
from flask import Flask, redirect, render_template, request

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///days.db")

# Make sure API key is set
if not os.environ.get("BEARER_TOKEN"):
    raise RuntimeError("API_KEY not set")

# Using twitter API, search for what is today (Reference: https://github.com/twitterdev/Twitter-API-v2-sample-code/blob/main/Recent-Search/recent_search.py)
# To set your environment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ.get("BEARER_TOKEN")
search_url = "https://api.twitter.com/2/tweets/search/recent"

# Twitter API bearer token authentication
def bearer_oauth(r):
    """ Bearer token authentication """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r

# Use Twitter Search API to get what today possibly is, return standard JSON response of search API
def get_today_json(url):
    # Define today (GMT+9 Japan Standard Time), get today
    jst = timezone(timedelta(hours=9), 'jst')
    today = datetime.now(jst)
    today_month = today.month
    today_day = today.day
    # Twitter search API query parameters
    query_params = {'query': f'{today_month}月{today_day}日は の日 OR ({today_month}月{today_day}日は デイ)', 'max_results': 50}
    response = requests.get(url, auth=bearer_oauth, params=query_params)
    # Ensure Twitter API HTTP response code is 200
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()

# Take in the output of get_today_json, return a list of "day"s that today can possibly be
def get_today_list(response_json):
    # Initiate a list to store possibilities of what is today
    day_list = list()
    # Iterate through each recent tweet, search for "what day is it" using Regex
    for i in range(len(response_json["data"])):
        x = re.search(r'日は?[#、,，[{(”（）｛「【『〔［〈≪《\s][^\n]*(の日|デイ)', response_json["data"][i]["text"])
        # If above regex matches any part of the tweet, add the matched part to the day_list
        if x is not None:
            y = re.search("日は", x.group(0))
            if y is None:
                continue
            startpos = y.end()
            z = re.search("の日", x.group(0))
            endpos = z.end()
            day_name = x.group(0)[startpos+1:endpos]
            # Prevent " from entering the day_name list, which will make the tweet count API to fail
            if "\"" in day_name or "\'" in day_name or "’" in day_name or "”" in day_name or "＃" in day_name:
                continue
            if day_name not in day_list:
                day_list.append(day_name)
    return day_list

# Take in a list of possible "day"s, return a dictionary storing tweet count of each "day" as values
# Data obtained via Twitter tweet count API
def get_each_day_tweet_count(day_list):
    count_url = "https://api.twitter.com/2/tweets/counts/recent"
    tweet_count_dict = dict()
    # Define today (GMT+9 Japan Standard Time), get today
    jst = timezone(timedelta(hours=9), 'jst')
    today = datetime.now(jst)
    today_month = today.month
    today_day = today.day

    for i in range(len(day_list)):
        # Twitter tweet count API query parameters
        query_params = {'query': f'{today_month}月{today_day}日は {day_list[i]}', 'granularity': 'day'}
        response = requests.get(count_url, auth=bearer_oauth, params=query_params)
        # Ensure Twitter tweet count API HTTP response code is 200
        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
        tweet_count_json = response.json()
        tweet_count_dict[day_list[i]] = tweet_count_json["meta"]["total_tweet_count"]
    return tweet_count_dict

@app.route("/", methods=["GET","POST"])
def index():
    """ Let user poll what day is it, with POST request. If with GET request, show what day is it """
    if request.method == "POST":
        user_input = request.form.get("user_day")
        # Ensure user_input is not empty
        if not user_input:
            return render_template("invalidinput.html")
        # Define today (GMT+9 Japan Standard Time), get today
        jst = timezone(timedelta(hours=9), 'jst')
        today = datetime.now(jst)
        today_month = today.month
        today_day = today.day
        # Look up days.db to see if the claimed "day" already an entry
        day_lookup = db.execute("SELECT * FROM daysinyear WHERE month = ? AND day = ? AND dayName = ?", today_month, today_day, user_input)
        # If not, create new entry, set count to 1
        if len(day_lookup) == 0:
            db.execute("INSERT INTO daysinyear (month, day, dayName, count) VALUES (?, ?, ?, 1)", today_month, today_day, user_input)
        # If yes, update count
        else:
            db.execute("UPDATE daysinyear SET count = count + 1 WHERE month = ? AND day = ? AND dayName = ?", today_month, today_day, user_input)
        return redirect("/")

    else:
        # Define today (GMT+9 Japan Standard Time), get today
        jst = timezone(timedelta(hours=9), 'jst')
        today = datetime.now(jst)
        today_month = today.month
        today_day = today.day
        # Show what today is, using the data obtained from Twitter search API and count API
        today_json = get_today_json(search_url)
        todaylist = get_today_list(today_json)
        todaydict = get_each_day_tweet_count(todaylist)
        # Sort todaydict to today_dict
        today_list = list()
        today_dict = {k: v for k, v in sorted(todaydict.items(), key=lambda item: item[1], reverse=True)}
        # Prepare Twitter API results for passing into index.html
        for k in today_dict:
            today_list.append(k)
        count_list = list()
        numberofitems = len(today_list)
        for i in range(numberofitems):
            count_list.append(today_dict[today_list[i]])

        # Prepare user_day_ranking for passing into index.html
        user_day_item_count = 0
        user_day_item_list = list()
        user_day_vote_count = list()
        user_day_dict = db.execute("SELECT * FROM daysinyear WHERE month = ? AND day = ? ORDER BY count desc LIMIT 3", today_month, today_day)
        # Skip if no entry
        if not user_day_dict:
            return render_template("index.html", numberofitems=numberofitems, item_list=today_list, count_list=count_list, user_day_item_count=0, user_day_item_list=[], user_day_vote_count=[])
        for i in range(len(user_day_dict)):
            user_day_item_list.append(user_day_dict[i]["dayName"])
            user_day_vote_count.append(user_day_dict[i]["count"])
        user_day_item_count = len(user_day_item_list)

        return render_template("index.html", numberofitems=numberofitems, item_list=today_list, count_list=count_list, user_day_item_count=user_day_item_count, user_day_item_list=user_day_item_list, user_day_vote_count=user_day_vote_count)

@app.route("/database", methods=["GET", "POST"])
def database():
    """ Allow user to browse through each day of a year, get what is that day """
    # Request method == POST
    if request.method == "POST":
        user_month = request.form.get("usermonth")
        user_day = request.form.get("userday")

        # Ensure user inputs are not empty
        if not user_month or not user_day:
            return render_template("invalidinput.html")
        usermonth = int(user_month)
        userday = int(user_day)
        # Ensure user input is valid
        if usermonth < 1 or usermonth > 12 or userday < 1 or userday > 31:
            return render_template("invalidinput.html")
        if (usermonth == 2 and userday > 29) or (usermonth == 4 and userday > 30) or (usermonth == 6 and userday > 30) or (usermonth == 9 and userday > 30) or (usermonth == 11 and userday > 30):
            return render_template("invalidinput.html")

        # Prepare user_day_ranking for passing into database.html
        user_day_item_count = 0
        user_day_item_list = list()
        user_day_vote_count = list()
        user_day_dict = db.execute("SELECT * FROM daysinyear WHERE month = ? AND day = ? ORDER BY count desc LIMIT 3", usermonth, userday)
        # Skip if no entry
        if not user_day_dict:
            return render_template("database.html", month=usermonth, day=userday, user_day_item_count=0, user_day_item_list=[], user_day_vote_count=[])
        for i in range(len(user_day_dict)):
            user_day_item_list.append(user_day_dict[i]["dayName"])
            user_day_vote_count.append(user_day_dict[i]["count"])
        user_day_item_count = len(user_day_item_list)
        return render_template("database.html", month=usermonth, day=userday, user_day_item_count=user_day_item_count, user_day_item_list=user_day_item_list, user_day_vote_count=user_day_vote_count)

    # Request method == GET
    else:
        # Define today (GMT+9 Japan Standard Time), get today
        jst = timezone(timedelta(hours=9), 'jst')
        today = datetime.now(jst)
        today_month = today.month
        today_day = today.day

        # Prepare user_day_ranking for passing into database.html
        user_day_item_count = 0
        user_day_item_list = list()
        user_day_vote_count = list()
        user_day_dict = db.execute("SELECT * FROM daysinyear WHERE month = ? AND day = ? ORDER BY count desc LIMIT 3", today_month, today_day)
        # Skip if no entry
        if not user_day_dict:
            return render_template("database.html", month=today_month, day=today_day, user_day_item_count=0, user_day_item_list=[], user_day_vote_count=[])
        for i in range(len(user_day_dict)):
            user_day_item_list.append(user_day_dict[i]["dayName"])
            user_day_vote_count.append(user_day_dict[i]["count"])
        user_day_item_count = len(user_day_item_list)
        return render_template("database.html", month=today_month, day=today_day, user_day_item_count=user_day_item_count, user_day_item_list=user_day_item_list, user_day_vote_count=user_day_vote_count)

@app.route("/poll", methods=["GET", "POST"])
def poll():
    """ Allow user to poll any specific day is what kind of "day" """
    # Request method == POST
    if request.method == "POST":
        user_month = request.form.get("usermonth")
        user_day = request.form.get("userday")
        dayname = request.form.get("dayname")

        # Ensure user inputs are not empty
        if not user_month or not user_day or not dayname:
            return render_template("invalidinput.html")
        usermonth = int(user_month)
        userday = int(user_day)

        # Ensure user input is valid
        if usermonth < 1 or usermonth > 12 or userday < 1 or userday > 31:
            return render_template("invalidinput.html")
        if (usermonth == 2 and userday > 29) or (usermonth == 4 and userday > 30) or (usermonth == 6 and userday > 30) or (usermonth == 9 and userday > 30) or (usermonth == 11 and userday > 30):
            return render_template("invalidinput.html")

        # Check if userday already exist
        record = db.execute("SELECT * FROM daysinyear WHERE month = ? AND day = ? AND dayName = ?", usermonth, userday, dayname)
        if len(record) != 0:
            db.execute("UPDATE daysinyear SET count = count + 1 WHERE month = ? AND day = ? AND dayName = ?", usermonth, userday, dayname)
        else:
            db.execute("INSERT INTO daysinyear (month, day, dayName, count) VALUES (?, ?, ?, 1)", usermonth, userday, dayname)

        # Prepare user_day_ranking for passing into database.html
        user_day_item_count = 0
        user_day_item_list = list()
        user_day_vote_count = list()
        user_day_dict = db.execute("SELECT * FROM daysinyear WHERE month = ? AND day = ? ORDER BY count desc LIMIT 3", usermonth, userday)
                # Skip if no entry
        if len(user_day_dict) == 0:
            return render_template("database.html", month=usermonth, day=userday, user_day_item_count=0, user_day_item_list=[], user_day_vote_count=[])
        for i in range(len(user_day_dict)):
            user_day_item_list.append(user_day_dict[i]["dayName"])
            user_day_vote_count.append(user_day_dict[i]["count"])
        user_day_item_count = len(user_day_item_list)
        return render_template("database.html", month=usermonth, day=userday, user_day_item_count=user_day_item_count, user_day_item_list=user_day_item_list, user_day_vote_count=user_day_vote_count)

    # Request method == GET
    else:
        return render_template("poll.html")