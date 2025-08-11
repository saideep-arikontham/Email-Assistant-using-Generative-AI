# -----------------------------
# IMPORTING LIBRARIES
# -----------------------------


from typing_extensions import TypedDict
from typing import Literal

from langgraph.graph import StateGraph, START, END
import json

from email_classification import *
from JOB_information_extraction import *
from tracker_updation import *


# -----------------------------
# LANGGRAPH STATE CLASS
# -----------------------------

class TypedDictState(TypedDict):
    state: str
    email: str
    classification: Literal["JOB", "MEET", "OTHER"]
    job_details: dict
    tracker_update: Literal["Successful", "Failed"]
    meet_request_details: dict
    meet_details: dict
    meet_link_sent: Literal["Successful", "Failed"]
    is_both_meet_and_job: bool


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
        return {"classification": classification, "is_both_meet_and_job": True}
    else:
        return {"classification": classification, "is_both_meet_and_job":False}


def route_after_classification(state: TypedDictState) -> Literal["JOB", "MEET", "OTHER"]:
    """
    Routes to the correct path based on the email classification stored in the state.
    """
    print(f"Routing to: {state['classification']}")
    return state["classification"]


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

    company_name, job_title, job_id, application_status = extract_JOB_info(email)

    return {"job_details": {"company_name": company_name, "job_title": job_title, "job_id": job_id, "application_status":application_status}, "state": "Job details extracted"}

def update_tracker(state: TypedDictState):
    print("This function updated the tracker with extracted job details")
    job_details = state["job_details"]
    updates_df = pd.DataFrame([job_details], index=[0])
    upsert_applications("test_tracker", updates_df)
    
    return {"tracker_update": "Successful", "state": "Tracker update successful"}


# -----------------------------
# MEET SCHEDULING FLOW
# -----------------------------


def MEET(state: TypedDictState) -> dict:
    """A placeholder node representing the online_meet check step."""
    print("---IN ONLINE MEET PATH---")
    return {}

def online_meet_tracking_allowed(state: TypedDictState):
    print("User allowed Meet scheduler, flow triggered")
    return {"state": "User allowed Meet scheduler, flow triggered"}

def online_meet_tracking_denied(state: TypedDictState):
    print("User denied Meet scheduler, Ending flow")
    return {"state": "User denied Meet scheduler, Ending flow"}

def identify_meet_timings(state: TypedDictState):
    print("This function reads the email to extract online meet requested date, time, duration")
    return {"meet_request_details": {"requested_by": "johndoe@gmail.com", "date": "2025-07-13", "time": "9:00", "duration": "00:30"}, "state": "meeting request details extracted"}

def create_meet(state: TypedDictState):
    print("This function is to create online meet based on identified details")
    return {"meet_details": {"meet_link": "abcd link"}, "state": "meet link created"}

def send_meet_link(state: TypedDictState):
    print("This function is to draft and send email including meet link")
    return {"meet_link_sent": "Successful", "state": "meet link sent"}


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
    graph_builder.add_node("update_tracker", update_tracker)
    
    graph_builder.add_node("identify_meet_timings", identify_meet_timings)
    graph_builder.add_node("create_meet", create_meet)
    graph_builder.add_node("send_meet_link", send_meet_link)
    
    # Graph Edges
    graph_builder.add_edge(START, "email_classification")
    
    
    graph_builder.add_conditional_edges("email_classification", route_after_classification)
    
    graph_builder.add_edge("JOB", "identify_job_details")
    graph_builder.add_edge("identify_job_details", "update_tracker")
    graph_builder.add_edge("update_tracker", END)
    
    graph_builder.add_edge("MEET", "identify_meet_timings")
    graph_builder.add_edge("identify_meet_timings", "create_meet")
    graph_builder.add_edge("create_meet", "send_meet_link")
    graph_builder.add_edge("send_meet_link", END)
    
    graph_builder.add_edge("OTHER", END)

    graph = graph_builder.compile()
    return graph