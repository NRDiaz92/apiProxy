from flask import Blueprint, request
from configs.proxy import proxy
from configs.limiter import setLimits

routesMeli = Blueprint("routesMeli", __name__)
target_url = 'https://api.mercadolibre.com'

@routesMeli.before_request
def configLimits():
    meliLimits = setLimits("meli", request)
    return meliLimits

@routesMeli.route('/', methods=['GET'], strict_slashes=False)
def rootPath():
    targetUrlWithPath = f'{target_url}'
    apiResponse = proxy(targetUrlWithPath)
    return apiResponse

@routesMeli.route('<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'], strict_slashes=False)
def proxyRoute(subpath=''):
    targetUrlWithPath = f'{target_url}/{subpath}'
    apiResponse = proxy(targetUrlWithPath)
    return apiResponse