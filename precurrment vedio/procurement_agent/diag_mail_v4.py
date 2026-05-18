import sys, os, json, requests
sys.path.insert(0, '.')
from backend.auth_handler import OAuthHandler

def run_diagnostic():
    try:
        auth = OAuthHandler()
        token, email_user = auth.get_token_details('gmail')
        
        print(f'--- Diagnostic v4 (Gmail API) ---')
        
        if not token:
            print('No Gmail OAuth token.')
            return

        print('Fetching messages via Gmail Web API...')
        url = 'https://gmail.googleapis.com/gmail/v1/users/me/messages'
        params = {'maxResults': 5, 'q': 'label:INBOX'}
        headers = {'Authorization': f'Bearer {token}'}
        
        resp = requests.get(url, params=params, headers=headers)
        if resp.ok:
            data = resp.json()
            messages = data.get('messages', [])
            print(f'SUCCESS: Found {len(messages)} messages via API.')
            
            for m in messages:
                m_id = m['id']
                # Fetch full message
                m_resp = requests.get(f'{url}/{m_id}', headers=headers)
                if m_resp.ok:
                    details = m_resp.json()
                    headers_list = details.get('payload', {}).get('headers', [])
                    subject = next((h['value'] for h in headers_list if h['name'].lower() == 'subject'), '(No Subject)')
                    print(f' - [{m_id}] Subject: {subject}')
                else:
                    print(f' - [{m_id}] Error fetching details')
        else:
            print(f'FAILED: Gmail API error: {resp.status_code} {resp.text}')

    except Exception as e:
        print(f'CRITICAL Error: {e}')

if __name__ == '__main__':
    run_diagnostic()
