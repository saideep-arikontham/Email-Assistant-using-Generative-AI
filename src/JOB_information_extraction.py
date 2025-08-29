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
FALLBACK_MODEL = "moonshotai/kimi-k2-instruct"
TOKEN = os.getenv("NVIDIA_API_KEY")


# -----------------------------
# SETUP PROMPT
# -----------------------------

INFO_EXTRACTION_PROMPT = """**Task Description:**
    You are an expert at extracting structured information from emails.
    Your task is to analyze the following email and extract details about a job application.
    Please read the email carefully and identify the required fields.

    **Output Format:**
    Provide the output as a single line of pipe-delimited (`|`) text. Do not include any explanatory text before or after the result.
    The fields must be in the following exact order:
    `company_name|job_role|job_id|application_status|sent_by`
    Use `unknown` for any optional fields that are not present in the email.

    **Field Definitions:**
    * `company_name`: The name of the company that sent the application status email. This is a required field.
    * `job_role`: The specific job title or role mentioned in the email (e.g., "Software Engineer", "Product Manager"). If not specified, use null.
    * `job_id`: The unique identifier for the job posting. If not specified, use null.
    * `application_status`: The current status of the application. Choose one of the following options:
        -   `applied`: The application has been successfully submitted and received.
        -   `assessment`: The candidate is asked to complete a test or assessment.
        -   `interview`: The candidate is invited for an interview (phone, video, or in-person).
        -   `job offered`: The candidate has been offered the job.
        -   `rejected`: The company has decided not to move forward with the application.
        -   `withdrawn`: The candidate has withdrawn their application.
        -   `application incomplete`: The application is missing information and needs action.
        -   `other`: The status does not fit into any of the above categories.
    * `sent_by`: The name of the person, team, or system that sent the email (e.g., "Jane Doe", "The Google Recruitment Team", "no-reply@greenhouse.io").

    **Few-Shot Examples:**

    ---
    **Example Email 1:**
    Subject: Your application for Software Engineer at Innovate Inc.

    Hi Alex,

    Thank you for your interest in the Software Engineer (ID: SWE-123) position at Innovate Inc. We have received your application and are currently reviewing it. We will get back to you soon.

    Best,
    The Innovate Inc. Hiring Team

    **Example Pipe-Delimited Output 1:**
    Innovate Inc.|Software Engineer|SWE-123|applied|The Innovate Inc. Hiring Team
    ---
    **Example Email 2:**
    Subject: Update on your application

    Dear Jordan,

    Thank you for applying to Nebula Corp. After careful consideration, we have decided not to move forward with your candidacy at this time. We wish you the best in your job search.

    Sincerely,
    Nebula Corp. Recruiting

    **Example Pipe-Delimited Output 2:**
    Nebula Corp.|unknown|unknown|rejected|Nebula Corp. Recruiting"""

# -----------------------------
# INFORMATION EXTRACTION FUNCTIONS
# -----------------------------

def prompt_llm_for_info_extraction(model, token, email_content: str, examples: list = None):
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
        f"""{INFO_EXTRACTION_PROMPT}\n\n EMAIL TO ANALYZE: {{email_content}} \n\n PIPE-DELIMITED OUTPUT:"""
    ))

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages(messages)

    # Use the NVIDIA LLM via LangChain
    llm = ChatNVIDIA(
        model=MODEL,
        api_key=TOKEN,
        temperature=0.0,
        top_p=1.0,
        max_tokens=4096,
        streaming=False
    )

    # Define chain
    chain = prompt | llm | StrOutputParser()

    # Run it
    result = chain.invoke({"email_content": email_content})
    return result.split("|")


def extract_JOB_info(email_content, examples=None):
        
        result = prompt_llm_for_info_extraction(MODEL, TOKEN, email_content, examples)

        final_result = is_valid_result(result, email_content, examples)
        return final_result


# -----------------------------
# INFORMATION EXTRACTION FALLBACK
# -----------------------------

def is_valid_result(result, email_content, examples):

    if len(result) != 5: #If the result does not contain exactly four values, implement a fallback
        print("--FALLBACK INITIATED - JOB INFO EXTRACTION--")
        fallback_result = prompt_llm_for_info_extraction(FALLBACK_MODEL, TOKEN, email_content, examples)
        
        if(len(fallback_result) != 5):
            return [str(fallback_result), str(result), "Error", "Error", "Error"]
        return [str(result), "Error", "Error", "Error", "Error"]

    
    if (result[3] not in ["application incomplete", "applied", "assessment", "interview", "job offered", "rejected", "withdrawn", "other"]):
        result[3] = "other"
        return result
    
    else:
        return result
    

