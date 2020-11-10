import json
import os
import subprocess
from datetime import datetime, timedelta

import pytz
import requests

if __name__ == "__main__":
    s = requests.Session()

    schedule = {}

    response = s.get("https://time.ngtv.io/v1/rundown", params={
                    "instance": "as-east", "startTime": 0, "endTime": 2147483647}, timeout=30).json()
    manifest = {"updated": int(response["timeUTC"]), "data": []}

    for show in response["shows"]:
        del(show["last_update"])
        del(show["serial"])
        time = datetime.utcfromtimestamp(show["scheduled_timestamp"]).replace(
            tzinfo=pytz.timezone("UTC")).astimezone(tz=pytz.timezone("US/Eastern"))
        date_string = time.strftime("%Y-%m-%d")
        if date_string not in schedule:
            schedule[date_string] = [show]
        else:
            schedule[date_string].append(show)

    del(schedule[list(schedule)[0]])

    for date in schedule.keys():
        with open("ngtv-v1/" + date, "w+") as file:
            file.write(json.dumps(schedule[date], indent=4))
        manifest["data"].append(
            {"date": date, "url": "https://github.com/%s/raw/ngtv-v1/%s" % (os.environ['GITHUB_REPOSITORY'], date)})

    if subprocess.run(["git", "status", "--porcelain"], cwd="ngtv-v1", stdout=subprocess.PIPE).stdout != b"":
        with open("ngtv-v1/manifest", "w+") as file:
            file.write(json.dumps(manifest, indent=4))
