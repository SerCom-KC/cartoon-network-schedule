#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import os
from datetime import datetime
from lxml import etree
import pytz
import re
import json
from calendar import monthrange

def getDate(month, day):
    if month == '01':
        date = 'January'
    elif month == '02':
        date = 'February'
    elif month == '03':
        date = 'March'
    elif month == '04':
        date = 'April'
    elif month == '05':
        date = 'May'
    elif month == '06':
        date = 'June'
    elif month == '07':
        date = 'July'
    elif month == '08':
        date = 'August'
    elif month == '09':
        date = 'September'
    elif month == '10':
        date = 'October'
    elif month == '11':
        date = 'November'
    elif month == '12':
        date = 'December'
    date += ' ' + day.lstrip('0')
    if int(day) >= 11 and int(day) <= 13:
        date += 'th'
    elif day.endswith('1'):
        date += 'st'
    elif day.endswith('2'):
        date += 'nd'
    elif day.endswith('3'):
        date += 'rd'
    else:
        date += 'th'
    return date

def fixName(name, force_the=False, reverse=False):
    fixed_names = []
    for title in name.split('/'):
        fixed = re.sub(r'(.*?) $', 'The \\1', title)
        fixed = re.sub(r'(.*?), The$', 'The \\1', fixed)
        if force_the and not fixed.startswith('The '):
            fixed = 'The ' + fixed
        else:
            fixed = re.sub(r'(.*?), An$', 'An \\1', fixed)
            fixed = re.sub(r'(.*?), A$', 'A \\1', fixed)
        if reverse:
            fixed_names.insert(0, fixed)
        else:
            fixed_names.append(fixed)
    name = '/'.join(fixed_names)
    return name.replace('/', '; ')

def generate():
    today = datetime.now(pytz.timezone('US/Eastern'))
    day = int(today.strftime('%d').lstrip('0'))
    month = today.date().month
    schedules = []
    url = "https://raw.githubusercontent.com/" + os.environ['TRAVIS_REPO_SLUG'] + "/master/show-list?"
    list = requests.get(url, timeout=3).json()
    s = requests.Session()
    while True:
        url = 'https://www.cartoonnetwork.com/cnschedule/xmlServices/' + str(day) + '.EST.xml'
        print('Fetching ' + url)
        allshows = etree.XML(s.get(url, timeout=10).content).xpath('//allshows/show[@blockName!="AdultSwim"]')
        date_split = allshows[0].xpath('@date')[0].split('/')
        if int(date_split[0]) < month:
            print('\033[32mSchedule generation completed successfully!\033[0m')
            manifest(schedules)
            return 0
        date = date_split[2] + '-' + date_split[0] + '-' + date_split[1]
        cn_shows = []
        for show in allshows:
            title = "Unknown Series"
            for element in list:
                if element["showId"] == show.xpath('@showId')[0]:
                    title = element["title"]
            url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/ScheduleServices'
            params = {
                'methodName': 'getEpisodeDesc',
                'showId': show.xpath('@showId')[0],
                'episodeId': show.xpath('@episodeId')[0],
                'isFeatured': 'N'
            }
            while True:
                try:
                    episodeName = fixName(etree.XML(s.get(url, params=params, timeout=3).content).xpath("//Desc/episodeDesc/text()")[0][:-1], reverse=True)
                    break
                except requests.exceptions.ReadTimeout:
                    continue
                except Exception as e:
                    print(e)
                    exit(-1)
            if episodeName == "":
                print('\033[33mFailed to fetch episode name of showId=' + show.xpath('@showId')[0] + ', episodeId=' + show.xpath('@episodeId')[0] + ' from ScheduleServices\033[0m')
                episodeName = fixName(show.xpath('@episodeName')[0], force_the=True if show.xpath('@showId')[0] == "376453" else False)
            rating = show.xpath('@rating')[0]
            airtime_str = show.xpath('@date')[0] + ' ' + show.xpath('@military')[0]
            airtime_dt = pytz.timezone('US/Eastern').localize(datetime.strptime(airtime_str, '%m/%d/%Y %H:%M'))
            airtime = int(airtime_dt.timestamp())
            new = True if show.xpath('@newPremieres')[0] == "Y" else False
            premiere_str = show.xpath('@originalAirDate')[0]
            premiere_dt = pytz.timezone('US/Eastern').localize(datetime.strptime(premiere_str, '%Y-%m-%d %H:%M:%S.%f'))
            premiere = int(premiere_dt.timestamp())
            cn_show = {"show": title, "episode": episodeName, "rating": rating, "airtime": airtime, "new": new, "premiere": premiere}
            cn_shows.append(cn_show)
        result = {"date": date, "data": cn_shows}
        print('Writing schedule of ' + date + ' to file')
        file = open('master/' + date, 'w+')
        file.write(json.dumps(result))
        file.close()
        schedules.append(date)
        day += 1
        if day > monthrange(airtime_dt.date().year, airtime_dt.date().month)[1]:
            day = 1
            month = month + 1 if month != 12 else 1

def guessNextShowings():
    s = requests.Session()
    today = datetime.now(pytz.timezone('US/Eastern'))
    nextshowings = []
    guessmissing = {'slashcount': {}, 'dates': []}
    url = "https://raw.githubusercontent.com/" + os.environ['TRAVIS_REPO_SLUG'] + "/master/show-list?"
    list = requests.get(url, timeout=3).json()
    for element in list:
        if element["blockName"] == "":
            print('Fetching all upcoming showings for ' + element["title"])
            url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/ScheduleServices'
            params = {
                'methodName': 'getAllShowingsByID',
                'showId': element["showId"],
                'timezone': 'EST'
            }
            while True:
                try:
                    allShowings = etree.XML(s.get(url, params=params, timeout=3).content)
                    break
                except requests.exceptions.ReadTimeout:
                    continue
                except Exception as e:
                    print(e)
                    exit(-1)
            try:
                errtmp = allShowings[0]
            except IndexError:
                continue
            title = element["title"]
            guessmissing['slashcount'][element['title']] = 0
            for show in allShowings:
                guessmissing['slashcount'][element['title']] += show.xpath('@episode')[0].count('/') + 1
                if today.date().month == 12 and show.xpath('@date')[0].find('January'):
                    airtime_year = str(today.date().year + 1)
                else:
                    airtime_year = str(today.date().year)
                episodeName = fixName(show.xpath('@episode')[0])
                rating = show.xpath('@rating')[0].replace('[', '').replace(']', '')
                airtime_str = show.xpath('@time')[0] + ' ' + show.xpath('@date')[0] + ' ' + airtime_year
                airtime_dt = pytz.timezone('US/Eastern').localize(datetime.strptime(airtime_str, '%I:%M %p %B %d %Y'))
                airtime = int(airtime_dt.timestamp())
                thumbnail = None
                try:
                    url = "https://s3.amazonaws.com/cn-orchestrator/%s_001_1280x720.jpg" % (show.xpath('@episodeId')[0])
                    response = s.get(url, timeout=10, stream=True)
                    if response.status_code == 200:
                        thumbnail = url
                except Exception as e:
                    print('\033[33mFailed to check thumbnail availability of showId=' + element["showId"] + ', episodeId=' + show.xpath('@episodeId')[0] + '\033[0m')
                nextshowings.append({"show": title, "episode": episodeName, "rating": rating, "airtime": airtime, "thumbnail": thumbnail})
            if guessmissing['slashcount'][element['title']] >= 30:
                date_str = airtime_dt.strftime('%Y-%m-%d')
                flag = True
                for date in guessmissing['dates']:
                    if date_str == date["date"]:
                        flag = False
                        date['shows'].append(element['showId'])
                        break
                if flag:
                    guessmissing['dates'].append({"date": date_str, "shows": [element['showId']]})
    nextshowings = sorted(nextshowings, key=lambda k: int(k['airtime']))
    guessmissing['dates'] = sorted(guessmissing['dates'], key=lambda k: k['date'])
    result = {"updated": int(time.time()), "missing": guessmissing['dates'], "schedule": nextshowings}
    print('Writing to next-showings')
    file = open('master/next-showings', 'w+')
    file.write(json.dumps(result))
    file.close()
    print('Generating human-readable output')
    result = "## DISCLAIMER\n**This is an auto-generated page based on upcoming showing data of each series. All data is pulled from official schedule APIs and is correct at time of publication. Some time slots might be missing due to API limits or unknown series identifiers. Please do not contact any Cartoon Network employee on social media regarding any schedule information this page provides.**  \n**SPOILER ALERT: Links on episode titles leads to a thumbnail of the episode. These thumbnails may be either kind of nonsense (because they were automatically taken), full of spoilers (please add proper spoiler tags when sharing them), or incorrect at all (especially for back to back showings). YOU HAVE BEEN WARNED.**\n\n"
    result += '_Last Update: ' + time.strftime('%B ') + time.strftime('%d, %Y at %H:%M:%S %Z').lstrip('0') + '_ ![](https://api.travis-ci.org/' + os.environ['TRAVIS_REPO_SLUG'] + '.svg?branch=source)  \n\n'
    if guessmissing['dates'] != []:
        result += '## Missing time slots\nIf no upcoming new/returning series exists in the next 2 weeks, the missing time slots might be one of the following:  \n'
        for date in guessmissing['dates']:
            date_list = date["date"].split('-')
            shows = []
            for show in date["shows"]:
                for element in list:
                    if show == element["showId"]:
                        shows.append(element["title"])
            result += 'For missing time slots on ' + getDate(date_list[1], date_list[2]) + ' and/or after: ' + ', '.join(shows) + '  \n'
    result += '\n## Known schedule\n'
    date = ""
    for show in nextshowings:
        airtime_dt = datetime.fromtimestamp(show['airtime']).astimezone(pytz.timezone('US/Eastern'))
        date_str = airtime_dt.strftime('%A, ' + getDate(airtime_dt.strftime('%m'), airtime_dt.strftime('%d')))
        if date != date_str:
            result += '\n### ' + date_str + '\n'
            date = date_str
        result += airtime_dt.strftime('%I:%M%p ' + show['show'] + ' - ')
        if show["thumbnail"]:
            result += '[' + show['episode'] + '](' + show["thumbnail"] + ')  \n'
        else:
            result += show['episode'] + '  \n'
    file = open('master/next-showings.md', 'w+')
    file.write(result)
    file.close()

def manifest(schedules):
    data = []
    for schedule in schedules:
        data.append({"date": schedule, "url": "https://github.com/" + os.environ['TRAVIS_REPO_SLUG'] + "/raw/master/" + schedule})
    result = {"updated": int(time.time()), "data": data}
    print('Writing to manifest')
    file = open('master/manifest', 'w+')
    file.write(json.dumps(result))
    file.close()
    print('\033[32mManifest generation completed successfully!\033[0m')

if __name__ == "__main__":
    generate()
    guessNextShowings()
