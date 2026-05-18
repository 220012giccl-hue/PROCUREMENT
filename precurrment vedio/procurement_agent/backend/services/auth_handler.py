import requests
import json
import os
import time
import base64
from ..config.settings import (
    OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET, OUTLOOK_TENANT_ID, OUTLOOK_REDIRECT_URI,
    GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REDIRECT_URI, DATA_DIR
)

class OAuthHandler:
    def __init__(self):
        self.token_file = DATA_DIR / "tokens.json"
        self.tokens = self._load_tokens()

    def _load_tokens(self):
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_tokens(self):
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        with open(self.token_file, 'w') as f:
            json.dump(self.tokens, f, indent=4)

    def _is_token_expired(self, token_data):
        expiry = token_data.get('expiry_timestamp')
        if not expiry:
            return True
        return time.time() >= (expiry - 60)

    def get_google_auth_url(self):
        scopes = "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/userinfo.email"
        return (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={GMAIL_CLIENT_ID}"
            f"&redirect_uri={GMAIL_REDIRECT_URI}"
            "&response_type=code"
            f"&scope={scopes}"
            "&access_type=offline"
            "&prompt=consent"
        )

    def get_outlook_auth_url(self):
        scopes = "offline_access https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.Send https://graph.microsoft.com/IMAP.AccessAsUser.All email openid"
        return (
            f"https://login.microsoftonline.com/{OUTLOOK_TENANT_ID}/oauth2/v2.0/authorize"
            f"?client_id={OUTLOOK_CLIENT_ID}"
            f"&redirect_uri={OUTLOOK_REDIRECT_URI}"
            "&response_type=code"
            f"&scope={scopes}"
            "&response_mode=query"
        )

    def _extract_email_from_id_token(self, id_token, provider='gmail'):
        try:
            parts = id_token.split('.')
            if len(parts) >= 2:
                padding = '=' * (4 - len(parts[1]) % 4)
                payload = json.loads(base64.b64decode(parts[1] + padding))
                if provider == 'gmail':
                    return payload.get('email')
                else:
                    return (
                        payload.get('preferred_username')
                        or payload.get('email')
                        or payload.get('upn')
                    )
        except Exception as e:
            print(f"ERROR: Failed to decode id_token for {provider}: {e}")
        return None

    def exchange_google_code(self, code):
        data = {
            'code': code,
            'client_id': GMAIL_CLIENT_ID,
            'client_secret': GMAIL_CLIENT_SECRET,
            'redirect_uri': GMAIL_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        response = requests.post("https://oauth2.googleapis.com/token", data=data)
        if response.ok:
            token_data = response.json()
            if 'id_token' in token_data:
                token_data['email'] = self._extract_email_from_id_token(token_data['id_token'], 'gmail')
            token_data['expiry_timestamp'] = time.time() + token_data.get('expires_in', 3600)
            self.tokens['gmail'] = token_data
            self._save_tokens()
            return True
        return False

    def exchange_outlook_code(self, code):
        data = {
            'client_id': OUTLOOK_CLIENT_ID,
            'scope': "https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.Send https://graph.microsoft.com/IMAP.AccessAsUser.All email openid offline_access",
            'code': code,
            'redirect_uri': OUTLOOK_REDIRECT_URI,
            'grant_type': 'authorization_code',
            'client_secret': OUTLOOK_CLIENT_SECRET
        }
        url = f"https://login.microsoftonline.com/{OUTLOOK_TENANT_ID}/oauth2/v2.0/token"
        response = requests.post(url, data=data)
        if response.ok:
            token_data = response.json()
            if 'id_token' in token_data:
                token_data['email'] = self._extract_email_from_id_token(token_data['id_token'], 'outlook')
            token_data['expiry_timestamp'] = time.time() + token_data.get('expires_in', 3600)
            self.tokens['outlook'] = token_data
            self._save_tokens()
            return True
        return False

    def get_token_details(self, provider):
        self.tokens = self._load_tokens()
        token_data = self.tokens.get(provider)
        if not token_data:
            return None, None

        refresh_token = token_data.get('refresh_token')
        if self._is_token_expired(token_data) and refresh_token:
            if provider == 'gmail':
                try:
                    data = {
                        'client_id': GMAIL_CLIENT_ID,
                        'client_secret': GMAIL_CLIENT_SECRET,
                        'refresh_token': refresh_token,
                        'grant_type': 'refresh_token'
                    }
                    response = requests.post("https://oauth2.googleapis.com/token", data=data)
                    if response.ok:
                        new_data = response.json()
                        token_data['access_token'] = new_data.get('access_token')
                        token_data['expiry_timestamp'] = time.time() + new_data.get('expires_in', 3600)
                        self.tokens[provider] = token_data
                        self._save_tokens()
                except: pass
            elif provider == 'outlook':
                try:
                    data = {
                        'client_id': OUTLOOK_CLIENT_ID,
                        'client_secret': OUTLOOK_CLIENT_SECRET,
                        'refresh_token': refresh_token,
                        'grant_type': 'refresh_token',
                        'scope': "https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.Send https://graph.microsoft.com/IMAP.AccessAsUser.All email openid offline_access"
                    }
                    url = f"https://login.microsoftonline.com/{OUTLOOK_TENANT_ID}/oauth2/v2.0/token"
                    response = requests.post(url, data=data)
                    if response.ok:
                        new_data = response.json()
                        new_data['email'] = token_data.get('email')
                        new_data['expiry_timestamp'] = time.time() + new_data.get('expires_in', 3600)
                        self.tokens[provider] = new_data
                        self._save_tokens()
                        token_data = new_data
                except: pass

        return token_data.get('access_token'), token_data.get('email')

    def is_connected(self, provider):
        return provider in self.tokens
