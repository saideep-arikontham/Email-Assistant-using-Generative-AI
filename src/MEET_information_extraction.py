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
import numpy as np

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

INFO_EXTRACTION_PROMPT = """You are an information extraction assistant.  
You will be given the full text of an email regarding a meeting request. It can be a virtual meeting, in-person meeting, audio/video call, a job interview request, etc.

Your task is to read the email carefully and extract the following details exactly as they appear in the email (or return empty string "" if the detail is missing):

1. Request sent by — The name of the person or body that is requesting the meeting.
2. Requested date and time - The date and time when the meeting is requested to be held. Make sure to return the exact content if specified.
6. Reason for meeting - The reason for meeting if specified in the email. Make sure to summarize the reason in no more than 15 words.

** Important Rule:**
- The output must have exactly 3 values separated by a pipe (|).

### Output format:
<request_sent_by>|<requested_date_time>|<reason_for_meeting>"""

# -----------------------------
# INFORMATION EXTRACTION FUNCTIONS
# -----------------------------

def prompt_llm_for_info_extraction(email_content: str, examples: list = None):
    """
    Extract information from JOB emails using an NVIDIA LLM with optional few-shot examples.

    Args:
        model (str): NVIDIA LLM model name.
        token (str): API key for NVIDIA LLM.
        prompt_msg (str): Classification instruction message.
        email_content (str): Email text to classify.
        examples (list, optional): Few-shot examples in the form 
                                   [{"email": "example email", "label": "JOB"}, ...]

    Returns:
        str: Extracted information result.
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
        f"""{{email_content}}\n\n{INFO_EXTRACTION_PROMPT}"""
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
    return result.strip().split("|")


def extract_MEET_info(email_content, examples=None):
        
        result = prompt_llm_for_info_extraction(email_content, examples)

        final_result = is_meet_result_valid(result)
        return final_result


# -----------------------------
# INFORMATION EXTRACTION FALLBACK
# -----------------------------

def is_meet_result_valid(result):

    if len(result) != 3: #If the result does not contain exactly four values, implement a fallback
        return [str(result), "Error", "Error"]
    
    else:
        return result
    

