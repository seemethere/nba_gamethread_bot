#!/usr/bin/python

from bs4 import BeautifulSoup
from time import sleep
from prettytable import PrettyTable
import arrow
import schedule
import requests
import json

current_date = None
start_offset = 30 #in minutes

with open('../data/teams.json', 'r') as teams_file:
    teams_text = teams_file.read()
    teams_json = json.loads(teams_text)
    teams = teams_json['teams']

class Game:
    def __init__(self, away, away_rec, home, home_rec, gametime):
        self.away = away
        self.away_rec = away_rec
        self.home = home
        self.home_rec = home_rec
        self.gametime = gametime
        self.posted = False

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

def get_current():
    return arrow.now('US/Eastern')

def get_todays_games():
    now = get_current().datetime
    date_fmt = '{year}{month:02d}{day}'.format(year=now.year,
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
        i = 0
        games = []
        for matchup in matchups:
            time = times[i].split(':')
            away = find_team(matchup[0:3])
            home = find_team(matchup[3:6])
            gametime = arrow.now('US/Eastern').replace(hour=int(time[0][0:2]),
                                                       minute=int(time[1][0:2]),
                                                       second=0,
                                                       microsecond=0)
            gametime = convert_to_24(gametime, 'pm' in time[1])
            games.append(Game(away, get_record(away), home, get_record(home), gametime))
            i += 1
        return sorted(games, key=lambda x: x.gametime) #Sorts by time, probably not necessary
    else:
        return r.status_code

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

if __name__ == '__main__':
    games = get_todays_games()
    if isinstance(games, int):
        print 'ERROR[{}]'.format(games)
        exit()
    table = PrettyTable(['Time', 'Away', 'Home', 'Starting Soon'])
    table.align['Home'] = table.align['Away'] = 'l'
    for game in games:
        hour, minute = game.get_time()
        table.add_row(['{:02d}:{:02d}'.format(hour, minute),
                       game.get_team(False),
                       game.get_team(True),
                       game.starting_soon()])
    print table
