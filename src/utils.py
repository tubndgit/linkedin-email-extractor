def handle_api_request(url, params=None, method='GET'):
    import requests

    try:
        if method == 'GET':
            response = requests.get(url, params=params)
        elif method == 'POST':
            response = requests.post(url, json=params)
        else:
            raise ValueError("Unsupported HTTP method: {}".format(method))

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

def log_message(message):
    import logging

    logging.basicConfig(level=logging.INFO)
    logging.info(message)

def format_data(data):
    import json

    return json.dumps(data, indent=4)