from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .api import auth, vendors, projects, emails, ai, dashboard, clients
from .api.auth import oauth_handler
from fastapi.responses import RedirectResponse
from .config.settings import APP_NAME, FRONTEND_DIR
from .database.session import init_db

app = FastAPI(title=APP_NAME) # Reloaded with new AI routes

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database
@app.on_event("startup")
def startup_event():
    init_db()
    # Log all registered routes
    import sys
    print("\n--- Registered Routes ---")
    for route in app.routes:
        print(f"Path: {route.path}")
    print("------------------------\n")
    sys.stdout.flush()

# Register Routers
app.include_router(auth.router, prefix="/api/auth")
app.include_router(vendors.router, prefix="/api/vendors")
app.include_router(projects.router, prefix="/api/projects")
app.include_router(emails.router, prefix="/api/emails")
app.include_router(ai.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(clients.router, prefix="/api/clients")

# --- Legacy OAuth Callbacks (to match whitelisted URIs) ---
@app.get("/gmail/oauth/callback")
def legacy_gmail_callback(code: str):
    print(f"DEBUG: [Legacy Auth] Received Gmail Callback with code: {code[:10]}...")
    if oauth_handler.exchange_google_code(code):
        print("DEBUG: [Legacy Auth] Google authentication successful.")
        return RedirectResponse(url="/")
    print("ERROR: [Legacy Auth] Google authentication failed.")
    return RedirectResponse(url="/?error=google_auth_failed")

@app.get("/oauth/callback")
def legacy_outlook_callback(code: str):
    print(f"DEBUG: [Legacy Auth] Received Outlook Callback with code: {code[:10]}...")
    if oauth_handler.exchange_outlook_code(code):
        print("DEBUG: [Legacy Auth] Outlook authentication successful.")
        return RedirectResponse(url="/")
    print("ERROR: [Legacy Auth] Outlook authentication failed.")
    return RedirectResponse(url="/?error=outlook_auth_failed")

# Serve Frontend (Catch-all)
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("procurement_agent.backend.main:app", host="0.0.0.0", port=5001, reload=True)
