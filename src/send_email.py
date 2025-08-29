# ----------------------------------------
# IMPORTING LIBRARIES
# ----------------------------------------

import os.path
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from email.mime.multipart import MIMEMultipart
import html as _html

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


# ----------------------------------------
# HTML BUILDER
# ----------------------------------------
def build_html_for_notifying(email_sent_date: str, sender_name: str, sender_email: str, email_content: str) -> str:
    """
    Returns a responsive, email-client-friendly HTML string showing:
    - Email sent date
    - Sender name
    - Sender email
    - Email content (plain text -> HTML with <br>)
    """
    def nl2br(s: str) -> str:
        # Escape HTML + convert newlines to <br> for safe rendering
        return _html.escape(s).replace("\n", "<br>")

    sent_date_html = nl2br(email_sent_date)
    sender_name_html = nl2br(sender_name)
    sender_email_html = nl2br(sender_email)
    content_html = nl2br(email_content)

    # Use table-based layout + inline styles for broad email client support
    return f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#f6f8fb;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background:#f6f8fb;">
      <tr>
        <td align="center" style="padding:24px;">
          <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e5e9f2;">
            <!-- Header -->
            <tr>
              <td style="padding:20px 24px;background:#0f62fe;color:#ffffff;font-family:Arial,Helvetica,sans-serif;">
                <div style="font-size:18px;font-weight:700;letter-spacing:.2px;">New Email Notification</div>
                <div style="font-size:12px;opacity:.9;margin-top:4px;">Automated summary</div>
              </td>
            </tr>

            <!-- Meta -->
            <tr>
              <td style="padding:20px 24px;font-family:Arial,Helvetica,sans-serif;color:#111827;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="padding:8px 0;width:140px;color:#6b7280;font-size:12px;">Sent</td>
                    <td style="padding:8px 0;font-size:14px;font-weight:600;">{sent_date_html}</td>
                  </tr>
                  <tr>
                    <td style="padding:8px 0;width:140px;color:#6b7280;font-size:12px;">Sender</td>
                    <td style="padding:8px 0;font-size:14px;font-weight:600;">{sender_name_html}</td>
                  </tr>
                  <tr>
                    <td style="padding:8px 0;width:140px;color:#6b7280;font-size:12px;">Email</td>
                    <td style="padding:8px 0;font-size:14px;">
                      <a href="mailto:{sender_email_html}" style="color:#0f62fe;text-decoration:none;">{sender_email_html}</a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Divider -->
            <tr>
              <td style="padding:0 24px;">
                <hr style="border:none;border-top:1px solid #eef2f7;margin:0;">
              </td>
            </tr>

            <!-- Content -->
            <tr>
              <td style="padding:20px 24px 24px 24px;font-family:Arial,Helvetica,sans-serif;color:#111827;">
                <div style="font-size:13px;color:#6b7280;margin-bottom:8px;">Email Content</div>
                <div style="font-size:15px;line-height:1.6;">
                  {content_html}
                </div>
              </td>
            </tr>

            <!-- Footer -->
            <tr>
              <td style="padding:14px 24px 22px 24px;background:#fafbfe;font-family:Arial,Helvetica,sans-serif;color:#6b7280;font-size:12px;">
                You’re receiving this because you enabled notifications. This is a no-reply message.
              </td>
            </tr>
          </table>

          <div style="font-family:Arial,Helvetica,sans-serif;color:#9ca3af;font-size:11px;margin-top:10px;">
            © {nl2br(email_sent_date)[:4]} – Notification Service
          </div>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


# ----------------------------------------
# SENDER HELPERS (uses your existing token.json path variable)
# ----------------------------------------
def build_html_message(to: str, subject: str, html_body: str, text_fallback: str = "View this message in an HTML-capable client.", sender: str = "me") -> dict:
    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["From"] = sender
    msg["Subject"] = subject
    msg.attach(MIMEText(text_fallback, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}

def send_html_email(to: str, subject: str, html_body: str, text_fallback: str = "View this message in an HTML-capable client."):
    creds = Credentials.from_authorized_user_file(f'{path}/config/token.json')
    service = build('gmail', 'v1', credentials=creds)
    body = build_html_message(to=to, subject=subject, html_body=html_body, text_fallback=text_fallback, sender="me")
    result = service.users().messages().send(userId="me", body=body).execute()
    print(f"✅ Email sent! Message ID: {result.get('id')}")
