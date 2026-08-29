#!/usr/bin/env python3
"""
Validation set for Proyecto 3 RAG layer.
Tests both in-scope (should have answers) and out-of-scope (should decline) questions.
"""

import urllib.request
import json

BASE_URL = "http://localhost:8000"

VALIDATION_SET = [
    # In-scope: Should find answers in library
    {
        "id": "Q1",
        "pregunta": "¿Qué es HAZOP y cuál es su propósito?",
        "tipo": "in_scope",
        "documento_esperado": ["H1", "P6"],
        "descripcion": "Definición de HAZOP"
    },
    {
        "id": "Q2",
        "pregunta": "¿Cuáles son las 20 elementos del marco RBPS de CCPS?",
        "tipo": "in_scope",
        "documento_esperado": ["P7", "P9"],
        "descripcion": "Marco RBPS completo"
    },
    {
        "id": "Q3",
        "pregunta": "¿Qué pasa si se pierde el agua de enfriamiento en un condensador?",
        "tipo": "in_scope",
        "documento_esperado": ["H4", "L4"],
        "descripcion": "Análisis de falla específico"
    },
    {
        "id": "Q4",
        "pregunta": "Describe los casos de accidentes investigados por el CSB",
        "tipo": "in_scope",
        "documento_esperado": ["A1", "A2", "A3", "A4", "A5", "A6"],
        "descripcion": "Accidentes reales"
    },
    {
        "id": "Q5",
        "pregunta": "¿Cuál es la diferencia entre HAZOP y LOPA?",
        "tipo": "in_scope",
        "documento_esperado": ["H1", "L1", "P6", "P15"],
        "descripcion": "Diferenciación de metodologías"
    },
    {
        "id": "Q6",
        "pregunta": "¿Cuáles son los elementos del Pilar III (Gestión del Riesgo) del marco RBPS?",
        "tipo": "in_scope",
        "documento_esperado": ["P9", "P7"],
        "descripcion": "Estructura del RBPS"
    },
    {
        "id": "Q7",
        "pregunta": "¿Qué es un MOC (Management of Change)?",
        "tipo": "in_scope",
        "documento_esperado": ["P3", "P14", "M1"],
        "descripcion": "Definición de gestión del cambio"
    },
    {
        "id": "Q8",
        "pregunta": "Explica el proceso de respuesta ante emergencias según OSHA",
        "tipo": "in_scope",
        "documento_esperado": ["P4"],
        "descripcion": "Procedimiento de emergencias"
    },
    {
        "id": "Q9",
        "pregunta": "¿Qué es LOTO (bloqueo y etiquetado)?",
        "tipo": "in_scope",
        "documento_esperado": ["P16"],
        "descripcion": "Procedimiento de seguridad"
    },
    {
        "id": "Q10",
        "pregunta": "¿Cuáles son las capas de protección independientes evaluadas en un LOPA?",
        "tipo": "in_scope",
        "documento_esperado": ["L1", "L2", "L3", "L4"],
        "descripcion": "Concepto de IPL"
    },
    
    # Out-of-scope: Should decline gracefully
    {
        "id": "Q11",
        "pregunta": "¿Cuál es la capital de Francia?",
        "tipo": "out_of_scope",
        "documento_esperado": [],
        "descripcion": "Pregunta completamente fuera de dominio"
    },
    {
        "id": "Q12",
        "pregunta": "¿Cómo construyo un reactor nuclear?",
        "tipo": "out_of_scope",
        "documento_esperado": [],
        "descripcion": "Tema de ingeniería no cubierto"
    },
    {
        "id": "Q13",
        "pregunta": "¿Cuáles son los últimos avances en machine learning?",
        "tipo": "out_of_scope",
        "documento_esperado": [],
        "descripcion": "Tema totalmente ajeno a seguridad de procesos"
    },
]


def test_question(pregunta_data: dict) -> dict:
    """Send question to RAG endpoint and check response."""
    try:
        url = f"{BASE_URL}/asistente/preguntar"
        payload = {"pregunta": pregunta_data["pregunta"], "umbral_relevancia": 0.2}
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        # Analyze response
        resultado = {
            "id": pregunta_data["id"],
            "tipo": pregunta_data["tipo"],
            "citas_devueltas": result.get("citas", []),
            "informacion_insuficiente": result.get("informacion_insuficiente", False),
            "confianza": result.get("confianza", 0.0),
            "validacion_citas": result.get("validacion_citas", {}).get("is_valid", False),
            "respuesta_preview": (result.get("respuesta", "")[:100] + "...") if len(result.get("respuesta", "")) > 100 else result.get("respuesta", ""),
        }
        
        # Check correctness
        if pregunta_data["tipo"] == "in_scope":
            # Should have found something
            if resultado["citas_devueltas"] and not resultado["informacion_insuficiente"]:
                resultado["correcto"] = True
                resultado["razon"] = "Encontró documentos relevantes"
            else:
                resultado["correcto"] = False
                resultado["razon"] = "No encontró información que debería estar disponible"
        else:  # out_of_scope
            # Should decline gracefully
            if resultado["informacion_insuficiente"] or not resultado["citas_devueltas"]:
                resultado["correcto"] = True
                resultado["razon"] = "Rechazó gracefully"
            else:
                resultado["correcto"] = False
                resultado["razon"] = "Intentó responder algo que no debería estar en la biblioteca"
        
        resultado["razon"] = resultado.get("razon", "Sin evaluación")
        
        return resultado
        
    except Exception as e:
        return {
            "id": pregunta_data["id"],
            "tipo": pregunta_data["tipo"],
            "error": str(e),
            "correcto": False
        }


def main():
    print("=" * 80)
    print("VALIDATION SET — Proyecto 3 RAG Layer")
    print("=" * 80)
    print(f"\nEjecutando {len(VALIDATION_SET)} preguntas de prueba...\n")
    
    results = []
    for pregunta in VALIDATION_SET:
        print(f"[{pregunta['id']}] ({pregunta['tipo']}) {pregunta['pregunta'][:60]}...", end=" ")
        resultado = test_question(pregunta)
        results.append(resultado)
        
        if resultado.get("correcto"):
            print("✓")
        else:
            print("✗")
        
        if "error" in resultado:
            print(f"  ERROR: {resultado['error']}\n")
    
    # Summary
    print("\n" + "=" * 80)
    print("RESULTADOS FINALES")
    print("=" * 80)
    
    in_scope_correct = sum(1 for r in results if r.get("tipo") == "in_scope" and r.get("correcto"))
    in_scope_total = sum(1 for r in results if r.get("tipo") == "in_scope")
    out_scope_correct = sum(1 for r in results if r.get("tipo") == "out_of_scope" and r.get("correcto"))
    out_scope_total = sum(1 for r in results if r.get("tipo") == "out_of_scope")
    
    print(f"\nPreguntas in-scope (con respuesta esperada): {in_scope_correct}/{in_scope_total}")
    print(f"Preguntas out-of-scope (rechazadas correctamente): {out_scope_correct}/{out_scope_total}")
    print(f"Total correcto: {in_scope_correct + out_scope_correct}/{len(results)}")
    
    # Detailed results
    print("\n" + "-" * 80)
    print("DETALLE")
    print("-" * 80)
    for resultado in results:
        status = "✓" if resultado.get("correcto") else "✗"
        print(f"\n{status} [{resultado['id']}] {resultado['razon']}")
        if resultado.get("error"):
            print(f"  Error: {resultado['error']}")
        else:
            print(f"  Citas: {resultado.get('citas_devueltas', [])}")
            print(f"  Confianza: {resultado.get('confianza', 0.0):.2f}")
            print(f"  Info insuficiente: {resultado.get('informacion_insuficiente', False)}")
    
    print("\n" + "=" * 80)
    if (in_scope_correct + out_scope_correct) == len(results):
        print("✓ TODOS LOS TESTS PASARON")
    else:
        print(f"✗ {len(results) - (in_scope_correct + out_scope_correct)} tests fallaron")
    print("=" * 80)


if __name__ == "__main__":
    main()
