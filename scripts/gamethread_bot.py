#!/usr/bin/python

from bs4 import BeautifulSoup
from time import sleep
from prettytable import PrettyTable
import arrow
import schedule
import requests
import json
import curses


start_offset = 30 #in minutes
games = []
running = True

with open('../data/teams.json', 'r') as teams_file:
    teams_text = teams_file.read()
    teams_json = json.loads(teams_text)
    teams = teams_json['teams']

with open('../data/templates/title.txt', 'r') as title_file:
    title_text = title_file.read()

class Game:
    def __init__(self, away, away_rec, home, home_rec, gametime, tv):
        self.away = away
        self.away_rec = away_rec
        self.home = home
        self.home_rec = home_rec
        self.gametime = gametime
        self.posted = False
        self.tv = tv

    def get_time(self, tz='US/Eastern'):
        time = self.gametime.to(tz).datetime
        return time.hour, time.minute

    def get_team(self, is_home):
        fmt = '{} {} ({}-{})'
        if is_home:
            return fmt.format(self.home['location'], self.home['nickname'],
                              self.home_rec['wins'], self.home_rec['losses'])
        else:
            return fmt.format(self.away['location'], self.away['nickname'],
                              self.away_rec['wins'], self.away_rec['losses'])

    def starting_soon(self):
        if get_current().replace(minutes=30) > self.gametime:
            return True
        return False

    def is_posted(self):
        return self.posted

    def on_national_tv(self):
        return self.tv != 'NBALP'

def get_current():
    return arrow.now('US/Eastern')

#Original arrow objects did not account for AM/PM, this is to remedy that
def convert_to_24(time, is_PM):
    if is_PM:
        return time.replace(hours=12)
    else:
        return time

def find_team(abbr):
    for team in teams:
        if abbr.lower() == team['abbr']:
            return team

def get_record(team):
    loc = team['location']
    # These two teams are weird in how they're accounted for
    if loc == 'Los Angeles':
        if team['abbr'] == 'lac':
            loc = 'L.A. Clippers'
        else:
            loc = 'L.A. Lakers'
    nba_url = 'http://www.nba.com/standings/team_record_comparison/conferenceNew_Std_Div.html'
    r = requests.get(nba_url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text)
        records = soup.findAll('tr', {'class':'odd'})
        records2 = soup.findAll('tr', {'class':'even'})
        for element in records2:
            records.append(element)
        for element in records:
            if loc in str(element.contents[1]):
                record = {}
                record['wins'] = element.contents[3].string
                record['losses'] = element.contents[5].string
        return record
    print "ERROR: Couldn't find record for {} {}".format(loc, team['nickname'])

def get_table_of_games(matches):
    table = PrettyTable(['Time', 'Away', 'Home', 'Starting Soon', 'TV'])
    table.align['Home'] = table.align['Away'] = 'l'
    for game in matches:
        hour, minute = game.get_time()
        table.add_row(['{:02d}:{:02d}'.format(hour, minute),
                       game.get_team(False),
                       game.get_team(True),
                       game.starting_soon(),
                       game.tv])
    return table.get_string()

def find_games_starting_soon():
    print "Searching for games starting soon..."
    for game in games:
        if game.starting_soon():
            title = generate_title(game)
            games.remove(game)
            print "{}".format(title)
            #TODO: THIS IS WHERE THE POST TO REDDIT PART WILL GO

def generate_title(game):
    title = title_text
    date_fmt = '{}/{}/{}'.format(game.gametime.month,
                                 game.gametime.day,
                                 game.gametime.year)
    return title.format(away = game.get_team(False),
                        home = game.get_team(True),
                        date = date_fmt)

def get_todays_games():
    print "Getting today's games"
    now = get_current().datetime
    games[:] = []
    date_fmt = '{year}{month:02d}{day:02d}'.format(year=now.year,
                                                   month=now.month,
                                                   day=now.day)
    today_url = 'http://www.nba.com/gameline/{date}/'.format(date=date_fmt)
    #today_url = 'http://www.nba.com/gameline/20150213/' #Error 403 Tester
    r = requests.get(today_url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text)
        times_base = soup.findAll('div', {'class':'nbaFnlStatTxSm'})
        times = [str(element.string) for element in times_base]
        if len(times) < 1: return None
        matchups_base = soup.findAll('div', {'class': 'nbaPreMnButtDiv'})
        matchups = [str(element)[54:61] for element in matchups_base]
        tv_stations = soup.findAll('div', {'class':'nbaLiveNetwkLogo'})
        i = 0
        for matchup in matchups:
            time = times[i].split(':')
            # Finds out the tv stations it's on
            if 'nbaTNT' in  str(tv_stations[i]):
                tv = 'TNT'
            elif 'nbaESPN2' in str(tv_stations[i]):
                tv = 'ESPN2'
            elif 'nbaESPN' in str(tv_stations[i]):
                tv = 'ESPN'
            elif 'nbaNBATV' in str(tv_stations[i]):
                tv = 'NBATV'
            else:
                tv = 'NBALP'
            away = find_team(matchup[0:3])
            home = find_team(matchup[3:6])
            gametime = arrow.now('US/Eastern').replace(hour=int(time[0][0:2]),
                                                       minute=int(time[1][0:2]),
                                                       second=0,
                                                       microsecond=0)
            gametime = convert_to_24(gametime, 'pm' in time[1])
            games.append(Game(away, get_record(away), home, get_record(home), gametime, tv))
            i += 1
    else:
        None
        #TODO: Add error logging mechanism

if __name__ == '__main__':
    version = 0.2
    print "NBA Gamethread Bot v{} by seemethere has started...".format(version)
    get_todays_games()
    schedule.every().day.at('4:00').do(get_todays_games)
    schedule.every(1).minutes.do(find_games_starting_soon)
    print "{}".format(get_table_of_games(games))
    while running:
        schedule.run_pending()
        sleep(30)
    exit()
