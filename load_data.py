#!/usr/bin/env python3
"""
Load library data: 20 RBPS elements, 7 document types, 33 documents + relationships.
"""

import csv
import sys
from sqlalchemy import text
from database import engine, SessionLocal
from models import ElementoRBPS, TipoDocumento, Documento, DocumentoRelacionado

# 20 RBPS elements per CCPS framework
RBPS_ELEMENTOS = [
    # Pilar I: Compromiso con la Seguridad de Procesos
    ("Cultura de Seguridad de Procesos", "I. Compromiso con la Seguridad de Procesos"),
    ("Cumplimiento con Normas", "I. Compromiso con la Seguridad de Procesos"),
    ("Competencia", "I. Compromiso con la Seguridad de Procesos"),
    ("Participación de la Fuerza de Trabajo", "I. Compromiso con la Seguridad de Procesos"),
    ("Vinculación con las Partes Interesadas", "I. Compromiso con la Seguridad de Procesos"),
    
    # Pilar II: Comprender Peligros y Riesgos
    ("Gestión del Conocimiento del Proceso", "II. Comprender Peligros y Riesgos"),
    ("Identificación de Peligros y Análisis de Riesgo (HIRA)", "II. Comprender Peligros y Riesgos"),
    
    # Pilar III: Gestión del Riesgo
    ("Procedimientos Operativos", "III. Gestión del Riesgo"),
    ("Integridad Mecánica y Confiabilidad de Activos", "III. Gestión del Riesgo"),
    ("Gestión del Cambio (MOC)", "III. Gestión del Riesgo"),
    ("Gestión de Emergencias", "III. Gestión del Riesgo"),
    ("Prácticas de Trabajo Seguro", "III. Gestión del Riesgo"),
    ("Preparación Operacional", "III. Gestión del Riesgo"),
    ("Entrenamiento y Aseguramiento del Desempeño", "III. Gestión del Riesgo"),
    ("Auditorías", "III. Gestión del Riesgo"),
    ("Medición y Métricas", "III. Gestión del Riesgo"),
    
    # Pilar IV: Aprender de la Experiencia
    ("Investigación de Incidentes", "IV. Aprender de la Experiencia"),
    ("Revisión de la Gestión y Mejora Continua", "IV. Aprender de la Experiencia"),
]

# Document types
DOCUMENT_TYPES = [
    ("Informe de Incidente", "Investigación de accidentes e incidentes industriales reales"),
    ("Procedimiento", "Procedimientos corporativos internos"),
    ("Norma", "Estándares y normas regulatorias"),
    ("HAZOP", "Estudios HAZOP — Análisis cualitativo de peligros y operabilidad"),
    ("LOPA", "Análisis LOPA — Cuantificación de riesgo y capas de protección"),
    ("MOC", "Gestión del Cambio — Evaluación y gestión de modificaciones"),
    ("Documento Relacionado", "Referencias cruzadas entre documentos"),
]

# Document relationships: (id_origen, id_destino, tipo_relacion)
DOCUMENT_LINKS = [
    ("H1", "L1", "cuantifica"),  # L1 cuantifica el riesgo que H1 identificó
    ("H2", "L2", "cuantifica"),
    ("H3", "L3", "cuantifica"),
    ("H4", "L4", "cuantifica"),
    ("M1", "H1", "se basa en"),    # M1 MOC se basa en H1/L1
    ("M1", "L1", "se basa en"),
    ("M1", "P3", "aplica norma"),  # M1 aplica la política MOC de Chevron
    ("M2", "P14", "aplica norma"), # M2 aplica política de ExxonMobil
    ("M3", "A2", "relacionado"),   # M3 RBI conecta temáticamente con A2
    ("M4", "P14", "aplica norma"), # M4 ejemplifica cambio organizacional de P14
    ("M4", "H5", "misma unidad"),  # M4 y H5 en misma unidad de alquilación
    ("P6", "P15", "siguiente paso"), # P15 es el siguiente paso después de P6
]


def seed_rbps_elements(session):
    """Load 20 RBPS elements."""
    print("\nCargando 20 elementos RBPS...")
    for nombre, pilar in RBPS_ELEMENTOS:
        existing = session.query(ElementoRBPS).filter_by(nombre=nombre).first()
        if not existing:
            elem = ElementoRBPS(nombre=nombre, pilar=pilar)
            session.add(elem)
    session.commit()
    count = session.query(ElementoRBPS).count()
    print(f"  ✓ {count} elementos RBPS en base de datos")


def seed_document_types(session):
    """Load 7 document types."""
    print("\nCargando 7 tipos de documento...")
    for nombre, descripcion in DOCUMENT_TYPES:
        existing = session.query(TipoDocumento).filter_by(nombre=nombre).first()
        if not existing:
            dtype = TipoDocumento(nombre=nombre, descripcion=descripcion)
            session.add(dtype)
    session.commit()
    count = session.query(TipoDocumento).count()
    print(f"  ✓ {count} tipos de documento en base de datos")


def get_element_by_name(session, nombre):
    """Helper: get ElementoRBPS by name."""
    return session.query(ElementoRBPS).filter_by(nombre=nombre).first()


def get_type_by_name(session, nombre):
    """Helper: get TipoDocumento by name."""
    return session.query(TipoDocumento).filter_by(nombre=nombre).first()


def seed_documents(session, csv_path):
    """Load all 33 documents from CSV."""
    print(f"\nCargando documentos desde {csv_path}...")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_biblioteca = row.get('ID', '').strip()
            if not id_biblioteca:
                continue
            
            # Check if already exists
            existing = session.query(Documento).filter_by(id_biblioteca=id_biblioteca).first()
            if existing:
                continue
            
            # Get document type
            tipo_nombre = row.get('Tipo', '').strip()
            tipo = get_type_by_name(session, tipo_nombre)
            if not tipo:
                print(f"  ⚠ Tipo desconocido: {tipo_nombre} para {id_biblioteca}")
                continue
            
            # Get primary RBPS element
            elemento_principal_nombre = row.get('Elemento RBPS (principal)', '').strip()
            elemento_principal = None
            if elemento_principal_nombre:
                elemento_principal = get_element_by_name(session, elemento_principal_nombre)
            
            # Create document
            doc = Documento(
                id_biblioteca=id_biblioteca,
                titulo=row.get('Título', '').strip(),
                autor=row.get('Autor', '').strip(),
                empresa=row.get('Empresa', '').strip(),
                fecha=row.get('Fecha', '').strip() or None,
                tipo=tipo,
                elemento_rbps_principal=elemento_principal,
                palabras_clave=row.get('Palabras clave', '').strip() or None,
                descripcion=row.get('Descripción', '').strip() or None,
                notas=row.get('Notas / advertencias', '').strip() or None,
                grupo_origen=row.get('Grupo de origen', '').strip() or None,
            )
            session.add(doc)
            
            # Handle secondary RBPS elements (many-to-many)
            elementos_secundarios_str = row.get('Elementos RBPS (secundarios)', '').strip()
            if elementos_secundarios_str:
                for elem_nombre in elementos_secundarios_str.split(';'):
                    elem_nombre = elem_nombre.strip()
                    elem = get_element_by_name(session, elem_nombre)
                    if elem and elem not in doc.elementos_rbps:
                        doc.elementos_rbps.append(elem)
    
    session.commit()
    count = session.query(Documento).count()
    print(f"  ✓ {count} documentos en base de datos")


def seed_document_relationships(session):
    """Create document relationships (H1↔L1, MOC→HAZOP, etc.)"""
    print("\nCargando relaciones entre documentos...")
    
    for id_origen, id_destino, tipo_relacion in DOCUMENT_LINKS:
        # Find documents
        doc_origen = session.query(Documento).filter_by(id_biblioteca=id_origen).first()
        doc_destino = session.query(Documento).filter_by(id_biblioteca=id_destino).first()
        
        if not doc_origen or not doc_destino:
            continue
        
        # Check if relationship already exists
        existing = session.query(DocumentoRelacionado).filter_by(
            documento_origen_id=doc_origen.id,
            documento_destino_id=doc_destino.id
        ).first()
        
        if not existing:
            rel = DocumentoRelacionado(
                documento_origen=doc_origen,
                documento_destino=doc_destino,
                tipo_relacion=tipo_relacion
            )
            session.add(rel)
    
    session.commit()
    count = session.query(DocumentoRelacionado).count()
    print(f"  ✓ {count} relaciones entre documentos en base de datos")


def main():
    from models import Base
    
    # Create tables if they don't exist
    print("Inicializando esquema...")
    Base.metadata.create_all(engine)
    print("  ✓ Esquema creado")
    
    session = SessionLocal()
    
    try:
        seed_rbps_elements(session)
        seed_document_types(session)
        seed_documents(session, "biblioteca_data.csv")
        seed_document_relationships(session)
        
        print("\n✓ Carga de datos completada exitosamente")
        
        # Verification
        print("\n--- Resumen ---")
        print(f"Elementos RBPS: {session.query(ElementoRBPS).count()}")
        print(f"Tipos de documento: {session.query(TipoDocumento).count()}")
        print(f"Documentos: {session.query(Documento).count()}")
        print(f"Relaciones: {session.query(DocumentoRelacionado).count()}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        session.rollback()
        return 1
    finally:
        session.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
