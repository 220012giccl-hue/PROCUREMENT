"""
Context Resolver Agent — PRD v2.1
==================================
Given an incoming email (sender + body), this agent determines which
Topic (project) it belongs to by:
  1. Looking up the sender in contacts.contact_emails (PostgreSQL ARRAY)
  2. Fetching all active Topics for that contact
  3. Calling the LLM to score which topic best matches the email content

Returns a dict:
  {"status": "researching", "topic_id": 12, "confidence": 0.92, "reason": "..."}
  {"status": "triage",      "topic_id": None, "confidence": 0.0,  "reason": "..."}

DO NOT MODIFY existing agents. This file is standalone.
"""
import json
import logging
import os
import requests
from config.database import SessionLocal
from database.models import Contact, Topic
from config.prompts import CONTEXT_RESOLVER_PROMPT
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Confidence threshold from PRD v2.1 Section 8 (Rule 7)
CONFIDENCE_THRESHOLD = 0.85


def resolve(sender_email: str, email_body: str) -> dict:
    """
    Main entry point. Call this with the sender's email and the email body.
    Returns a routing decision dict.
    """
    db = SessionLocal()
    try:
        # ── Step 1: Find contact by sender email (PostgreSQL ARRAY lookup) ──
        contact = db.execute(
            text("SELECT * FROM contacts WHERE :email = ANY(contact_emails) LIMIT 1"),
            {"email": sender_email}
        ).fetchone()

        if not contact:
            logger.info(f"[ContextResolver] Unknown sender: {sender_email} → triage")
            return {
                "status": "triage",
                "topic_id": None,
                "confidence": 0.0,
                "reason": f"Sender {sender_email} not found in any contact record."
            }

        contact_id = contact.id

        # ── Step 2: Fetch all active Topics for this contact ──
        topics = db.query(Topic).filter(
            Topic.contact_id == contact_id,
            Topic.status == "ACTIVE"
        ).all()

        if not topics:
            logger.info(f"[ContextResolver] No active topics for contact_id={contact_id} → triage")
            return {
                "status": "triage",
                "topic_id": None,
                "confidence": 0.0,
                "reason": f"Contact found ({contact.contact_name}) but has no active projects."
            }

        # ── Step 3: Build topic list string for LLM ──
        topic_list_str = "\n".join([
            f"- ID: {t.id} | Name: {t.topic_name} | "
            f"Site: {getattr(t, 'site_address', 'N/A') or 'N/A'} | "
            f"Ref: {t.topic_reference or 'N/A'}"
            for t in topics
        ])

        # ── Step 4: Call LLM ──
        llm_result = _call_llm(email_body, topic_list_str)

        if not llm_result:
            return {
                "status": "triage",
                "topic_id": None,
                "confidence": 0.0,
                "reason": "LLM call failed or returned invalid response."
            }

        topic_id   = llm_result.get("topic_id")
        confidence = float(llm_result.get("confidence", 0.0))
        reason     = llm_result.get("reason", "")

        # ── Step 5: Route based on confidence threshold ──
        if confidence >= CONFIDENCE_THRESHOLD and topic_id:
            logger.info(f"[ContextResolver] Assigned topic_id={topic_id} (conf={confidence:.2f})")
            return {
                "status":     "researching",
                "topic_id":   topic_id,
                "confidence": confidence,
                "reason":     reason
            }
        else:
            logger.info(f"[ContextResolver] Low confidence {confidence:.2f} → triage")
            return {
                "status":     "triage",
                "topic_id":   topic_id,   # best guess, may be None
                "confidence": confidence,
                "reason":     reason
            }

    except Exception as e:
        logger.error(f"[ContextResolver] Error: {e}")
        return {
            "status":     "triage",
            "topic_id":   None,
            "confidence": 0.0,
            "reason":     f"Internal resolver error: {str(e)}"
        }
    finally:
        db.close()


def _call_llm(email_body: str, topic_list: str) -> dict | None:
    """
    Sends the prompt to OpenRouter (same LLM provider used by existing agents).
    Returns parsed JSON dict or None on failure.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model   = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    url     = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1")

    if not api_key:
        logger.error("[ContextResolver] OPENROUTER_API_KEY not set")
        return None

    prompt = CONTEXT_RESOLVER_PROMPT.format(
        email_body=email_body[:3000],   # limit to avoid token overflow
        topic_list=topic_list
    )

    try:
        resp = requests.post(
            f"{url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json"
            },
            json={
                "model":    model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200
            },
            timeout=30
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        return json.loads(content)

    except (json.JSONDecodeError, KeyError, requests.RequestException) as e:
        logger.error(f"[ContextResolver] LLM call failed: {e}")
        return None
