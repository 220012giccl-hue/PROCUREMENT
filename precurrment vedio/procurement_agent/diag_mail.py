import sys, os, imaplib, base64, json
sys.path.insert(0, '.')
from backend.auth_handler import OAuthHandler
from backend.config import GMAIL_HOST, GMAIL_USER, GMAIL_PASSWORD

def run_diagnostic():
    try:
        auth = OAuthHandler()
        token, email_user = auth.get_token_details('gmail')
        user = email_user or GMAIL_USER
        
        print(f'--- Diagnostic for {user} ---')
        
        # 1. Test Password Login
        print('Testing Password Login...')
        try:
            mail = imaplib.IMAP4_SSL(GMAIL_HOST, timeout=20)
            mail.login(user, GMAIL_PASSWORD)
            print('SUCCESS: Password login worked.')
            
            print('Listing labels:')
            status, labels = mail.list()
            if status == 'OK':
                for l in labels:
                    print(f'  {l.decode()}')
            
            status, data = mail.select('INBOX', readonly=True)
            print(f'INBOX Selection: {status}, Data: {data}')
            
            status, ids_data = mail.search(None, 'ALL')
            print(f'Search ALL: {status}, IDs found: {len(ids_data[0].split()) if ids_data[0] else 0}')
            
            mail.logout()
        except Exception as e:
            print(f'FAILED: Password login error: {e}')

        # 2. Test OAuth Login
        if token:
            print('\nTesting OAuth (XOAUTH2) Login...')
            try:
                mail = imaplib.IMAP4_SSL(GMAIL_HOST, timeout=20)
                auth_string = f"user={user}\x01auth=Bearer {token}\x01\x01"
                auth_bytes = base64.b64encode(auth_string.encode('utf-8'))
                mail.authenticate('XOAUTH2', lambda x: auth_bytes)
                print('SUCCESS: OAuth login worked.')
                mail.logout()
            except Exception as e:
                print(f'FAILED: OAuth login error: {e}')
        else:
            print('\nNo OAuth token found.')

    except Exception as e:
        print(f'CRITICAL Error: {e}')

if __name__ == '__main__':
    run_diagnostic()
