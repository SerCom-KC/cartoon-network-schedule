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

def fixName(name, force_the=False):
    for title in name.split('/'):
        fixed = re.sub(r'(.*?) $', 'The \\1', title)
        fixed = re.sub(r'(.*?), The$', 'The \\1', fixed)
        if force_the and not fixed.startswith('The '):
            fixed = 'The ' + fixed
        else:
            fixed = re.sub(r'(.*?), An$', 'An \\1', fixed)
            fixed = re.sub(r'(.*?), A$', 'A \\1', fixed)
        name = name.replace(title, fixed)
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
        url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/' + str(day) + '.EST.xml'
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
                    episodeName = fixName(etree.XML(s.get(url, params=params, timeout=3).content).xpath("//Desc/episodeDesc/text()")[0][:-1])
                    break
                except requests.exceptions.ReadTimeout:
                    continue
                except Exception as e:
                    print(e)
                    exit(-1)
            if episodeName == "":
                print('\033[33mFailed to fetch episode name of showId=' + show.xpath('@showId')[0] + ', episodeId=' + show.xpath('@episodeId')[0] + ' from ScheduleServices\033[0m')
                episodeName = fixName(show.xpath('@episodeName')[0], True if show.xpath('@showId')[0] == "376453" else False)
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
