from flask import Blueprint
from configs.redis import redisLoggerGetDates, redisLoggerGetDatesPerApp, redisLoggerGetLogsPerApp

routesLogs = Blueprint("routesLogs", __name__)

@routesLogs.route('', methods=['GET'], strict_slashes=False)
def getLogsDates():
    logDates = redisLoggerGetDates()
    return logDates

@routesLogs.route('/<path:subpath>', methods=['GET'], strict_slashes=False)
def getLogs(subpath=''):
    getRedisLogList = redisLoggerGetDates(subpath)
    return getRedisLogList

@routesLogs.route('/<appName>/', methods=['GET'], strict_slashes=False)
def getLogsByApp(appName='app'):
    getRedisLogListPerApp = redisLoggerGetDatesPerApp(appName)
    return getRedisLogListPerApp

@routesLogs.route('/<appName>/<path:subpath>', methods=['GET'], strict_slashes=False)
def getLogsByDate(appName='app', subpath=''):
    getRedisLogsByDate = redisLoggerGetLogsPerApp(appName, subpath)
    return getRedisLogsByDate