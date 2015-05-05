#!/usr/bin/python

from time import sleep
from prettytable import PrettyTable
import arrow
import schedule
import requests
import json

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
    def __init__(self, gameid, away, away_rec, home, home_rec, gametime, tv):
        self.gameid = gameid
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

def convert_to_24(time, is_PM):
    #Originally arrow objects do not account for AM/PM, this is to remedy that
    if is_PM:
        return time.replace(hours=12)
    else:
        return time

def find_team(abbr):
    for team in teams:
        if abbr.lower() == team['abbr']:
            return team

def get_record(team_row):
    record = {}
    record['total'] = team_row.split('-')
    record['wins'] = record['total'][0]
    record['losses'] = record['total'][1]
    return record

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
    c = get_current()
    print "[{:02d}:{:02d}:{:02d}] Searching for games starting soon...".format(c.hour, c.minute, c.second)
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
    scoreboard_base = "http://stats.nba.com/stats/scoreboard/?LeagueID={leagueid:02d}"+ \
        "&gameDate={month:02d}%2F{day:02d}%2F{year}&DayOffset={offset}"
    scoreboard_url = scoreboard_base.format(leagueid = 00,
                                           month = now.month,
                                           day = now.day,
                                           year = now.year,
                                           offset = 0)
    r = requests.get(scoreboard_url)
    if r.status_code == 200:
        scoreboard = json.loads(r.text)
        game_data = scoreboard['resultSets'][0]['rowSet']
        team_data = scoreboard['resultSets'][1]['rowSet']
        i = 0
        for game in game_data:
            time = game[4].replace(':', ' ').split(' ')
            gameid = game[2]
            away = find_team(team_data[i][4])
            home = find_team(team_data[i+1][4])
            gametime = arrow.now('US/Eastern').replace(hour=int(time[0]),
                                                       minute=int(time[1]),
                                                       second=0,
                                                       microsecond=0)
            gametime = convert_to_24(gametime, 'pm' in game[4])
            tv = game[11]
            games.append(Game(gameid, away, get_record(team_data[i][6]), home, get_record(team_data[i+1][6]), gametime, tv))
            i += 2
    else:
        print "Didn't work :("

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
