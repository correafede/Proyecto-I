#!/usr/bin/env python3
import urllib.request, json

endpoints = [
    ("/health", "Health check"),
    ("/estadisticas/", "Statistics"),
    ("/rbps-elementos/", "RBPS Elements"),
    ("/tipos-documento/", "Document Types"),
    ("/documentos/", "All Documents (first 5)"),
    ("/documentos/H1", "Document H1"),
    ("/documentos/L1", "Document L1"),
    ("/documentos/H1/relacionados/", "H1 Related Docs"),
]

base_url = "http://localhost:8000"

for endpoint, description in endpoints:
    try:
        url = base_url + endpoint
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        
        if endpoint == "/estadisticas/":
            print(f"\n{description}:")
            print(f"  Total docs: {data['total_documentos']}")
            print(f"  RBPS elements: {data['total_elementos_rbps']}")
            print(f"  Document types: {data['total_tipos']}")
            print(f"  Relationships: {data['total_relaciones']}")
        elif endpoint == "/documentos/":
            print(f"\n{description}:")
            print(f"  First 3 documents:")
            for doc in data[:3]:
                print(f"    - {doc['id_biblioteca']}: {doc['titulo'][:50]}")
        elif endpoint == "/documentos/H1":
            print(f"\n{description}:")
            print(f"  ID: {data['id_biblioteca']}")
            print(f"  Title: {data['titulo']}")
            print(f"  Type: {data['tipo']['nombre']}")
        elif endpoint == "/documentos/H1/relacionados/":
            print(f"\n{description}:")
            print(f"  Relates to: {len(data['relaciona_con'])} documents")
            for rel in data['relaciona_con']:
                print(f"    - {rel['id_biblioteca']}: {rel['tipo_relacion']}")
        else:
            print(f"\n{description}: OK ({len(str(data))} bytes)")
    except Exception as e:
        print(f"\n{description}: ERROR - {e}")

print("\n✓ API Tests Complete")
