import requests
import json
from ..config.settings import LLM_API_URL, LLM_MODEL, OPENAI_API_KEY
from ..config.prompts import (
    GENERAL_AGENT_PROMPT, QUOTATION_EXTRACTION_PROMPT, 
    EMAIL_CLASSIFICATION_PROMPT, PRODUCT_EXTRACTION_PROMPT, RFQ_DRAFT_PROMPT
)

class LLMClient:
    def __init__(self):
        self.api_url = LLM_API_URL
        self.headers = {}
        if OPENAI_API_KEY:
            self.headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
            # OpenRouter recommended headers
            self.headers["HTTP-Referer"] = "http://localhost:5001"
            self.headers["X-Title"] = "Abdex Procurement Agent"
            print(f"DEBUG: [LLM] Initialized with API Key: {OPENAI_API_KEY[:8]}...{OPENAI_API_KEY[-4:]}")
        else:
            print("ERROR: [LLM] NO API KEY FOUND IN SETTINGS!")
    
    def stream_chat(self, messages, timeout=180):
        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "stream": True
        }
        
        # Fix potential double slashes
        base_url = self.api_url.rstrip('/')
        endpoint = f"{base_url}/chat/completions"
        print(f"DEBUG: [LLM] Streaming AI Agent at {endpoint}")
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=timeout, stream=True)
            if response.status_code == 200:
                for line in response.iter_lines():
                    if not line: continue
                    try:
                        line_str = line.decode('utf-8').strip()
                        if not line_str: continue
                        if line_str.startswith("data: "):
                            line_str = line_str[6:].strip()
                        if line_str == "[DONE]": break
                        
                        chunk = json.loads(line_str)
                        # Ollama style response
                        if 'message' in chunk and 'content' in chunk['message']:
                            yield chunk['message']['content']
                        # OpenAI/OpenRouter style response
                        elif 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                        elif 'response' in chunk:
                            yield chunk['response']
                    except Exception as e:
                        print(f"DEBUG: [LLM] Skip line: {e}")
                        continue
            else:
                print(f"ERROR: [LLM] Streaming API Error {response.status_code}")
                yield f"Error: API returned {response.status_code}"
        except Exception as e:
            print(f"ERROR: [LLM] Streaming Exception: {e}")
            yield f"Error: {str(e)}"

    def _call_llm(self, messages, timeout=180, json_mode=False):
        payload = { 
            "model": LLM_MODEL,
            "messages": messages,
            "stream": False
        }
        if json_mode:
            payload["format"] = "json"
        
        # Fix potential double slashes
        base_url = self.api_url.rstrip('/')
        
        # Priority endpoint first
        endpoints = [
            f"{base_url}/chat/completions",
            f"{base_url}/v1/chat/completions"
        ]
        
        for api_endpoint in endpoints:
            try:
                print(f"DEBUG: [LLM] Calling AI Agent at {api_endpoint} (JSON Mode: {json_mode})")
                response = requests.post(api_endpoint, json=payload, headers=self.headers, timeout=timeout)
                if response.status_code == 200:
                    result = response.json()
                    content = ""
                    if 'choices' in result: content = result['choices'][0]['message']['content']
                    elif 'message' in result: content = result['message'].get('content', '')
                    elif 'response' in result: content = result['response']
                    
                    if not content: 
                        print(f"DEBUG: [LLM] Empty response from {api_endpoint}")
                        continue
                    
                    # Robust parsing: if content is string but looks like JSON, try to extract value
                    content = str(content).strip()
                    if not json_mode and (content.startswith('{') and content.endswith('}')):
                        try:
                            parsed = json.loads(content)
                            if isinstance(parsed, dict):
                                # Try common keys first
                                for key in ['content', 'message', 'text', 'response', 'answer', 'result', 'code']:
                                    if key in parsed: return str(parsed[key])
                                # Fallback: return the longest string value
                                string_vals = [str(v) for v in parsed.values() if isinstance(v, (str, int, float))]
                                if string_vals: return max(string_vals, key=len)
                        except: pass
                    
                    print(f"DEBUG: [LLM] Received response: {content[:100]}...")
                    return content
                else:
                    print(f"ERROR: [LLM] API Error {response.status_code}: {response.text}")
            except Exception as e:
                print(f"ERROR: [LLM] Exception calling {api_endpoint}: {e}")
        return None

    def analyze_email(self, email_body):
        messages = [
            {"role": "system", "content": PRODUCT_EXTRACTION_PROMPT},
            {"role": "user", "content": f"Extract products: {email_body}"}
        ]
        content = self._call_llm(messages, json_mode=True)
        if content:
            try:
                if "```" in content: content = content.split("```")[1].replace("json", "")
                return json.loads(content.strip())
            except: pass
        return []

    def analyze_email_classification(self, email_text, attachment_text=None):
        full_text = email_text
        if attachment_text: full_text += f"\n\n[ATTACHMENT CONTENT]:\n{attachment_text}"
        messages = [
            {"role": "system", "content": EMAIL_CLASSIFICATION_PROMPT},
            {"role": "user", "content": full_text}
        ]
        return self._call_llm(messages, json_mode=True) or '{"category": "IRRELEVANT"}'

    def generate_draft(self, vendor_name, vendor_category, products):
        """Generates an RFQ draft. 'products' can be a list or a raw string description."""
        products_display = products
        if isinstance(products, list):
            products_display = "\n".join([f"- {p.get('product', 'Item')}: {p.get('quantity', 'N/A')}" for p in products])
            
        messages = [
            {"role": "system", "content": RFQ_DRAFT_PROMPT.format(vendor_name=vendor_name, vendor_category=vendor_category)},
            {"role": "user", "content": f"Draft professional RFQ for these requirements:\n{products_display}"}
        ]
        return self._call_llm(messages, json_mode=False)

    def improve_draft(self, original_body, instructions):
        messages = [
            {"role": "system", "content": "You are a professional procurement email editor. Improve the following email based on user instructions. Maintain professionalism."},
            {"role": "user", "content": f"Original Email:\n{original_body}\n\nInstructions:\n{instructions}"}
        ]
        return self._call_llm(messages, json_mode=False)

    def extract_quote_from_text(self, text):
        messages = [
            {"role": "system", "content": QUOTATION_EXTRACTION_PROMPT},
            {"role": "user", "content": text}
        ]
        content = self._call_llm(messages, json_mode=True)
        if content:
            try:
                if "```" in content: content = content.split("```")[1].replace("json", "")
                return json.loads(content.strip())
            except: pass
        return []

    def chat(self, messages):
        # General purpose chat using the platform system prompt
        system_msg = {"role": "system", "content": GENERAL_AGENT_PROMPT}
        return self._call_llm([system_msg] + messages, json_mode=False)
