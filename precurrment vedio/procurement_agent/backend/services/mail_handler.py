import imaplib
import email
import smtplib
import requests
import base64
import json
import os
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config.settings import (
    GMAIL_HOST, GMAIL_USER, GMAIL_PASSWORD, 
    OUTLOOK_HOST, OUTLOOK_USER, OUTLOOK_PASSWORD, EMAILS_FILE
)

class MailHandler:
    def fetch_emails(self, provider="gmail", token=None, email_address=None):
        print(f"DEBUG: [MailHandler] Fetching emails for {provider} ({email_address or 'Unknown user'})")
        if provider == "gmail" and token:
            return self._fetch_with_gmail_api(token)
        elif provider in ["outlook", "gmail"]:
            return self._fetch_with_imap(provider, email_address)
        return []

    def _fetch_with_gmail_api(self, token):
        try:
            print("DEBUG: [MailHandler] Starting Gmail API fetch sequence...")
            url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, params={"maxResults": 10})
            
            if not response.ok:
                print(f"ERROR: [MailHandler] Gmail API error: {response.status_code} - {response.text}")
                return None
            
            emails = []
            messages = response.json().get('messages', [])
            print(f"DEBUG: [MailHandler] Found {len(messages)} message candidates")
            
            for msg_summary in messages:
                msg_id = msg_summary['id']
                msg_resp = requests.get(f"{url}/{msg_id}", headers=headers, params={"format": "full"})
                if not msg_resp.ok: continue
                
                msg_data = msg_resp.json()
                headers_list = msg_data.get('payload', {}).get('headers', [])
                
                subject = next((h['value'] for h in headers_list if h['name'].lower() == 'subject'), 'No Subject')
                sender = next((h['value'] for h in headers_list if h['name'].lower() == 'from'), 'Unknown Sender')
                snippet = msg_data.get('snippet', '')
                
                try:
                    safe_subject = (subject or "")[:30].encode('ascii', 'ignore').decode()
                    print(f"DEBUG: [MailHandler] Processed message ID {msg_id}: {safe_subject}...")
                except:
                    print(f"DEBUG: [MailHandler] Processed message ID {msg_id}")
                
                emails.append({
                    "id": msg_id,
                    "subject": subject,
                    "sender": sender,
                    "snippet": snippet,
                    "body": snippet, # Simplified for now
                    "provider": "gmail"
                })
            return emails
        except Exception as e:
            print(f"ERROR: [MailHandler] Gmail API exception: {e}")
            return None

    def _fetch_with_imap(self, provider, user_email):
        try:
            host = GMAIL_HOST if provider == "gmail" else OUTLOOK_HOST
            password = GMAIL_PASSWORD if provider == "gmail" else OUTLOOK_PASSWORD
            
            print(f"DEBUG: [MailHandler] Connecting to IMAP {host} for {user_email or 'Default User'}")
            mail = imaplib.IMAP4_SSL(host)
            
            # Use provided user or default from config
            target_user = user_email or (GMAIL_USER if provider == "gmail" else OUTLOOK_USER)
            mail.login(target_user, password)
            
            print(f"DEBUG: [MailHandler] Login successful for {target_user}")
            mail.select("INBOX")
            
            status, ids_data = mail.search(None, 'ALL')
            ids = ids_data[0].split()[-10:] # Last 10
            print(f"DEBUG: [MailHandler] Found {len(ids)} emails via IMAP")
            
            emails = []
            for m_id in ids:
                status, data = mail.fetch(m_id, '(RFC822)')
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                subject = decode_header(msg['Subject'])[0][0]
                if isinstance(subject, bytes): subject = subject.decode()
                
                sender = msg['From']
                safe_subject = subject[:30].encode('ascii', 'ignore').decode()
                print(f"DEBUG: [MailHandler] IMAP Message: {safe_subject}...")
                
                emails.append({
                    "id": m_id.decode(),
                    "subject": subject,
                    "sender": sender,
                    "body": "See original for full content",
                    "provider": provider
                })
                
            mail.logout()
            return emails
        except Exception as e:
            print(f"ERROR: [MailHandler] IMAP Login/Fetch failed for {provider} ({target_user}): {e}")
            if "LOGIN failed" in str(e):
                print(f"TIP: Please check if the password for {target_user} is correct. For Gmail/Outlook, you likely need a 16-character 'App Password' if 2FA is enabled.")
            return None

    def mark_as_read(self, provider, message_id, token=None, email_address=None):
        """Marks an email as read on the server."""
        print(f"DEBUG: [MailHandler] Marking {message_id} as READ on {provider}")
        try:
            if provider == "gmail" and token:
                url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/batchModify"
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                data = {"removeLabelIds": ["UNREAD"]}
                requests.post(url, headers=headers, json=data)
            elif provider in ["outlook", "gmail"]:
                host = GMAIL_HOST if provider == "gmail" else OUTLOOK_HOST
                password = GMAIL_PASSWORD if provider == "gmail" else OUTLOOK_PASSWORD
                user = email_address or (GMAIL_USER if provider == "gmail" else OUTLOOK_USER)
                
                mail = imaplib.IMAP4_SSL(host)
                mail.login(user, password)
                mail.select("INBOX")
                mail.store(message_id, '+FLAGS', '\\Seen')
                mail.logout()
            return True
        except Exception as e:
            print(f"ERROR: [MailHandler] Failed to mark as read: {e}")
            return False

    def create_remote_draft(self, provider, recipient, subject, body, token=None, email_address=None):
        """Syncs a locally created draft to the email provider's Drafts folder."""
        print(f"DEBUG: [MailHandler] Syncing draft to {provider} Drafts folder")
        try:
            if provider == "gmail" and token:
                url = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                
                # Construct MIME message
                message = MIMEMultipart()
                message['to'] = recipient
                message['subject'] = subject
                message.attach(MIMEText(body))
                raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
                
                requests.post(url, headers=headers, json={"message": {"raw": raw}})
            # IMAP APPEND for Outlook Drafts would go here...
            return True
        except Exception as e:
            print(f"ERROR: [MailHandler] Failed to create remote draft: {e}")
            return False
