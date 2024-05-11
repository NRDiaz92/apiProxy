from flask import jsonify, request
import requests

def proxy(targetUrlWithPath):
    try:
        apiRequest = requests.request(
            method=request.method,
            url=targetUrlWithPath,
            headers={key: value for (key, value) in request.headers if key != 'Host' and key != 'Accept'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False
        )

        apiResponse = jsonify(apiRequest.json())
        apiResponse.status_code = apiRequest.status_code

        return apiResponse

    except Exception as e:
        return jsonify({'error': str(e)}), 500