import ast
from flask import abort
from configs.redis import redisLimiter

def ruleConfigs():
    Rules = open("configs/limits.config", "r").read()
    rulesConfig = ast.literal_eval(Rules)
    return rulesConfig

def rulesUpdater():
    Rules = ruleConfigs()
    for appName, limitConfigs in Rules.items():
        for Rule, Action in limitConfigs.items():
            redisLimiter("rules", "Update", appName, {"Rule": Rule, "Action": Action})

def rulesChecker(appName, ruleData):
    redisCheckRule = redisLimiter("rules", "Check", appName, {"remoteAddr": ruleData["remoteAddr"], "requestPath": ruleData["requestPath"]})
    return redisCheckRule

def limitCreator(appName, limitData):
    print(f'limitData: {limitData}')
    request, timeInSeconds = convertRuleToSeconds(limitData["ruleData"])
    redisCreate = redisLimiter("limits", "Create", appName, {"ruleName": limitData["ruleName"], "request": request, "timeInSeconds": timeInSeconds})
    return redisCreate

def limitsUpdater(appName, limitData):
    redisUpdate = redisLimiter("limits", "Update", appName, {"ruleName": limitData["ruleName"], "existingLimit": limitData["existingLimit"]})
    return redisUpdate
    
def limitsChecker(appName, limitData):
    redisCheckLimit = redisLimiter("limits", "Check", appName, {"ruleName": limitData["ruleName"], "ruleData": limitData["ruleData"]})
    return redisCheckLimit
    
def requestBlock():
    abort(404, {"Connection limit excedeed"})
            
def convertRuleToSeconds(ruleData="0/0"):
    seconds=1
    minute=60
    hour=360
    day=86400
    requests = int(ruleData.split("/")[0])
    timeMeassure = ruleData.split("/")[1]
    timeInSeconds = int(timeMeassure.replace(str(timeMeassure), str(eval(timeMeassure))))
    return requests, timeInSeconds

def setLimits(appName, request):
    rules = ruleConfigs()
    remoteAddr = request.remote_addr
    if len(request.path.replace(f"/{appName}", '')) > 0:
        requestPath = request.path.replace(f"/{appName}", '').split("/")[1]
    else:
        requestPath = str(f"{appName}")
    baseRule = rulesChecker(appName, {"remoteAddr": remoteAddr, "requestPath": requestPath})
    ruleData = baseRule.split(':')[2]
    ruleName = baseRule.split(f':{ruleData}')[0]
    if baseRule != ':' or baseRule != '':
        existingLimit = int(limitsChecker(appName, {"ruleName": ruleName, "ruleData": ruleData}))
        if existingLimit != "":
            if existingLimit > 0:
                limitsUpdater(appName, {"ruleName": ruleName, "existingLimit": existingLimit})
            elif existingLimit < 0:
                limitCreator(appName, {"ruleName": ruleName, "ruleData": ruleData})
            else:
                requestBlock()
        else:
            limitCreator(appName, {"ruleName": ruleName, "ruleData": ruleData})
    else:
        pass