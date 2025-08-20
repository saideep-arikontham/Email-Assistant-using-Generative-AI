# -----------------------------
# IMPORTING LIBRARIES
# -----------------------------

import argparse
from read_email import *
from langgraph_flow import *
from dotenv import load_dotenv
from assign_email_label import *

# -----------------------------
# SET UP ENVIRONMENT VARIABLES
# -----------------------------


load_dotenv(dotenv_path=f"{path}/config/config.env")
EMAIL = os.getenv("EMAIL_ID")


# -----------------------------
# EXECUTE FLOW
# -----------------------------

def main():
    
    parser = argparse.ArgumentParser(description="Print the provided ID.")
    parser.add_argument("id", help="The ID to be printed")
    args = parser.parse_args()

    # Get ID from command line argument
    id = args.id

    # Call the function with the provided ID to get email details
    mail_details = get_email_by_id(id)

    return mail_details


if __name__ == "__main__":
    mail_details = main()
    print(mail_details["body"])
