class HunterIOClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.hunter.io/v2"

    def generate_email(self, first_name, last_name, domain):
        url = f"{self.base_url}/email-finder?first_name={first_name}&last_name={last_name}&domain={domain}&api_key={self.api_key}"
        response = self._make_request(url)
        return response

    def _make_request(self, url):
        import requests
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to Hunter IO API: {e}")
            return None