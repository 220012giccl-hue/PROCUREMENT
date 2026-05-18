import sys, os, imaplib, base64, json, requests
sys.path.insert(0, '.')
from backend.services.auth_handler import OAuthHandler
from backend.config.settings import GMAIL_HOST, GMAIL_USER

def run_diagnostic():
    try:
        auth = OAuthHandler()
        token, email_user = auth.get_token_details('gmail')
        user = email_user or GMAIL_USER
        
        print(f'--- Diagnostic v3 for {user} ---')
        
        print('\nTesting IMAP XOAUTH2 with RAW string (no manual b64)...')
        try:
            mail = imaplib.IMAP4_SSL(GMAIL_HOST, timeout=15)
            # Raw format
            auth_string = f"user={user}\x01auth=Bearer {token}\x01\x01"
            
            print(f'Sending AUTH XOAUTH2 for {user} with raw string...')
            # imaplib should b64 encode this
            mail.authenticate('XOAUTH2', lambda x: auth_string.encode('utf-8'))
            
            print('SUCCESS: IMAP XOAUTH2 connected with raw string!')
            
            print('Selecting INBOX...')
            mail.select('INBOX')
            status, ids_data = mail.search(None, 'ALL')
            print(f'Search ALL: {status}, Total IDs: {len(ids_data[0].split()) if ids_data[0] else 0}')
            
            mail.logout()
        except imaplib.IMAP4.error as e:
            print(f'FAILED with IMAP error: {e}')
        except Exception as e:
            print(f'FAILED with unexpected error: {e}')

    except Exception as e:
        print(f'CRITICAL Error: {e}')

if __name__ == '__main__':
    run_diagnostic()
