# -----------------------------
# IMPORTING LIBRARIES
# -----------------------------


from typing_extensions import TypedDict
from typing import Literal

from langgraph.graph import StateGraph, START, END
import json

from email_classification import *
from JOB_information_extraction import *
from MEET_information_extraction import *
from tracking import *
from send_email import *
from dotenv import load_dotenv
from read_thread import *


# -----------------------------
# SET UP ENVIRONMENT VARIABLES
# -----------------------------

load_dotenv(dotenv_path=f"{path}/config/config.env")

EMAIL = os.getenv("EMAIL_ID")


# -----------------------------
# LANGGRAPH STATE CLASS
# -----------------------------

class TypedDictState(TypedDict):
    state: str
    message_id: str
    thread_id: str
    email: str
    email_sent_on: str
    sender_email: str
    classification: Literal["JOB", "MEET", "OTHER"]
    job_details: dict
    tracker_update: Literal["Successful", "Failed"]
    meet_request_details: dict
    is_both_job_and_meet: bool


# -----------------------------
# LANGGRAPH FLOW
# -----------------------------

# --------------------------------------
# CLASSIFICATION AND ROUTING FUNCTIONS
# --------------------------------------

def email_classification(state: TypedDictState) -> dict:
    """
    This function reads the email, classifies it, and updates the state.
    """

    print("---CLASSIFYING EMAIL---")
    email = state.get('email')

    result = classify_email(email)
    print(result)
    JOB_flag, MEET_flag, OTHER_flag = result

    if eval(OTHER_flag):
        classification="OTHER"

    elif eval(JOB_flag):
        classification="JOB"
    
    elif eval(MEET_flag):
        classification="MEET"

    if eval(JOB_flag) and eval(MEET_flag):
        return {"classification": classification, "is_both_job_and_meet": True}
    else:
        return {"classification": classification, "is_both_job_and_meet":False}


def route_after_classification(state: TypedDictState) -> Literal["JOB", "MEET", "OTHER"]:
    """
    Routes to the correct path based on the email classification stored in the state.
    """
    print(f"Routing to: {state['classification']}")
    return state["classification"]


def route_after_job_tracker(state: TypedDictState) -> Literal["MEET", "__end__"]:
    """
    Routes to the correct path based on the is_both_job_and_meet flag in the state.
    """
    if state["is_both_job_and_meet"]:
        print("Routing to: MEET path from JOB flow")
        return "MEET"
    else:
        print("Ending flow after job status update")
        return "__end__"



# -----------------------------
# JOB TRACKER FLOW
# -----------------------------


def JOB(state: TypedDictState) -> dict:
    """A placeholder node representing the job_status check step."""
    print("---IN JOB STATUS PATH---")
    return {}

def identify_job_details(state: TypedDictState):
    print("This function reads the email to extract job title, company name and job status")
    email = state["email"]

    company_name, job_title, job_id, application_status, sent_by = extract_JOB_info(email)

    return {"job_details": {"sender_email":state["sender_email"], "company_name": company_name, "job_title": job_title, "job_id": job_id, "application_status":application_status, "sent_by":sent_by, "email_sent_date":state["email_sent_on"]}, "state": "Job details extracted"}

def track_application_status(state: TypedDictState):
    print("This function updated the tracker with extracted job details")
    job_details = state["job_details"]
    updates_df = pd.DataFrame([job_details], index=[0])
    insert_records("test_application_tracker", updates_df)
    print(state)
    return {"tracker_update": "Successful", "state": "Tracker update successful"}


# -----------------------------
# MEET SCHEDULING FLOW
# -----------------------------


def MEET(state: TypedDictState) -> dict:
    """A placeholder node representing the online_meet check step."""
    print("---IN ONLINE MEET PATH---")
    return {}

def identify_meet_details(state: TypedDictState):
    print("This function reads the email to extract online meet requested date, time, duration")

    request_sent_by, requested_date_time, reason_for_meeting = extract_MEET_info(state["email"])

    return {"meet_request_details": {"sender_email":state["sender_email"], "request_sent_by": request_sent_by, "mail_sent_date": state["email_sent_on"], "requested_date_time": requested_date_time, "reason_for_meeting":reason_for_meeting}, "state": "meeting request details extracted"}

def track_meet_requests(state: TypedDictState):
    print("This function is to record the meet details in the tracker")
    meet_request_details = state["meet_request_details"]
    updates_df = pd.DataFrame([meet_request_details], index=[0])
    insert_records("test_meeting_tracker", updates_df)

    return {"state": "meet link sent"}

def notify_user(state: TypedDictState):
    print("This function is to notify the user that this email requires immediate attention")
    ## CODE TO SEND EMAIL TO THE USER ABOUT THIS EMAIL REQUIRING IMMEDIATE ATTENTION
    ## SENDER WILL BE THE SAME AS THE RECEIVER, WHICH IS THE USER.

    email = get_and_display_cleaned_thread(state["thread_id"])
    to = EMAIL
    subject = f"IMPORTANT: Action Required for Meeting Request | {state['message_id']} | {state['thread_id']}"
    message = f"""You got a meeting request email that requires your immediate attention. Below are the details:\nEmail sent date: {state["email_sent_on"]}\nSender name: {state["meet_request_details"]["request_sent_by"]}\n\nEmail content:\n\n{email}"""



    html = build_html_for_notifying(
        email_sent_date=state["email_sent_on"],
        sender_name=state["meet_request_details"]["request_sent_by"],
        sender_email=state["sender_email"],
        email_content=(
            email
        ),
    )

    send_html_email(
        to=to,
        subject=subject,
        html_body=html,
        text_fallback=message
    )


    print(state)
    return {"state": "User notified about the meeting request email"}


# -----------------------------
# OTHER FLOW
# -----------------------------


def OTHER(state: TypedDictState):
    print("---IN OTHER PATH---")
    return {"state": "Other flow triggered"}


# -----------------------------
# BUILDING GRAPH
# -----------------------------


def build_graph():

    # Build the LangGraph
    graph_builder = StateGraph(TypedDictState)
    
    # Graph Nodes
    graph_builder.add_node("email_classification", email_classification)
    graph_builder.add_node("JOB", JOB)
    graph_builder.add_node("MEET", MEET)
    graph_builder.add_node("OTHER", OTHER)
    
    graph_builder.add_node("identify_job_details", identify_job_details)
    graph_builder.add_node("track_application_status", track_application_status)
    
    graph_builder.add_node("identify_meet_details", identify_meet_details)
    graph_builder.add_node("track_meet_requests", track_meet_requests)
    graph_builder.add_node("notify_user", notify_user)
    
    # Graph Edges
    graph_builder.add_edge(START, "email_classification")
    
    
    graph_builder.add_conditional_edges("email_classification", route_after_classification)
    
    graph_builder.add_edge("JOB", "identify_job_details")
    graph_builder.add_edge("identify_job_details", "track_application_status")
    graph_builder.add_conditional_edges(
    "track_application_status",
    route_after_job_tracker,
    {
        "MEET": "MEET",
        "__end__": END
    }
)

    
    graph_builder.add_edge("MEET", "identify_meet_details")
    graph_builder.add_edge("identify_meet_details", "track_meet_requests")
    graph_builder.add_edge("track_meet_requests", "notify_user")
    graph_builder.add_edge("notify_user", END)
    
    graph_builder.add_edge("OTHER", END)

    graph = graph_builder.compile()
    return graph