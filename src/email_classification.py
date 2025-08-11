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
TOKEN = os.getenv("NVIDIA_API_KEY")


# -----------------------------
# SETUP PROMPT
# -----------------------------

CLASSIFICATION_PROMPT = """You are an expert email class identification system. Your task is to analyze the provided email and identify if the email falls it each category or not. Your response must be **only** the True/False for each category without any additional text or metadata.

### **Categories**

**1. JOB**
Identify an email as `JOB` if it concerns the status of a specific job application. Recipient of the mail will be informed about the status of their application. This includes notifications that a candidate has:
*   Successfully applied/in the process of applying for a job (application confirmation).
*   Been shortlisted for a position.
*   Been invited to an interview or assessment.
*   Been rejected for a position.
*   Job recommendations or suggestions or ads from job boards, recruiters, companies, etc., do not classify as JOB.

**2. MEET**
Identify an email as `MEET` if the sender is requesting to schedule a meeting, virtual or in-person.
*   Can be a virtual meeting via Zoom, Google Meet, Teams, Video call, etc.
*   Can be an in-person meeting at a specific location.
*   Can be an invitation to job interviews, assessments as well.
*   Cannot be classified as MEET unless it is mentioned explicitly in the email. Future steps of a process or a job application having a meeting do not classify as MEET.

**3. OTHER**
Identify an email as `OTHER` only if it does not fit into the `JOB` or `MEET` categories. This includes, but is not limited to:
*   General job-related discussions that are not about application status (e.g., networking, asking about a role, advertisements, job suggestions or requesting for an interview).
*   Newsletters, marketing emails, personal correspondence, etc.

**Important Rules:**
*   An email cannot be identified as any other class if it classifies as OTHER.
*   An email can be identified as either JOB or either MEET or both JOB and MEET.
*   Possible combinations of classes for email are:
    *   JOB, MEET
    *   JOB
    *   MEET
    *   OTHER

### **Output Format**

Your answer must be three True or False values, one for each JOB, MEET and OTHER in this exact order:
<is a JOB>, <is a MEET>, <is OTHER>"""

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
        f"""{{email_content}}\n\n{CLASSIFICATION_PROMPT}"""
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
    clean_result = re.sub(r'[^A-Za-z,]+', '', result)
    split_result = clean_result.split(",")

    final_result = is_valid_result(split_result)
    

    return final_result


# -----------------------------
# CLASSIFICATION FALLBACK
# -----------------------------

def is_valid_result(result):

    if len(result) != 3: #If the result does not contain exactly three flags, return OTHER
        return ["False", "False", "True"] #OTHER

    for i in result:
        if i not in ["True", "False"]:
            return ["False", "False", "True"] #OTHER
    
    if("True" not in result or "False" not in result): #All three flags cant be True or False. Both True and False must exist in the result.
        return ["False", "False", "True"] #OTHER
    
    elif((result[0]=="True" or result[1]=="True") and result[2]=="True"): #If JOB or MEET is True, OTHER must be False
        return ["False", "False", "True"] #OTHER
    
    else:
        return result
    

