# --------------------------
# IMPORTING LIBRARIES
# --------------------------

import os
import sys
import base64
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import datetime

# --------------------------
# SETTING UP PATH
# --------------------------

# Getting Path of current file
path = Path(os.path.dirname(os.getcwd()))
path = str(path)
sys.path.insert(1, path)


# --------------------------
# REQUIRED FUNCTIONS
# --------------------------


def assign_label_to_email(message_id, label_name):
    """Gets the ID of a label by its name."""

    creds = Credentials.from_authorized_user_file(f'{path}/config/token.json')
    service = build('gmail', 'v1', credentials=creds)

    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        for label in labels:
            if label['name'].lower() == label_name.lower():
                add_label_to_email(message_id, label['id'], service)
                return True
        
        print(f"Error: Label '{label_name}' not found.")
        return False
    except Exception as e:
        print(f"An error occurred while getting labels: {e}")
        return None


def add_label_to_email(message_id, label_id, service):
    """Adds a label to a specific email message."""
    try:
        
        body = {
            'addLabelIds': [label_id]
        }
        
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body=body
        ).execute()
        
        print(f"Successfully applied label to message '{message_id}'.")
        return True
    except Exception as e:
        print(f"An error occurred while adding label to message '{message_id}': {e}")
        return False


