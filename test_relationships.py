#!/usr/bin/env python3
"""
Verification: document linking works correctly
- H1 ↔ L1 (HAZOP ↔ LOPA quantification)
- M1 → H1, L1 (MOC based on analysis)
- M1 → P3 (MOC applies Chevron policy)
"""

import urllib.request, json

def test_relationship(doc_id, expected_related, description):
    """Test that a document has expected related documents."""
    try:
        url = f"http://localhost:8000/documentos/{doc_id}/relacionados/"
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        
        found = [r['id_biblioteca'] for r in data['relaciona_con']]
        relationships = [r for r in data['relaciona_con']]
        
        print(f"\n{description}:")
        print(f"  {doc_id} relates to: {', '.join(found)}")
        for rel in relationships:
            print(f"    - {rel['id_biblioteca']}: {rel['tipo_relacion']}")
        
        for expected_doc in expected_related:
            if expected_doc in found:
                print(f"    ✓ {expected_doc} found")
            else:
                print(f"    ✗ {expected_doc} NOT found (ERROR)")
        
        return all(exp in found for exp in expected_related)
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

print("=" * 60)
print("Testing Document Relationships")
print("=" * 60)

results = [
    test_relationship("H1", ["L1"], "H1 (HAZOP) should relate to L1 (LOPA)"),
    test_relationship("L1", [], "L1 (LOPA) - incoming relationship from H1"),
    test_relationship("M1", ["H1", "L1", "P3"], "M1 (MOC) should relate to H1, L1, P3"),
    test_relationship("H2", ["L2"], "H2 (HAZOP) should relate to L2 (LOPA)"),
    test_relationship("H3", ["L3"], "H3 (HAZOP) should relate to L3 (LOPA)"),
    test_relationship("H4", ["L4"], "H4 (HAZOP) should relate to L4 (LOPA)"),
    test_relationship("M2", ["P14"], "M2 (MOC) should apply P14 policy"),
]

print("\n" + "=" * 60)
passed = sum(results)
total = len(results)
print(f"Results: {passed}/{total} relationship checks passed")

if passed == total:
    print("✓ All document linking tests PASSED")
else:
    print(f"✗ {total - passed} test(s) FAILED")
