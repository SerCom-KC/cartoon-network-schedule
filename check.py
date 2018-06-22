#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from lxml import etree
import requests
import re
import os

if __name__ == "__main__":
    result = True
    print('Check if there is any show not exist in list')
    list = requests.get("https://raw.githubusercontent.com/" + os.environ['TRAVIS_REPO_SLUG'] + "/master/show-list").json()
    for day in range(1, 32):
        for channel in ['xmlServices', 'asXml']:
            url = 'https://www.adultswim.com/adultswimdynsched/' + channel + '/' + str(day) + '.EST.xml'
            print('Fetching ' + url)
            allshows = etree.XML(requests.get(url, timeout=10).content).xpath('//allshows/show')
            for show in allshows:
                flag = False
                for element in list:
                    if element["showId"] == show.xpath('@showId')[0]:
                        flag = True
                        break
                if not flag:
                    result = False
                    print('\033[31mUnknown show detected: ' + show.xpath('@showId')[0] + ' - ' + show.xpath('@urlName')[0] + '\033[0m')
    if result:
        print('\033[32mLooks good! Every show is known in the list\033[0m')
        exit(0)
    else:
        print('\033[31mUnknown show detected, aborting the build\033[0m')
        exit(-1)
