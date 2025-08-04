# -----------------------------
# IMPORTING LIBRARIES
# -----------------------------

import os
import requests
from dotenv import load_dotenv
from langsmith import traceable
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re

import warnings
warnings.filterwarnings("ignore")

### Getting Path of current file
import os
import sys
from pathlib import Path

path = Path(os.path.dirname(os.getcwd()))
path = str(path)
sys.path.insert(1, path)


# -----------------------------
# SETTING UP API KEYS 
# -----------------------------

load_dotenv(dotenv_path=f"{path}/config/nvidia_token.env")

MODEL = "mistralai/mistral-nemotron"
TOKEN = os.getenv("MISTRAL_API_KEY")


# -----------------------------
# SETUP PROMPT
# -----------------------------

PROMPT_MSG = """You are an expert email classification system. Your task is to analyze the provided email and classify it into one of the three categories below. Your response must be **only** the category name and nothing else.

### **Categories**

**1. JOB**
Classify an email as `JOB` if it concerns the status of a specific job application. Recipient of the mail will be informed about the status of their application. This includes notifications that a candidate has:
*   Successfully applied for a job (only application confirmation).
*   Been invited for an assessment (online or offline).
*   Been shortlisted for a position.
*   Been invited to an interview (online or offline).
*   Been rejected for a position.

**2. MEET**
Classify an email as `MEET` if the sender is requesting to schedule an **online meeting**.
*   **Crucial Condition:** The request must be for an online/virtual meeting, NOT an in-person meeting.

**3. OTHER**
Classify an email as `OTHER` if it does not fit into the `JOB` or `MEET` categories. This includes, but is not limited to:
*   General job-related discussions that are not about application status (e.g., networking, asking about a role, advertisements or requesting for an interview).
*   Requests for an in-person or face-to-face meeting.
*   Newsletters, marketing emails, personal correspondence, etc.

**Important Rules:**
* If an email mentions a "meeting" but does not specify whether it is virtual or in-person, classify it as an online meeting.
* Any Job interview online meeting request must be classified as `JOB` category only.
* Only classify an email as JOB if it communicates a completed action related to the application status (e.g., application received, interview invitation, rejected, job offered). Do NOT classify emails with ongoing or vague updates (e.g., "Your application is incomplete") as JOB.
* If the email indicates that the application is incomplete or encourages the candidate to complete the incomplete application, classify it as OTHER.


### **Output Format**

Your answer must be one of these three words exactly, with no additional text:
*   JOB
*   MEET
*   OTHER"""

# -----------------------------
# CLASSIFICATION FUNCTIONS
# -----------------------------

def classify_email(email_content: str, examples=None):
    """
    Classify emails using an NVIDIA LLM with optional few-shot examples.

    Args:
        email_content (str): Email text to classify.

    Returns:
        str: Cleaned classification result (only capital letters).
    """

    # Build few-shot messages
    messages = []

    # Add few-shot examples if provided
    if examples:
        for ex in examples:
            messages.append(("user", ex["email"]))
            messages.append(("assistant", ex["label"]))

    # Add the actual email to classify
    messages.append((
        "user",
        f"""{{email_content}}\n\n{PROMPT_MSG}"""
    ))

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages(messages)

    # Use the NVIDIA LLM via LangChain
    llm = ChatNVIDIA(
        model=MODEL,
        api_key=TOKEN,
        temperature=0.2,
        max_tokens=4096,
        streaming=False
    )

    # Define chain
    chain = prompt | llm | StrOutputParser()

    # Run it
    result = chain.invoke({"email_content": email_content})

    # Extract only capital letters (JOB, MEET, OTHER)
    clean_result = re.sub(r'[^A-Z]+', '', result)

    final_result = is_result_valid_category(clean_result)
    return final_result


# -----------------------------
# CLASSIFICATION FALLBACK
# -----------------------------

def is_result_valid_category(result):
    if(result not in ["JOB", "MEET", "OTHER"]):
        return "OTHER"
    else:
        return result