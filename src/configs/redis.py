import os
import json
import redis
from datetime import date

dbIndex = {
    "logs": 0,
    "rules": 1,
    "limits": 2
}

loggingApps = {
    "meli": True,
    "logs": False,
    "fakeApi": True
}

def redisConnect(dbNumber):
    r = redis.Redis(host=os.environ["REDIS_HOST"], port=6379, charset="utf-8", db=dbIndex[dbNumber], decode_responses=True)
    return r

def checkIfLogs(appName):
    loggingConfig = False if appName == '' else loggingApps[appName]
    return loggingConfig

def redisLogger(appName, logStream):
    checkIfLogs(appName)
    if checkIfLogs(appName):
        logDate = date.today().strftime("%d-%m-%Y")
        logEntry = json.dumps(logStream).encode("utf-8")
        redis = redisConnect("logs")
        redis.rpush(f"logs:{appName}:{logDate}", logEntry)
        print(logStream)
    return True

def redisLoggerGetDates():
    redis = redisConnect("logs")
    logDates = redis.keys(pattern=f"logs:*:*")
    return logDates

def redisLoggerGetDatesPerApp(appName):
    redis = redisConnect("logs")
    logDatesperApp = redis.keys(pattern=f"logs:{appName}:*")
    return logDatesperApp

def redisLoggerGetLogsPerApp(appName, logDate):
    redis = redisConnect("logs")
    logEntries = redis.lrange(f"logs:{appName}:{logDate}", 0, -1)
    return logEntries
    
def redisLimiter(limiterType, Option, Data, Args=''):
    response = eval(f"{limiterType}{Option}{(limiterType, Data, Args)}")
    return response

def rulesUpdate(limiterType, Rule, Action):
    redis = redisConnect(limiterType)
    redis.flushdb
    ruleUpdate = redis.set(Rule, Action)
    return ruleUpdate
    
def limitsCreate(limiterType, baseRule, limitData):
    redis = redisConnect(limiterType)
    limitCreate = redis.set(baseRule, limitData["request"], ex=limitData["timeInSeconds"])
    return limitCreate

def rulesCheck(limiterType, remoteAddr, requestPath):
    redis = redisConnect(limiterType)
    if redis.keys(pattern=f"{remoteAddr};/{requestPath}"):
        ruleName = redis.keys(pattern=f"{remoteAddr};/{requestPath}")[0]
        ruleData = redis.get(f"{remoteAddr};/{requestPath}")
    elif redis.keys(pattern=f"/{requestPath}"):
        ruleName = redis.keys(pattern=f"/{requestPath}")[0]
        ruleData = redis.get(f"/{requestPath}")
    elif redis.keys(pattern=f"{remoteAddr}"):
        ruleName = redis.keys(pattern=f"{remoteAddr}")[0]
        ruleData = redis.get(remoteAddr)
    else:
        ruleName = ""
        ruleData = ""
    return str(f"{ruleName}:{ruleData}")
    
def limitsCheck(limiterType, ruleName, ruleData):
    redis = redisConnect(limiterType)
    if redis.keys(pattern=f"{ruleName}"):
        limitValue = redis.get(ruleName)
    else:
        limitValue = -1
    return limitValue
    
def limitsUpdate(limiterType, ruleName, existingLimit):
    redis = redisConnect(limiterType)
    newLimit = int(existingLimit) - 1
    limitValue = redis.set(ruleName, newLimit, keepttl=True)
    return limitValue