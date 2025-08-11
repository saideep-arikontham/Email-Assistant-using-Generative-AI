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

MODEL = "openai/gpt-oss-120b"
TOKEN = os.getenv("NVIDIA_API_KEY")


# -----------------------------
# SETUP PROMPT
# -----------------------------

INFO_EXTRACTION_PROMPT = """You are an information extraction assistant.  
You will be given the full text of an email regarding a candidate’s job application status.

Your task is to read the email carefully and extract the following details exactly as they appear in the email (or return empty string "" if the detail is missing):

1. Company Name — The company or organization sending the email. This referes to the name of the company that is mentioned in the email and does not necessarily refer to the sender's name. For example, if the email is sent by Amazon talent acquisition team or Amazon career site or Amazon hiring manager, etc., the company name is Amazon.
2. Job Role — The job title or role mentioned in the email.
3. Job ID — The job requisition ID, reference number, or posting number mentioned.
4. Application Status — One of the following categories that best describes the current stage:
   - application incomplete
   - applied
   - assessment
   - interview
   - job offered
   - rejected
   - withdrawn
   - other (if none of the above applies)

### Output format:
<company_name>|<job_role>|<job_id>|<application_status>

Return the extracted information in the format above, with each detail separated by a pipe, without any additional text or metadata. If any detail is not present in the email, return an empty string for that detail (e.g., if the job ID is not mentioned, return <company_name>|<job_role>||<application_status>)."""

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
    return result.split("|")


def extract_JOB_info(email_content, examples=None):
        
        result = prompt_llm_for_info_extraction(email_content, examples)

        final_result = is_valid_result(result)
        return final_result


# -----------------------------
# INFORMATION EXTRACTION FALLBACK
# -----------------------------

def is_valid_result(result):

    if len(result) != 4: #If the result does not contain exactly four values, implement a fallback
        return ["Error", "Error", "Error", "Error"]
    
    if (result[0] == ""):
        return ["Error", "Error", "Error", "Error"]
    
    else:
        return result
    

