"""
LLM integration — Ollama API for local inference
"""

import json
import requests
from typing import Optional

# Ollama API endpoint (runs on host machine, accessible via host.docker.internal on Docker Desktop)
OLLAMA_API = "http://host.docker.internal:11434/api/generate"
MODEL = "llama2"  # Using llama2 (commonly available in Ollama)

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Optional[dict]:
    """
    Call Ollama LLM with structured JSON output.
    
    Args:
        system_prompt: System instructions
        user_prompt: User query with context
        temperature: Lower = more deterministic (good for factual answers)
    
    Returns:
        Parsed JSON response or None on error
    """
    try:
        # Combine prompts
        full_prompt = f"{system_prompt}\n\nUser Query:\n{user_prompt}"
        
        # Call Ollama
        response = requests.post(
            OLLAMA_API,
            json={
                "model": MODEL,
                "prompt": full_prompt,
                "stream": False,
                "temperature": temperature
            },
            timeout=60
        )
        
        response.raise_for_status()
        result_text = response.json()["response"]
        
        # Try to parse JSON from response
        try:
            # Extract JSON from the response (may have text before/after)
            start_idx = result_text.find("{")
            end_idx = result_text.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = result_text[start_idx:end_idx]
                result = json.loads(json_str)
                # Ensure all required fields exist
                if "respuesta" in result:
                    return result
        except (json.JSONDecodeError, ValueError):
            pass
        
        # If not valid JSON, create structured response from text
        # Clean the text
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
