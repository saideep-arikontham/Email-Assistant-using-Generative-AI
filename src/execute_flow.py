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

    label_map = {"application incomplete":"Application Incomplete",
                 "applied":"Applied",
                 "assessment":"Job Assessment",
                 "interview":"Interview Update",
                 "job offered":"Offer Made",
                 "rejected":"Rejected",
                 "withdrawn":"Withdrawn",
                 "other":"Other Update"}
    
    parser = argparse.ArgumentParser(description="Print the provided ID.")
    parser.add_argument("id", help="The ID to be printed")
    args = parser.parse_args()

    # Get ID from command line argument
    id = args.id

    # Call the function with the provided ID to get email details
    mail_details = get_email_by_id(id)

    # Build langgraph
    graph = build_graph()

    # Invoke the graph
    if(mail_details["sender"] == EMAIL):
        # Indicates that the email is from me, no need to process it
        print("Email is from me, no need to process.")
        return
    else:
        # email = f"sender email: {mail_details['sender']}" + '\n' + mail_details['subject'] + '\n' + mail_details['body']
        email = mail_details['subject'] + '\n' + mail_details['body']
        result = graph.invoke({"email": email, "email_sent_on": mail_details["date"], "sender_email": mail_details["sender"]})

        print(result)
        if(result["is_both_job_and_meet"]):
                assign_label_to_email(id, f'Job Interview/{label_map[result["job_details"]["application_status"]]}')

        elif(result["classification"]=="JOB"):
            assign_label_to_email(id, f'Job Update/{label_map[result["job_details"]["application_status"]]}')

        elif(result["classification"]=="MEET"):
            assign_label_to_email(id, "Meet Request")

        return result


if __name__ == "__main__":
    main()
