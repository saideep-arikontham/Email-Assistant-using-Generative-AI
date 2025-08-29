#!/usr/bin/env python3
"""
Cleanly print a Gmail thread as a conversation (new content only).

Usage:
  python cleaned_thread.py THREAD_ID
  # or set THREAD_ID env var:
  THREAD_ID=abc123 python cleaned_thread.py

Requirements:
  pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

Setup:
  1) Create a Google Cloud project with Gmail API enabled.
  2) Download OAuth client credentials as credentials.json into this folder.
  3) On first run, a browser will open to authorize; token.json will be saved.
"""

import base64
import os
import re
import sys
from typing import Any, Dict, List, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pathlib import Path

# -----------------------------
# Configuration
# -----------------------------

# Getting path of current file's parent directory
path = Path(os.path.dirname(os.getcwd()))
path = str(path)
sys.path.insert(1, path)


# -----------------------------
# Helpers
# -----------------------------
def extract_header(headers: List[Dict[str, str]], name: str) -> Optional[str]:
    """Extract a specific header value from a list of email headers."""
    return next((h.get("value") for h in headers if h.get("name", "").lower() == name.lower()), None)


def _decode_b64(data: str) -> str:
    """Decode URL-safe base64 to utf-8 string."""
    try:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def get_email_body(payload: Dict[str, Any]) -> str:
    """
    Try hard to extract a human-readable body.

    Preference order:
      - text/plain parts
      - fall back to text/html stripped to text
      - single-part bodies
    """
    # If multipart: walk parts depth-first
    if "parts" in payload:
        # Prefer text/plain
        for part in payload["parts"]:
            mime = part.get("mimeType", "")
            body_data = part.get("body", {}).get("data")
            if mime.startswith("text/plain") and body_data:
                return _decode_b64(body_data)

        # Then try nested parts (e.g., multipart/alternative)
        for part in payload["parts"]:
            sub = get_email_body(part)
            if sub:
                return sub

    # Single-part body
    mime = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")
    if body_data:
        text = _decode_b64(body_data)
        if mime.startswith("text/plain"):
            return text
        # crude HTML -> text fallback
        if mime.startswith("text/html"):
            # extremely light HTML strip
            text = re.sub(r"<(br|BR)\s*/?>", "\n", text)
            text = re.sub(r"<[^>]+>", "", text)
            return text

    return ""


_REPLY_HEADER_RE = re.compile(
    # Matches common "On Tue, Aug 27, 2025 at 12:34 PM Name <email> wrote:" (tolerant)
    r"^On\s(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s\w+\s\d{1,2},\s\d{4}.*?wrote:\s*$",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)

_SIGNATURE_RE = re.compile(
    # Stop at common signature starters; conservative to avoid false positives
    r"(?m)^\s*(--\s?$|Regards,|Best regards,|Best,|Thanks,|Thank you,)\s*$"
)


def _clean_email_body(body: str) -> str:
    """Remove quoted history and typical signatures to keep only the new content."""
    # Cut off everything after a reply header like "On Tue, ... wrote:"
    m = _REPLY_HEADER_RE.search(body)
    if m:
        body = body[: m.start()]

    # Drop quoted lines (starting with '>')
    lines = [ln for ln in body.splitlines() if not ln.strip().startswith(">")]
    body = "\n".join(lines)

    # Trim at common signature indicators (keep content above)
    sig_match = _SIGNATURE_RE.search(body)
    if sig_match:
        body = body[: sig_match.start()]

    # Normalize whitespace
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def clean_and_present_thread(sorted_emails: List[Dict[str, Any]]) -> None:
    """Pretty-print the conversation showing only new content per message."""
    cleaned_result = ""
    for email in sorted_emails:
        sender_full = email.get("sender", "") or ""
        # Extract email between <...> if present
        m = re.search(r"<(.+?)>", sender_full)
        sender_email = m.group(1) if m else sender_full.strip()

        cleaned_body = _clean_email_body(email.get("body", ""))

        if cleaned_body and sender_email:
            cleaned_result += "----------------------\n"
            cleaned_result += sender_email + "\n"
            cleaned_result += cleaned_body + "\n"
    cleaned_result += "----------------------\n"
    return cleaned_result



# -----------------------------
# Gmail API
# -----------------------------
def get_gmail_service():
    creds = Credentials.from_authorized_user_file(f'{path}/config/token.json')
    return build('gmail', 'v1', credentials=creds)


def get_and_display_cleaned_thread(thread_id: str) -> None:
    """Retrieve, sort by internalDate, clean, and print a Gmail thread."""
    service = get_gmail_service()
    thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
    messages = thread.get("messages", [])
    if not messages:
        print(f"No messages found in thread {thread_id}")
        return

    emails_to_sort: List[Dict[str, Any]] = []
    for msg in messages:
        payload = msg.get("payload", {})
        headers = payload.get("headers", [])
        emails_to_sort.append(
            {
                "internalDate": int(msg.get("internalDate", "0")),
                "sender": extract_header(headers, "From"),
                "body": get_email_body(payload),
            }
        )

    sorted_emails = sorted(emails_to_sort, key=lambda e: e["internalDate"])
    return clean_and_present_thread(sorted_emails)