import secrets
import logging
import time
from flask import Flask, jsonify, request, g
from views.routesMeli import routesMeli
from views.routesFakeApi import routesFakeApi
from views.routesLogs import routesLogs
from configs.logging import logRequest, logResponse
from configs.limiter import rulesUpdater

logging.getLogger('werkzeug').disabled = True

app = Flask(__name__)
app.register_blueprint(routesMeli, url_prefix="/meli")
app.register_blueprint(routesFakeApi, url_prefix="/fakeApi")
app.register_blueprint(routesLogs, url_prefix="/logs")

@app.before_request
def logBefore():
    g.requestId = secrets.token_hex(4)
    g.timeBefore = time.time()
    appName = request.path.split("/")[1] if "favicon" not in request.path else ''
    logRequest(g.requestId, request, appName)
    
@app.after_request
def logAfter(response):
    appName = request.path.split("/")[1] if "favicon" not in request.path else ''
    g.timeAfter = time.time()
    g.requestTime = round((g.timeAfter - g.timeBefore) * 1000, 2)
    logResponse(g.requestTime, g.requestId, response, appName)
    return response

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404
    
with app.app_context():
    rulesUpdater()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)