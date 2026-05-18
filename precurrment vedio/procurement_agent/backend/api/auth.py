from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from ..services.auth_handler import OAuthHandler

router = APIRouter(tags=["Authentication"])

oauth_handler = OAuthHandler()

@router.get("/google/login")
def google_login():
    url = oauth_handler.get_google_auth_url()
    print(f"DEBUG: [Auth] Redirecting to Google Login: {url}")
    return RedirectResponse(url)

@router.get("/google/callback")
def google_callback(code: str):
    print(f"DEBUG: [Auth] Received Google Callback with code: {code[:10]}...")
    if oauth_handler.exchange_google_code(code):
        print("DEBUG: [Auth] Google authentication successful.")
        return RedirectResponse(url="/")
    print("ERROR: [Auth] Google authentication failed.")
    return RedirectResponse(url="/?error=google_auth_failed")

@router.get("/outlook/login")
def outlook_login():
    url = oauth_handler.get_outlook_auth_url()
    print(f"DEBUG: [Auth] Redirecting to Outlook Login: {url}")
    return RedirectResponse(url)

@router.get("/outlook/callback")
def outlook_callback(code: str):
    print(f"DEBUG: [Auth] Received Outlook Callback with code: {code[:10]}...")
    if oauth_handler.exchange_outlook_code(code):
        print("DEBUG: [Auth] Outlook authentication successful.")
        return RedirectResponse(url="/")
    print("ERROR: [Auth] Outlook authentication failed.")
    return RedirectResponse(url="/?error=outlook_auth_failed")

@router.get("/gmail-url")
def get_gmail_url():
    return {"url": oauth_handler.get_google_auth_url()}

@router.get("/outlook-url")
def get_outlook_url():
    return {"url": oauth_handler.get_outlook_auth_url()}

@router.get("/status")
def get_auth_status():
    gmail_token, gmail_email = oauth_handler.get_token_details("gmail")
    outlook_token, outlook_email = oauth_handler.get_token_details("outlook")
    
    return {
        "gmail": {
            "connected": oauth_handler.is_connected("gmail"),
            "email": gmail_email or ""
        },
        "outlook": {
            "connected": oauth_handler.is_connected("outlook"),
            "email": outlook_email or ""
        }
    }
