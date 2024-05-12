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
    
def redisLimiter(limiterType, Option, appName, Args=''):
    response = eval(f"{limiterType}{Option}{(limiterType, appName, Args)}")
    return response

def rulesUpdate(limiterType, appName, Args):
    redis = redisConnect(limiterType)
    redis.flushdb
    for Rule, Action in Args.items():
        Rule = str(f'{appName}:{Args["Rule"]}')
        Action = Args["Action"]
        ruleUpdate = redis.set(Rule, Action)
        if ruleUpdate:
            print(f'Sucesfully updated rule: "{Rule}:{Action}"')
    
def limitsCreate(limiterType, appName, Args):
    redis = redisConnect(limiterType)
    ruleName = f'{Args["ruleName"]}'
    limitCreate = redis.set(ruleName, Args["request"], ex=Args["timeInSeconds"])
    return limitCreate

def rulesCheck(limiterType, appName, Args):
    redis = redisConnect(limiterType)
    if redis.keys(pattern=f'{appName}:{Args["remoteAddr"]};/{Args["requestPath"]}'):
        ruleName = redis.keys(pattern=f'{appName}:{Args["remoteAddr"]};/{Args["requestPath"]}')[0]
        ruleData = redis.get(f'{appName}:{Args["remoteAddr"]};/{Args["requestPath"]}')
    elif redis.keys(pattern=f'{appName}:/{Args["requestPath"]}'):
        ruleName = redis.keys(pattern=f'{appName}:/{Args["requestPath"]}')[0]
        ruleData = redis.get(f'{appName}:/{Args["requestPath"]}')
    elif redis.keys(pattern=f'{appName}:{Args["remoteAddr"]}'):
        ruleName = redis.keys(pattern=f'{appName}:{Args["remoteAddr"]}')[0]
        ruleData = redis.get(f'{appName}:{Args["remoteAddr"]}')
    else:
        ruleName = ""
        ruleData = ""
    print(str(f"{ruleName}:{ruleData}"))
    return str(f"{ruleName}:{ruleData}")
    
def limitsCheck(limiterType, appName, Args):
    redis = redisConnect(limiterType)
    if redis.keys(pattern=Args["ruleName"]):
        limitValue = redis.get(Args["ruleName"])
    else:
        limitValue = -1
    return limitValue
    
def limitsUpdate(limiterType, appName, Args):
    redis = redisConnect(limiterType)
    newLimit = int(Args["existingLimit"]) - 1
    limitValue = redis.set(Args["ruleName"], newLimit, keepttl=True)
    return limitValue