#!/usr/bin/python

import datetime
import pytz
import json
from time import sleep
import praw
from pyquery import PyQuery
import requests
import schedule

teams_file = open('../data/teams.json').read()
teams_json = json.loads(teams_file)
teams = teams_json['teams']
SUBREDDIT = 'seemethere'
body_template=open('../data/templates/body.txt').read()
refresh_rate = 3 #in minutes
mins_before = 30 # Indicates in minutes how many minutes before game to post thread
running = True

def getCurrent():
    now = datetime.datetime.now(pytz.timezone('US/Eastern'))
    today = datetime.datetime(now.year, now.month, now.day, now.hour,now.minute, now.second, 0,
                                tzinfo=pytz.timezone('US/Eastern'))
    todays_date = str(today)[0:10]
    time = str(today)[11:19]
    date_obj = datetime.datetime.strptime(todays_date, '%Y-%m-%d')
    return date_obj, time

def getTodaysGames(date):
    scheduled_games = []
    for team in teams:
        schedule_file = open('../data/teams/{name}.json'.format(name = team['full_name'])).read()
        schedule_json = json.loads(schedule_file)
        games = schedule_json['schedule']
        for game in games:
            gamedate = game['datetime'][0:10]
            if gamedate == str(date)[0:10]:
                scheduled_games.append(game)
                #opponent = game['opponent']
                #print "{0}: {1} vs. {2}".format(gamedate,team['nickname'],opponent['nickname'])
    return scheduled_games

def compareTimes(games, time):
    thirty = datetime.timedelta(minutes=mins_before)
    time_obj = datetime.datetime.strptime(time, '%H:%M:%S')
    starting_games = []
    for game in games:
        gametime = game['datetime'][11:19]
        gametime_obj = datetime.datetime.strptime(gametime, '%H:%M:%S')
        if time_obj + thirty > gametime_obj:
            starting_games.append(game)
            games.remove(game)
    if not starting_games:
        return None, games
    else:
        return starting_games, games

def generate_title(game):
    title_template = "GAME THREAD: {acity} {away} ({awin}-{aloss}) @ {hcity} {home} ({hwin}-{hloss}) - {date}"
    away = game['opponent']
    away_rec = get_record(away)
    home = game['hometeam']
    home_rec = get_record(home)
    date = game['datetime'][0:10]
    return title_template.format(acity=away['location'].replace('-', ' '),
                                 away=away['nickname'],
                                 awin=away_rec[0],
                                 aloss=away_rec[1],
                                 hcity=home['location'].replace('-', ' '),
                                 home=home['nickname'],
                                 hwin=home_rec[0],
                                 hloss=home_rec[1],
                                 date=date)

def generate_body(game):
    est = game[datetime][11:19]

def post_GameThread(games, redt):
    print "\nStarting soon: "
    for game in games:
        title = generate_title(game)

def get_login(inp):
    with open(inp, 'r') as login_file:
        user = login_file.readline().strip()
        password = login_file.readline().strip()
    return user, password

# Adapted from: https://github.com/alex/nba-gamethread
def get_record(team):
    team_url = 'http://espn.go.com/nba/team/schedule/_/name/{0}/{1}'.format(team['abbr'], team['full_name'])
    r = requests.get(team_url)
    r.raise_for_status()
    page = PyQuery(r.text)
    text = page('#sub-branding').find('.sub-title').text()
    record = text.split(',', 1)[0]
    return record.split("-")

def get_abbr(team):
    if team['nba_abbr'] is not None:
        return str(team['nba_abbr']).upper()
    else:
        return str(team['abbr']).upper()

def get_nba_page(game):
    year = game['datetime'][0:4]
    month = game['datetime'][5:7]
    day = game['datetime'][8:10]
    home = get_abbr(game['hometeam'])
    away = get_abbr(game['opponent'])
    url = "http://www.nba.com/games/{year}{month}{day}/{away}{home}/gameinfo.html"
    return url.format(year=year,
                      month=month,
                      day=day,
                      away=away,
                      home=home)

def check_games():
    date, time = getCurrent()
    todays_games = []
    starting_games = []
    print 'Hello World', time

if __name__ == '__main__':
    user, password = get_login('../LOGIN')
    redt = praw.Reddit(user_agent='NBA_MOD_BOT')
    redt.login(user, password)
    schedule.every(10).seconds.do(check_games)
    while running:
        schedule.run_pending()
        sleep(1)
