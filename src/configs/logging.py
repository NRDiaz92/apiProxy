from logging.config import dictConfig
from configs.redis import redisLogger
from datetime import datetime
import html_to_json
import json
import re

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] - %(message)s",
                "datefmt": "%d/%B - %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": "worldClock.log",
                "formatter": "default",
            },
        },
        "root": {"level": "DEBUG", "handlers": ["console", "file"]},
    }
)

def logRequest(requestId, request, appName):
    entryTime = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    logEntry = {"Timestamp": f"{entryTime}", "requestId": f"{requestId}", "Request": {"IP": f"{request.remote_addr}", "Method": f"{request.method}", "Full_Path": f"{request.full_path}"}}
    redisLogger(appName, logEntry)
    return logEntry

def logResponse(requestTime, requestId, response, appName):
    jsonResponse=''
    entryTime = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    if re.search("text/html", response.headers.get('Content-Type')):
        if re.search("Too Many Requests", response.data.decode()):
            jsonResponse = html_to_json.convert(response.data.decode())
    else:
        jsonResponse = json.loads(response.data.decode())
    logEntry = {"Timestamp": f"{entryTime}", "requestId": f"{requestId}", "requestTime": f"{requestTime}ms", "Response": f"{jsonResponse}"}
    redisLogger(appName, logEntry)
    return logEntry