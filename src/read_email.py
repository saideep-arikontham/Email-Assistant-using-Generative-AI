# --------------------------
# IMPORTING LIBRARIES
# --------------------------

import os
import sys
import base64
import re
import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# --------------------------
# SETTING UP PATH
# --------------------------

# Getting path of current file's parent directory
path = Path(os.path.dirname(os.getcwd()))
path = str(path)
sys.path.insert(1, path)


# --------------------------
# QUOTED-TEXT STRIPPING HELPERS
# --------------------------

# Common reply/forward markers in plain text
_QUOTE_SPLIT_REGEX = re.compile(
    r"(?im)"                                   # case-insensitive, multiline
    r"(?:^On .+?wrote:\s*$)"                   # Gmail/Apple Mail header
    r"|(?:^From:\s.+$)"                        # From:
    r"|(?:^Sent:\s.+$)"                        # Sent:
    r"|(?:^To:\s.+$)"                          # To:
    r"|(?:^Cc:\s.+$)"                          # Cc:
    r"|(?:^Subject:\s.+$)"                     # Subject:
    r"|(?:^-{2,}\s*Original Message\s*-{2,}\s*$)"  # -----Original Message-----
    r"|(?:^_{6,}\s*$)"                         # ______ separators
)

def _strip_quoted_text_plain(text: str) -> str:
    """Keep everything before the first reply/quote marker in plain text."""
    if not text:
        return ""
    # Keep everything before the first detected reply header/marker
    parts = _QUOTE_SPLIT_REGEX.split(text, maxsplit=1)
    head = parts[0]
    # Trim after a standard signature delimiter if present
    head = re.split(r"(?m)^--\s*$", head)[0]  # RFC 3676 signature marker
    return head.strip()

def _strip_quoted_text_html(html: str) -> str:
    """Remove quoted sections from HTML and return clean plain text."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")

    # Remove Gmail/Yahoo/Outlook quoted blocks and extras
    for sel in [
        "blockquote",
        ".gmail_quote", ".gmail_extra",
        ".yahoo_quoted", ".yahoo_quoted_container",
        ".moz-cite-prefix", ".moz-signature",
        "div[id^='orig-']", "div[id^='reply-']",
    ]:
        for el in soup.select(sel):
            el.decompose()

    # Best-effort: any element whose class contains 'quote'
    for el in soup.select('[class*="quote"]'):
        el.decompose()

    # Extract text and run through plain-text stripper to catch any headers
    text = soup.get_text(separator=" ", strip=True)
    return _strip_quoted_text_plain(text)


# --------------------------
# CORE HELPERS
# --------------------------

def _b64url_decode(s: str) -> str:
    """Decode base64url strings safely to UTF-8 text."""
    if not s:
        return ""
    # Add required padding for base64 if missing
    padding = '=' * (-len(s) % 4)
    try:
        return base64.urlsafe_b64decode(s + padding).decode("utf-8", errors="ignore")
    except Exception:
        return ""

def extract_header(headers, name):
    """Helper to extract a specific header value from Gmail headers."""
    for header in headers:
        if header.get('name', '').lower() == name.lower():
            return header.get('value', '')
    return f"(No {name})"


# --------------------------
# BODY EXTRACTION (TOP-MOST MESSAGE ONLY)
# --------------------------

def get_email_body(payload):
    """
    Extracts the best *top-most* message body from a Gmail payload, stripping
    quoted threads and returning plain text.
    """
    if not payload:
        return "(No content)"

    def decode_part(part):
        data = part.get('body', {}).get('data')
        mime = part.get('mimeType', '')
        return _b64url_decode(data), mime

    # Walk MIME tree:
    # 1) Prefer text/plain
    # 2) Fallback to text/html
    # 3) For multipart/alternative, inspect its children
    stack = [payload]
    text_plain_candidates = []
    text_html_candidates = []

    while stack:
        node = stack.pop()
        mime = node.get('mimeType', '')
        parts = node.get('parts')

        if parts:
            # Depth-first traversal
            stack.extend(reversed(parts))
            continue

        body_text, mtype = decode_part(node)
        if not body_text:
            continue

        if mtype == "text/plain":
            text_plain_candidates.append(body_text)
        elif mtype == "text/html":
            text_html_candidates.append(body_text)

    # Prefer the first plain text candidate, else first HTML candidate
    if text_plain_candidates:
        cleaned = _strip_quoted_text_plain(text_plain_candidates[0])
        return cleaned if cleaned else "(No content)"
    if text_html_candidates:
        cleaned = _strip_quoted_text_html(text_html_candidates[0])
        return cleaned if cleaned else "(No content)"

    # Single-part or unknown type at the root
    if 'body' in payload and payload.get('body', {}).get('data'):
        decoded = _b64url_decode(payload['body']['data'])
        if payload.get('mimeType') == "text/html":
            cleaned = _strip_quoted_text_html(decoded)
        else:
            cleaned = _strip_quoted_text_plain(decoded)
        return cleaned if cleaned else "(No content)"

    return "(No content)"


# --------------------------
# GMAIL READ FUNCTIONS
# --------------------------

def _get_gmail_service():
    creds = Credentials.from_authorized_user_file(f'{path}/config/token.json')
    return build('gmail', 'v1', credentials=creds)

def read_emails(max_results=None):
    """
    Fetch recent emails (default: since yesterday) and return a list of dicts:
    { sender, date, subject, body }
    """
    service = _get_gmail_service()

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    # IMPORTANT: no space after 'after:'
    query = f"after:{yesterday.strftime('%Y/%m/%d')}"

    if max_results is not None:
        results = service.users().messages().list(
            userId='me', maxResults=max_results
        ).execute()
    else:
        results = service.users().messages().list(
            userId='me', q=query
        ).execute()

    messages = results.get('messages', [])
    if not messages:
        print("No emails found.")
        return []

    out = []
    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me', id=msg['id'], format='full'
        ).execute()

        payload = msg_data.get('payload', {})
        headers = payload.get('headers', [])

        sender = extract_header(headers, 'from')
        subject = extract_header(headers, 'subject')
        date = extract_header(headers, 'date')
        body = get_email_body(payload)

        out.append({
            "sender": sender,
            "date": date,
            "subject": subject,
            "body": body
        })

    return out


def get_email_by_id(message_id):
    """
    Fetch a single email by message ID and return:
    { id, threadId, labels, sender, date, subject, body }
    """
    service = _get_gmail_service()

    try:
        msg_data = service.users().messages().get(
            userId='me', id=message_id, format='full'
        ).execute()

        # Extract threadId and labels from the top level of the response
        thread_id = msg_data.get('threadId')
        labels = msg_data.get('labelIds', []) # Get the list of label IDs

        payload = msg_data.get('payload', {})
        headers = payload.get('headers', [])

        sender = extract_header(headers, 'from')
        subject = extract_header(headers, 'subject')
        date = extract_header(headers, 'date')
        body = get_email_body(payload)

        return {
            "id": message_id,
            "thread_id": thread_id,
            "labels": labels, # Add the list of labels to the return dictionary
            "sender": sender,
            "date": date,
            "subject": subject,
            "body": body
        }
    except Exception as e:
        print(f"Error fetching email {message_id}: {e}")
        return None
