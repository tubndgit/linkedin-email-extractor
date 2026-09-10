class AnyMailFinderClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.anymailfinder.com/v4"

    def find_additional_emails(self, name, domain):
        url = f"{self.base_url}/search"
        params = {
            "name": name,
            "domain": domain,
            "api_key": self.api_key
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('emails', [])
        else:
            response.raise_for_status()