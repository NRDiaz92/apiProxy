from flask import Blueprint
from configs.proxy import proxy

routesFakeApi = Blueprint("routesFakeApi", __name__)
target_url = 'https://fake-json-api.mock.beeceptor.com'

@routesFakeApi.route('/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route(subpath=''):
    target_url_with_path = f'{target_url}/{subpath}'
    apiResponse = proxy(target_url_with_path)
    return apiResponse