class NeverBounceClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.neverbounce.com/v4"

    def verify_email(self, email):
        endpoint = f"{self.base_url}/single/check"
        params = {
            "key": self.api_key,
            "email": email
        }
        response = requests.get(endpoint, params=params)
        return response.json() if response.status_code == 200 else None