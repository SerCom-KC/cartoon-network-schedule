import json
import os
import subprocess
from datetime import datetime, timedelta, timezone

import pytz
import requests

FOLDER_NAME = "ngtv-v1"
GITHUB_REPOSITORY = os.environ.get('GITHUB_REPOSITORY', "SerCom-KC/cartoon-network-schedule")

if __name__ == "__main__":
    s = requests.Session()

    schedule = {}

    manifest = {
        "updated": 0,
        "data": []
    }

    for instance in ["as-east", "cn-east"]:
        response = s.get(
            "https://time.ngtv.io/v1/rundown",
            params={
                "instance": instance,
                #"startTime": int(datetime(year=2024, month=7, day=30, tzinfo=pytz.timezone("US/Eastern")).timestamp()),
                "startTime": int((datetime.now() - timedelta(days=14)).timestamp()),
                "endTime": 2147483647
            },
            timeout=30
        ).json()

        updated = int(response["timeUTC"])
        if updated > manifest["updated"]:
            manifest["updated"] = updated

        for show in response["shows"]:
            time = datetime.fromtimestamp(show["guide_timestamp"], tz=timezone.utc).replace(
                tzinfo=timezone.utc).astimezone(tz=pytz.timezone("US/Eastern"))
            date_string = time.strftime("%Y-%m-%d")
            if date_string not in schedule:
                schedule[date_string] = [show]
            else:
                schedule[date_string].append(show)

    del(schedule[list(schedule)[0]])

    for date in schedule.keys():
        with open(os.path.join(FOLDER_NAME, date), "w+") as file:
            file.write(json.dumps(sorted(schedule[date], key=lambda x: x["guide_timestamp"]), indent=4))
        manifest["data"].append(
            {"date": date, "url": "https://github.com/%s/raw/ngtv-v1/%s" % (GITHUB_REPOSITORY, date)})

    if subprocess.check_output(["git", "status", "--porcelain"], cwd=FOLDER_NAME) != b"":
        with open(os.path.join(FOLDER_NAME, "manifest"), "w+") as file:
            file.write(json.dumps(manifest, indent=4))
