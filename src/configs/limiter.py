from flask import abort
from configs.redis import redisLimiter

defaultLimit = "500000/seconds"

Rules = {
        "172.19.0.2": "15/minute",
        "/categories": "2/minute",
        "172.19.0.2;/sites": "15/hour",
        "172.19.0.2;/categories": "5/day",
        "152.152.152.152;/items": "10/minute"
        }

def rulesUpdater():
    for Rule, Action in Rules.items():
        redisUpdate = redisLimiter("rules", "Update", Rule, Action)
    return redisUpdate

def rulesChecker(remoteAddr, requestPath):
    redisCheckRule = redisLimiter("rules", "Check", remoteAddr, requestPath)
    return redisCheckRule

def limitCreator(ruleName, ruleData):
    request, timeInSeconds = convertRuleToSeconds(ruleData)
    redisCreate = redisLimiter("limits", "Create", ruleName, {"request": f"{request}", "timeInSeconds": f"{timeInSeconds}"})
    return redisCreate

def limitsUpdater(ruleName, existingLimit):
    redisUpdate = redisLimiter("limits", "Update", ruleName, existingLimit)
    return redisUpdate
    
def limitsChecker(ruleName, ruleData):
    redisCheckLimit = redisLimiter("limits", "Check", ruleName, ruleData)
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

def setLimits(app, request):
    remoteAddr = request.remote_addr
    if len(request.path.replace(f"/{app}", '')) > 0:
        requestPath = request.path.replace(f"/{app}", '').split("/")[1]
    else:
        requestPath = str(f"/{app}")
    print(f"requestPath: {requestPath}")
    baseRule = rulesChecker(remoteAddr, requestPath)
    ruleName = baseRule.split(":")[0]
    ruleData = baseRule.split(":")[1]
    print(baseRule)
    if baseRule != ':' or baseRule != '':
        existingLimit = int(limitsChecker(ruleName, ruleData))
        if existingLimit != "":
            if existingLimit > 0:
                limitsUpdater(ruleName, existingLimit)
            elif existingLimit < 0:
                limitCreator(ruleName, ruleData)
            else:
                requestBlock()
        else:
            limitCreator(ruleName, ruleData)
    else:
        pass