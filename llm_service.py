"""
LLM integration — Groq API for fast inference
"""

import json
import os
import requests
from typing import Optional

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Fallback: Ollama (commented out, but available if needed)
# OLLAMA_API = "http://host.docker.internal:11434/api/generate"
# OLLAMA_MODEL = "llama2"

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Optional[dict]:
    """
    Call Groq LLM with structured JSON output.
    
    Args:
        system_prompt: System instructions
        user_prompt: User query with context
        temperature: Lower = more deterministic (good for factual answers)
    
    Returns:
        Parsed JSON response or None on error
    """
    
    # Check if API key is configured
    if not GROQ_API_KEY or GROQ_API_KEY == "":
        print("Error: GROQ_API_KEY no está configurada. Por favor, establece la variable de entorno.")
        return {
            "respuesta": "Error: La API key de Groq no está configurada. Por favor, configura GROQ_API_KEY en tu archivo .env",
            "citas": [],
            "informacion_insuficiente": True,
            "confianza": 0.0,
            "error": "Missing API key"
        }
    
    try:
        # Prepare the message
        full_prompt = f"{system_prompt}\n\nUser Query:\n{user_prompt}"
        
        # Call Groq API
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": 1024,
            "top_p": 1.0
        }
        
        response = requests.post(
            GROQ_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract message content
        if "choices" in result and len(result["choices"]) > 0:
            result_text = result["choices"][0]["message"]["content"]
        else:
            result_text = ""
        
        # Try to parse JSON from response
        try:
            # Extract JSON from the response (may have text before/after)
            start_idx = result_text.find("{")
            end_idx = result_text.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = result_text[start_idx:end_idx]
                try:
                    result = json.loads(json_str)
                    # Ensure all required fields exist
                    if "respuesta" in result:
                        # Validate and normalize response structure
                        return {
                            "respuesta": str(result.get("respuesta", "")).strip(),
                            "citas": result.get("citas", []) if isinstance(result.get("citas"), list) else [],
                            "informacion_insuficiente": bool(result.get("informacion_insuficiente", False)),
                            "confianza": float(result.get("confianza", 0.5)) if result.get("confianza") else 0.5
                        }
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
        except Exception:
            pass
        
        # If not valid JSON, create structured response from text
        # Clean the text - remove any JSON artifacts
        cleaned_text = result_text.strip()
        
        # Remove stray JSON if it leaked into the text
        if cleaned_text.startswith("{") and cleaned_text.endswith("}"):
            cleaned_text = cleaned_text[cleaned_text.find("}")+1:].strip()
        
        if not cleaned_text or cleaned_text.lower() == "undefined" or cleaned_text == "null":
            cleaned_text = "No se pudo generar una respuesta válida. Por favor, intenta con otra pregunta."
        
        return {
            "respuesta": cleaned_text,
            "citas": [],
            "informacion_insuficiente": False,
            "confianza": 0.5
        }
        
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP de Groq: {e.response.status_code}")
        return {
            "respuesta": f"Error de API (HTTP {e.response.status_code}): No se pudo conectar a Groq.",
            "citas": [],
            "informacion_insuficiente": True,
            "confianza": 0.0,
            "error": f"HTTP {e.response.status_code}"
        }
    except requests.exceptions.ConnectionError:
        print("Error: No se puede conectar a la API de Groq.")
        return {
            "respuesta": "Error: No se puede conectar a la API de Groq. Verifica tu conexión a internet.",
            "citas": [],
            "informacion_insuficiente": True,
            "confianza": 0.0,
            "error": "Connection error"
        }
    except Exception as e:
        print(f"Error llamando a Groq: {e}")
        return {
            "respuesta": f"Error al consultar modelo: {str(e)}",
            "citas": [],
            "informacion_insuficiente": True,
            "confianza": 0.0,
            "error": str(e)
        }


def validate_citations(llm_response: dict, available_doc_ids: list[str]) -> dict:
    """
    Verify that all cited documents are in the context provided to LLM.
    
    Args:
        llm_response: Response from LLM with 'citas' field
        available_doc_ids: List of document IDs passed as context
    
    Returns:
        Dict with validation results
    """
    cited_ids = llm_response.get("citas", [])
    
    # Check each cited ID exists in context
    invalid_citations = []
    for cite_id in cited_ids:
        if cite_id not in available_doc_ids:
            invalid_citations.append(cite_id)
    
    is_valid = len(invalid_citations) == 0
    
    return {
        "is_valid": is_valid,
        "invalid_citations": invalid_citations,
        "total_cited": len(cited_ids),
        "total_available": len(available_doc_ids)
    }


# =============================================================================
# OLLAMA FALLBACK (Commented out - uncomment to use local Ollama instead)
# =============================================================================
"""
def call_ollama(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Optional[dict]:
    '''
    Call Ollama LLM with structured JSON output (LOCAL FALLBACK).
    
    Args:
        system_prompt: System instructions
        user_prompt: User query with context
        temperature: Lower = more deterministic (good for factual answers)
    
    Returns:
        Parsed JSON response or None on error
    '''
    OLLAMA_API = "http://host.docker.internal:11434/api/generate"
    OLLAMA_MODEL = "llama2"
    
    try:
        full_prompt = f"{system_prompt}\\n\\nUser Query:\\n{user_prompt}"
        
        response = requests.post(
            OLLAMA_API,
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False,
                "temperature": temperature
            },
            timeout=60
        )
        
        response.raise_for_status()
        result_text = response.json()["response"]
        
        # Parse JSON from response
        try:
            start_idx = result_text.find("{")
            end_idx = result_text.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = result_text[start_idx:end_idx]
                result = json.loads(json_str)
                if "respuesta" in result:
                    return result
        except (json.JSONDecodeError, ValueError):
            pass
        
        cleaned_text = result_text.strip()
        if not cleaned_text or cleaned_text.lower() == "undefined" or cleaned_text == "null":
            cleaned_text = "No se pudo generar una respuesta válida. Por favor, intenta con otra pregunta."
        
        return {
            "respuesta": cleaned_text,
            "citas": [],
            "informacion_insuficiente": False,
            "confianza": 0.5
        }
        
    except requests.exceptions.ConnectionError:
        return {
            "respuesta": "Error: No se puede conectar a Ollama. ¿Está Ollama ejecutándose en tu máquina?",
            "citas": [],
            "informacion_insuficiente": True,
            "confianza": 0.0,
            "error": "Connection error"
        }
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return {
            "respuesta": f"Error al consultar modelo: {str(e)}",
            "citas": [],
            "informacion_insuficiente": True,
            "confianza": 0.0,
            "error": str(e)
        }
"""
