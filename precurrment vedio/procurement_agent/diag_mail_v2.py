import sys, os, imaplib, base64, json, requests
sys.path.insert(0, '.')
from backend.auth_handler import OAuthHandler
from backend.config import GMAIL_HOST, GMAIL_USER, GMAIL_PASSWORD

def run_diagnostic():
    try:
        auth = OAuthHandler()
        token, email_user = auth.get_token_details('gmail')
        user = email_user or GMAIL_USER
        
        print(f'--- Diagnostic for {user} ---')
        
        # 1. Verify token via Google API
        if token:
            print(f'Verifying token with Google UserInfo API...')
            try:
                resp = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', 
                                   headers={'Authorization': f'Bearer {token}'})
                if resp.ok:
                    info = resp.json()
                    print(f'SUCCESS: Token is VALID for {info.get("email")}')
                else:
                    print(f'FAILED: Token verification failed: {resp.status_code} {resp.text}')
            except Exception as e:
                print(f'Error verifying token: {e}')
        
        # 2. Test IMAP with different XOAUTH2 formats
        if token:
            print('\nTesting IMAP XOAUTH2 with format 1 (user=...)...')
            try:
                mail = imaplib.IMAP4_SSL(GMAIL_HOST, timeout=15)
                # Standard format
                auth_string = f"user={user}\x01auth=Bearer {token}\x01\x01"
                auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
                
                # Try authenticate
                print(f'Sending AUTH XOAUTH2 for {user}...')
                # We return the b64 string. imaplib's authenticate sends it.
                mail.authenticate('XOAUTH2', lambda x: auth_b64)
                print('SUCCESS: IMAP XOAUTH2 connected!')
                mail.logout()
            except Exception as e:
                print(f'FAILED: format 1 error: {e}')

        # 3. Test Password Login again (carefully)
        print('\nTesting Password Login (GMAIL_PASSWORD)...')
        try:
            mail = imaplib.IMAP4_SSL(GMAIL_HOST, timeout=15)
            mail.login(user, GMAIL_PASSWORD)
            print('SUCCESS: Password login worked!')
            mail.logout()
        except Exception as e:
            print(f'FAILED: Password login error: {e}')

    except Exception as e:
        print(f'CRITICAL Error: {e}')

if __name__ == '__main__':
    run_diagnostic()
