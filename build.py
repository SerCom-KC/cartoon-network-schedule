import json
import os
from datetime import datetime, timedelta

import pytz
import requests

s = requests.Session()

schedule = {}

# Starts from yesterday at 12 AM
start_time = int((datetime.now().astimezone(tz=pytz.timezone("US/Eastern")).replace(
    hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)).timestamp())

# Ends at 30 days from now
end_time = int(datetime.now().timestamp() + 30*24*60*60)

response = s.get("https://time.ngtv.io/v1/rundown", params={
                 "instance": "as-east", "startTime": start_time, "endTime": end_time}, timeout=30).json()
manifest = {"updated": int(response["timeUTC"]), "data": []}

for show in response["shows"]:
    time = datetime.utcfromtimestamp(show["scheduled_timestamp"]).replace(
        tzinfo=pytz.timezone("UTC")).astimezone(tz=pytz.timezone("US/Eastern"))
    date_string = time.strftime("%Y-%m-%d")
    if date_string not in schedule:
        schedule[date_string] = [show]
    else:
        schedule[date_string].append(show)

for date in schedule.keys():
    with open("ngtv-v1/" + date, "w+") as file:
        file.write(json.dumps(schedule[date], indent=4))
    manifest["data"].append(
        {"date": date, "url": "https://github.com/%s/raw/ngtv-v1/%s" % (os.environ['TRAVIS_REPO_SLUG'], date)})

with open("ngtv-v1/manifest", "w+") as file:
    file.write(json.dumps(manifest, indent=4))
