#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from lxml import etree
import requests
import re

if __name__ == "__main__":
    print('Check if there is any show not exist in list')
    list = requests.get("https://raw.githubusercontent.com/" + os.environ['TRAVIS_REPO_SLUG'] + "/master/show-list").json()
    for day in range(1, 32):
        url = 'https://www.adultswim.com/adultswimdynsched/xmlServices/' + str(day) + '.EST.xml'
        print('Fetching ' + url)
        allshows = etree.XML(requests.get(url, timeout=10).content).xpath('//allshows/show[@blockName=""]')
        for show in allshows:
            flag = False
            for element in list:
                if element["showId"] == show.xpath('@showId')[0]:
                    flag = True
                    break
            if not flag:
                print('\033[91mUnknown show detected, aborting the build\033[0m')
                exit(-1)
    print('\033[92mLooks good! Every show is known in the list\033[0m')
    exit(0)