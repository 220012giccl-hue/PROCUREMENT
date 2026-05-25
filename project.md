```json
{
  "project_name": "Executive-RFQ-Assistant",
  "description": "A procurement assistant application integrating AI agents, email listeners, and a full frontend UI for processing requests for quotes (RFQs) and managing tenders.",
  "modules": [
    {
      "name": "api",
      "description": "Handles the core backend server, routing, background tasks, and utility functions.",
      "components": [
        "main.py (FastAPI application entry point)",
        "tasks.py (Background tasks execution)",
        "routes/ (API endpoints grouping)",
        "utils/ (Helper functions)"
      ]
    },
    {
      "name": "agents",
      "description": "Contains autonomous AI agents for executing procurement workflows.",
      "components": [
        "executive/ (Executive decision/management agent)",
        "rfq_agent/ (Agent responsible for handling RFQ processes)"
      ]
    },
    {
      "name": "auth",
      "description": "Manages authentication, authorization, session management, and auditing.",
      "components": [
        "audit.py (Auditing and logging)",
        "dependencies.py (FastAPI auth dependencies)",
        "security.py (Security hashes and token validations)",
        "session_manager.py (User session tracking)",
        "user_manager.py (User lifecycle management)"
      ]
    },
    {
      "name": "config",
      "description": "Centralizes configuration files for database, OAuth, environment variables, and AI prompts.",
      "components": [
        "auth_settings.py (Authentication configuration)",
        "database.py (Database configuration)",
        "gmail_oauth_config.py & oauth_config.py (OAuth integration parameters)",
        "prompts.py (System prompts for AI agents)",
        "settings.py (General application settings)"
      ]
    },
    {
      "name": "database",
      "description": "Defines database models, schemas, database connections, and setup scripts.",
      "components": [
        "models.py (ORM Models/Schemas)",
        "connection.py (DB connection pool)",
        "setup_database.py & complete_setup.py (Scripts to initialize the DB)",
        "migrations/ (Database migration scripts)"
      ]
    },
    {
      "name": "integrations",
      "description": "Connects to external systems for data ingestion.",
      "components": [
        "email_listeners/ (Modules to listen to and fetch emails)",
        "file_fetchers/ (Modules to fetch documents and files)"
      ]
    },
    {
      "name": "models",
      "description": "Contains clients and logic for interacting with external AI models.",
      "components": [
        "pixtral_client.py (Client for Pixtral AI model)"
      ]
    },
    {
      "name": "ui",
      "description": "Contains the frontend HTML, CSS, and JS files for the application dashboard.",
      "components": [
        "index.html, admin.html, admin-login.html, rfq.html, tenders.html, etc. (Views)",
        "css/ (Stylesheets)",
        "js/ (Frontend scripts)"
      ]
    },
    {
      "name": "tests",
      "description": "Contains test suites for verifying application logic and integrations.",
      "components": [
        "Various test scripts for backend, database, and agents"
      ]
    },
    {
      "name": "storage & sample_data",
      "description": "Directories used for local file storage and seeded data for testing."
    }
  ],
  "root_scripts": {
    "description": "Various standalone scripts at the root level for testing, migrating, and verifying functionality.",
    "scripts": [
      "run_gmail_oauth.py",
      "run_outlook_oauth.py",
      "refresh_outlook_token.py",
      "check_db.py",
      "check_ollama.py",
      "Dockerfile & docker-compose.yml"
    ]
  }
}
```
