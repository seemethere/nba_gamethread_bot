#!/usr/bin/python

# Heavily based on https://github.com/davewalk/2013-2014-nba-schedule

import requests, json
from bs4 import BeautifulSoup
import time
import datetime
import pytz

teams_file = open('../data/teams.json').read()
teams_json = json.loads(teams_file)
teams = teams_json['teams']

def find_team(location, nickname=''):
    # Los Angeles makes this tricky
    for team in teams:
        if nickname!= '':
            if nickname in team.values():
                return team
        else:
            if location in team.values():
                return team


# Cool!: http://stackoverflow.com/questions/455580/json-datetime-between-python-and-javascript
dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None

if __name__ == '__main__':
    for team in teams:
        #print "\n\n", team, "\n\n"
        team_url = 'http://espn.go.com/nba/team/schedule/_/name/{0}/{1}'.format(team['abbr'], team['full_name'])
        final_schedule = []

        r = requests.get(team_url)

        if r.status_code is 200:
            soup = BeautifulSoup(r.text)
            schedule = soup.find_all('table')[0]
            rows = schedule.find_all('tr')
            team_schedule = {'team': team, 'games': []}
            for row in rows:
                if row['class'][0] == 'oddrow' or row['class'][0] == 'evenrow':
                    elements = row.find_all('td')
                    # Included if a game has already been completed
                    if 'li class' in str(elements[2].contents[0]): continue
                    #Location (All I want is Home Games)
                    if '@' in str(elements[1].contents[0]): continue

                    # Date and Time
                    full_date = elements[0].contents[0]
                    month_abbr = full_date.split(',')[1].strip().split(' ')[0]
                    month = int(time.strptime(month_abbr, '%b').tm_mon)
                    year = 2014 if month > 4 else 2015
                    day = int(full_date.split(',')[1].strip().split(' ')[1])
                    gametime = elements[2].contents[0]
                    if 'preview' in str(gametime): continue
                    hour = int(gametime.split(':')[0])
                    hour = hour if hour is 12 else hour + 12
                    minute = int(gametime.split(':')[1].strip().split(' ')[0])
                    full_datetime = datetime.datetime(year,
                                                      month,
                                                      day,
                                                      hour,
                                                      minute,
                                                      0,
                                                      0,
                                                      tzinfo=pytz.timezone('US/Eastern'))
                    #Find the opponenet
                    opponent_location = row.find_all('li')[2].a.contents[0]
                    opponent_nickname = ''
                    if opponent_location == 'Los Angeles':
                        url = row.find_all('li')[2].a['href']
                        if 'lakers' in url:
                            opponent_nickname = 'Lakers'
                        elif 'clipper' in url:
                            opponent_nickname = 'Clippers'
                    if opponent_location == 'NY Knicks':
                        opponent_location = 'New York'
                    try:
                        opponent_info = find_team(opponent_location, opponent_nickname)
                    except:
                        opponent_info = find_team(opponent_location)
                    # Find our TV Station
                    tv = 'Regional'
                    if 'NBATV' in str(elements[3].contents[0].encode('utf-8')):
                        tv = 'NBATV'
                    elif 'ESPN' in str(elements[3].contents[0].encode('utf-8')):
                        tv = 'ESPN'
                    elif 'TNT' in str(elements[3].contents[0].encode('utf-8')):
                        tv = 'TNT'
                    where = {
                        'city':team['city'],
                        'arena':team['arena']
                    }
                    game = {
                        'fullDate': full_date,
                        'datetime': full_datetime,
                        'where': where,
                        'hometeam':team,
                        'opponent': opponent_info,
                        'tv': tv
                    }
                    final_schedule.append(game)
            json_file = open('../data/teams/{name}.json'.format(name = team['full_name']), 'w')
            team_data = {
                'team': team,
                'schedule': final_schedule
            }
            final_json = json.dumps(team_data, sort_keys= True, indent=4, default=dthandler)
            json_file.write(final_json)
            json_file.close()
            time.sleep(1)
            print '{0} {1} completed...'.format(team['location'], team['nickname'])
    exit()
