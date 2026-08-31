"""
LLM integration — Groq API for fast inference
"""

import json
import os
import requests
from typing import Optional

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")  # Updated to available model
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

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
    if not GROQ_API_KEY or GROQ_API_KEY.startswith("gsk_") == False:
        print("Error: GROQ_API_KEY no está configurada correctamente. Por favor, establece la variable de entorno.")
        return {
            "respuesta": "Error: La API key de Groq no está configurada correctamente. Por favor, configura GROQ_API_KEY en tu archivo .env",
            "citas": [],
            "informacion_insuficiente": True,
            "confianza": 0.0,
            "error": "Missing or invalid API key"
        }
    
    try:
        # Prepare the message
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
        
        print(f"Calling Groq API with model: {GROQ_MODEL}")
        
        response = requests.post(
            GROQ_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        # Check for HTTP errors
        if response.status_code != 200:
            print(f"Groq API error: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 400:
                return {
                    "respuesta": "Error: Solicitud inválida a Groq. Verifica tu configuración.",
                    "citas": [],
                    "informacion_insuficiente": True,
                    "confianza": 0.0,
                    "error": f"HTTP {response.status_code}: Bad Request"
                }
            elif response.status_code == 401:
                return {
                    "respuesta": "Error: Tu API key de Groq es inválida o ha expirado.",
                    "citas": [],
                    "informacion_insuficiente": True,
                    "confianza": 0.0,
                    "error": "HTTP 401: Unauthorized"
                }
            else:
                return {
                    "respuesta": f"Error de API de Groq (HTTP {response.status_code})",
                    "citas": [],
                    "informacion_insuficiente": True,
                    "confianza": 0.0,
                    "error": f"HTTP {response.status_code}"
                }
        
        result = response.json()
        
        # Extract message content
        if "choices" in result and len(result["choices"]) > 0:
            result_text = result["choices"][0]["message"]["content"]
        else:
            result_text = ""
        
        print(f"Groq response received: {len(result_text)} characters")
        
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
