# -----------------------------
# IMPORTING LIBRARIES
# -----------------------------

import argparse
from read_email import *
from langgraph_flow import *
from dotenv import load_dotenv
from assign_email_label import *
from read_thread import *

# -----------------------------
# SET UP ENVIRONMENT VARIABLES
# -----------------------------


load_dotenv(dotenv_path=f"{path}/config/config.env")
EMAIL = os.getenv("EMAIL_ID")


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def invoke_graph(id, mail_details, graph, label_map):
        email = f"Subject: {mail_details['subject']}\n\n{mail_details['body']}"
        result = graph.invoke({"email": email, "email_sent_on": mail_details["date"], "sender_email": mail_details["sender"], "message_id": id, "thread_id": mail_details["thread_id"]})

        if(result["is_both_job_and_meet"]):
                assign_label_to_email(id, f'Job Update/{label_map[result["job_details"]["application_status"]]}')
                assign_label_to_email(mail_details["thread_id"], "Meet Request")

        elif(result["classification"]=="JOB"):
            assign_label_to_email(id, f'Job Update/{label_map[result["job_details"]["application_status"]]}')

        elif(result["classification"]=="MEET"):
            assign_label_to_email(mail_details["thread_id"], "Meet Request")

        return result

# -----------------------------
# EXECUTE FLOW
# -----------------------------

def main():

    label_map = {"application incomplete":"Application Incomplete",
                 "applied":"Applied",
                 "assessment":"Assessment",
                 "interview":"Interview",
                 "job offered":"Offer Made",
                 "rejected":"Rejected",
                 "withdrawn":"Withdrawn",
                 "other":"Other"}
    
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
    # email = f"sender email: {mail_details['sender']}" + '\n' + mail_details['subject'] + '\n' + mail_details['body']
    print(mail_details)
    if(mail_details["thread_id"] == mail_details["id"]):
        print("Single email in thread")

        result = invoke_graph(id, mail_details, graph, label_map)

        return result
    
    else:
        thread_mail_details = get_email_by_id(mail_details["thread_id"])
        thread_content = get_and_display_cleaned_thread(mail_details["thread_id"])
        print(f"\n\n{thread_mail_details}")

        if('Label_4718307430553739191' in thread_mail_details['labels']):
            print("Thread already labelled as Meet Request")
            assign_label_to_email(id, "Meet Request")
            
            notify_user({"email": thread_content, "email_sent_on": mail_details["date"], "sender_email": mail_details["sender"], "message_id": id, "thread_id": mail_details["thread_id"], "meet_request_details": {"request_sent_by": thread_mail_details['sender']}})

        
        else:
             
            result = invoke_graph(id, mail_details, graph, label_map)
            return result


if __name__ == "__main__":
    main()
