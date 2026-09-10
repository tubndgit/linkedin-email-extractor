# LinkedIn Email Extractor

This project is designed to extract names and domains from LinkedIn Sales Navigator accounts, generate emails using the Hunter IO API, verify emails with the NeverBounce API, and find additional emails using AnyMailFinder.

## Project Structure

```
linkedin-email-extractor
├── src
│   ├── __init__.py
│   ├── linkedin_extractor.py
│   ├── hunterio_client.py
│   ├── neverbounce_client.py
│   ├── anymailfinder_client.py
│   ├── main.py
│   └── utils.py
├── requirements.txt
├── config
│   └── config.yaml
├── tests
│   ├── __init__.py
│   ├── test_linkedin_extractor.py
│   ├── test_hunterio_client.py
│   ├── test_neverbounce_client.py
│   └── test_anymailfinder_client.py
└── README.md
```

## Requirements

- Python 3.x
- Required libraries listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd linkedin-email-extractor
   ```

2. Install the required libraries:
   ```
   pip install -r requirements.txt
   ```

3. Configure the API keys and settings in `config/config.yaml`.

## Usage

To run the application, execute the following command:
```
python src/main.py
```

## Functionality

- **LinkedInExtractor**: Extracts names and domains from LinkedIn Sales Navigator accounts.
- **HunterIOClient**: Generates emails based on names and domains using the Hunter IO API.
- **NeverBounceClient**: Verifies generated emails using the NeverBounce API.
- **AnyMailFinderClient**: Finds additional emails for the given names using the AnyMailFinder API.

## Testing

To run the tests, use the following command:
```
pytest tests/
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.