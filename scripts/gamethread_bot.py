#!/usr/bin/python

import datetime
import pytz
import json
from time import sleep

teams_file = open('../data/teams.json').read()
teams_json = json.loads(teams_file)
teams = teams_json['teams']
running = True

def getCurrent():
    now = datetime.datetime.now(pytz.timezone('US/Eastern'))
    today = datetime.datetime(now.year, now.month, now.day, now.hour,now.minute, 0, 0,
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
    thirty = datetime.timedelta(minutes=30)
    time_obj = datetime.datetime.strptime(time, '%H:%M:%S')
    starting_games = []
    for game in games:
        gametime = game['datetime'][11:19]
        gametime_obj = datetime.datetime.strptime(gametime, '%H:%M:%S')
        if time_obj + thirty > gametime_obj:
            starting_games.append(game)
    if not starting_games:
        return None
    else:
        return starting_games


def postGameThread(*games):
    None
    #TODO: Finish function to actually write the game threads

if __name__ == '__main__':
    current_date = None
    todays_games = []
    starting_games = []
    while running:
        date, time = getCurrent()
        if current_date != date:
            #Clears the games that are for today
            todays_games[:] = []
            starting_games[:] = []
            current_date = date
        print "Current Date: {0}\tCurrent Time: {1}\n".format(date.date(), time)
        if not todays_games:
            todays_games = getTodaysGames(date)
            print "Todays Games:"
            for game in todays_games:
                print "{home} vs. {away} @ {time}".format(home=game['hometeam']['nickname'],
                                                          away=game['opponent']['nickname'],
                                                          time=game['datetime'][11:19])
        starting_games = compareTimes(todays_games, time)
        if starting_games is not None:
            postGameThread(starting_games)
        else:
            print "\nNo games starting soon!"
        print "Sleeping for 30 minutes..."
        sleep(600)
        date, time = getCurrent()
        print "Current Date: {0}\tCurrent Time: {1}".format(date.date(), time)
        print "Still sleeping... 20 minutes left!"
        sleep(600)
        date, time = getCurrent()
        print "Current Date: {0}\tCurrent Time: {1}".format(date.date(), time)
        print "Still sleeping... 10 minutes left!"
        sleep(600)
        print "Going back to work!"

