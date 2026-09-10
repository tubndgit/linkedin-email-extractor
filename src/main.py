from linkedin_extractor import LinkedInExtractor
from hunterio_client import HunterIOClient
from neverbounce_client import NeverBounceClient
from anymailfinder_client import AnyMailFinderClient
import yaml

def main():
    with open('config/config.yaml', 'r') as config_file:
        config = yaml.safe_load(config_file)

    linkedin_extractor = LinkedInExtractor(config['linkedin'])
    names_and_domains = linkedin_extractor.extract_names_and_domains()

    hunter_client = HunterIOClient(config['hunterio'])
    emails = []
    for name, domain in names_and_domains:
        email = hunter_client.generate_email(name, domain)
        emails.append(email)

    neverbounce_client = NeverBounceClient(config['neverbounce'])
    verified_emails = []
    for email in emails:
        if neverbounce_client.verify_email(email):
            verified_emails.append(email)

    anymailfinder_client = AnyMailFinderClient(config['anymailfinder'])
    additional_emails = []
    for name in names_and_domains:
        additional_emails.extend(anymailfinder_client.find_additional_emails(name))

    print("Generated Emails:", emails)
    print("Verified Emails:", verified_emails)
    print("Additional Emails:", additional_emails)

if __name__ == "__main__":
    main()