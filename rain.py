import requests
import json
import pandas as pd

import os
from os import path
import sys

if os.environ.get("HOMEPATH") == "\\Users\\clevy":
    LOCATION = "LOCAL"
else:
    LOCATION = "SERVER"


def isLocal():
    return LOCATION == "LOCAL"


if isLocal():
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    sys.path.append(os.path.realpath("."))
    sys.path.append("C:/Users/clevy/OneDrive/Python Scripts/CLM_utils")
else:
    sys.path.append("/home/CyrilFinanceData/FinDataScrap/utils")

import email_CLM

runTime = 6

LAT = 47.174340
LON = 8.446700

URL_ROOT = "https://api.openweathermap.org/data/3.0/onecall"
API_KEY = "3a9a7363411e09de7cb64f4d7bffb498"

weather_params = {"lat": LAT, "lon": LON, "appid": API_KEY}

response = requests.get(URL_ROOT, params=weather_params)
response.raise_for_status()
fulldata = response.json()
data = fulldata["hourly"][:16]
df = pd.DataFrame(data)
nested = df["weather"]
exploded = nested.apply(lambda s: str(s[0]))
exploded.replace("'", '"', regex=True, inplace=True)
exploded = exploded.apply(json.loads).apply(pd.Series)
exploded.columns = ["weather_" + c for c in exploded.columns]
df = pd.concat([df.drop("weather", axis=1), exploded], axis=1)
df["temp"] = df["temp"].apply(lambda x: int(x - 273))
df["feels_like"] = df["feels_like"].apply(lambda x: int(x - 273))
df["dew_point"] = df["dew_point"].apply(lambda x: int(x - 273))
output = df[["temp", "feels_like", "dew_point", "pressure", "wind_speed", "weather_description"]]
output.index += runTime
output.index.rename("Hour", inplace=True)
print(output)
minCode = df["weather_id"].min()
willRain = minCode < 700
title = "Weather forecast for today"
if willRain:
    title += " | Attention : PRECIPITATIONS !"

printTable = email_CLM.nice_table(output, title=title, color_border="black", min_width=100, min_chars=6, digits=1, comma=False)
email_CLM.send_cyril_andrea(title, printTable)
print("EMail sent")
