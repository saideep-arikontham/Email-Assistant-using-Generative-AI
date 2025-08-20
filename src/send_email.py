# ----------------------------------------
# IMPORTING LIBRARIES
# ----------------------------------------

import os.path
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import os
import sys
from pathlib import Path


# ----------------------------------------
# SETTING UP PATH
# ----------------------------------------


path = Path(os.path.dirname(os.getcwd()))
path = str(path)
sys.path.insert(1, path)


# ----------------------------------------
# IMPORTANT FUNCTIONS
# ----------------------------------------


def send_email(to, subject, message_text):
    creds = Credentials.from_authorized_user_file(f'{path}/config/token.json')
    service = build('gmail', 'v1', credentials=creds)

    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = "me"
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    send_message = {'raw': raw_message}

    result = service.users().messages().send(userId="me", body=send_message).execute()
    print(f"✅ Email sent! Message ID: {result['id']}")