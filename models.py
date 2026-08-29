from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, Table, DateTime, Column, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from database import Base

# Pivot table for many-to-many relationship between Document and ElementoRBPS
documento_elemento_rbps = Table(
    "documento_elemento_rbps",
    Base.metadata,
    Column("documento_id", Integer, ForeignKey("documentos.id"), primary_key=True),
    Column("elemento_rbps_id", Integer, ForeignKey("elementos_rbps.id"), primary_key=True),
)

class ElementoRBPS(Base):
    """RBPS framework: 4 pillars, 20 elements"""
    __tablename__ = "elementos_rbps"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    pilar: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "I. Compromiso", "II. Comprender", etc.
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    documentos: Mapped[list["Documento"]] = relationship(
        "Documento",
        secondary=documento_elemento_rbps,
        back_populates="elementos_rbps",
    )

    def __repr__(self):
        return f"<ElementoRBPS {self.nombre}>"


class TipoDocumento(Base):
    """Document types: Informe de Incidente, Procedimiento, HAZOP, LOPA, MOC, Norma"""
    __tablename__ = "tipos_documento"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    documentos: Mapped[list["Documento"]] = relationship("Documento", back_populates="tipo")

    def __repr__(self):
        return f"<TipoDocumento {self.nombre}>"


class Documento(Base):
    """Core table: 33 documents from the library"""
    __tablename__ = "documentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_biblioteca: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)  # A1, P3, H1, L2, M4, etc.
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    autor: Mapped[str] = mapped_column(String(200), nullable=False)
    empresa: Mapped[str] = mapped_column(String(200), nullable=False)
    fecha: Mapped[str] = mapped_column(String(20), nullable=True)  # "2007", "N/D", etc.
    
    tipo_id: Mapped[int] = mapped_column(ForeignKey("tipos_documento.id"))
    tipo: Mapped[TipoDocumento] = relationship("TipoDocumento", back_populates="documentos")
    
    elemento_rbps_principal_id: Mapped[int | None] = mapped_column(ForeignKey("elementos_rbps.id"), nullable=True)
    elemento_rbps_principal: Mapped[ElementoRBPS | None] = relationship(
        "ElementoRBPS",
        foreign_keys=[elemento_rbps_principal_id],
    )
    
    palabras_clave: Mapped[str | None] = mapped_column(Text, nullable=True)  # Comma-separated
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    grupo_origen: Mapped[str | None] = mapped_column(String(100), nullable=True)  # "Accidentes (CSB)", "Procedimientos/Normas", etc.
    
    # Many-to-many relationship with RBPS elements (secondary elements)
    elementos_rbps: Mapped[list[ElementoRBPS]] = relationship(
        "ElementoRBPS",
        secondary=documento_elemento_rbps,
        back_populates="documentos",
    )
    
    # Relationships for document linking (H1↔L1, etc.)
    documentos_relacionados_desde: Mapped[list["DocumentoRelacionado"]] = relationship(
        "DocumentoRelacionado",
        foreign_keys="DocumentoRelacionado.documento_origen_id",
        back_populates="documento_origen",
    )
    documentos_relacionados_hacia: Mapped[list["DocumentoRelacionado"]] = relationship(
        "DocumentoRelacionado",
        foreign_keys="DocumentoRelacionado.documento_destino_id",
        back_populates="documento_destino",
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_documento_id_biblioteca", "id_biblioteca"),
        Index("idx_documento_tipo_id", "tipo_id"),
        Index("idx_documento_elemento_rbps_principal_id", "elemento_rbps_principal_id"),
    )

    def __repr__(self):
        return f"<Documento {self.id_biblioteca}: {self.titulo}>"


class DocumentoRelacionado(Base):
    """Links between related documents (e.g., H1↔L1, M1→H1, M1→L1)"""
    __tablename__ = "documentos_relacionados"

    id: Mapped[int] = mapped_column(primary_key=True)
    documento_origen_id: Mapped[int] = mapped_column(ForeignKey("documentos.id"), nullable=False)
    documento_destino_id: Mapped[int] = mapped_column(ForeignKey("documentos.id"), nullable=False)
    tipo_relacion: Mapped[str] = mapped_column(String(50), nullable=False)  # "cuantifica", "se relaciona", "derivado de", etc.
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    documento_origen: Mapped[Documento] = relationship(
        "Documento",
        foreign_keys=[documento_origen_id],
        back_populates="documentos_relacionados_desde",
    )
    documento_destino: Mapped[Documento] = relationship(
        "Documento",
        foreign_keys=[documento_destino_id],
        back_populates="documentos_relacionados_hacia",
    )

    def __repr__(self):
        return f"<DocumentoRelacionado {self.documento_origen_id} -{self.tipo_relacion}-> {self.documento_destino_id}>"
