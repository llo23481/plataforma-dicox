from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# URL de PostgreSQL (Render te la da después de crear la BD)
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost/dicox')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Estudio(Base):
    __tablename__ = "estudios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_paciente = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    recibo = Column(String, unique=True, nullable=False)
    institucion = Column(String, default="REMadom")
    cliente = Column(String)
    fecha = Column(String)
    importe = Column(String, default="0")
    metodo_pago = Column(String)
    procesado = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now)

class Configuracion(Base):
    __tablename__ = "configuracion"
    
    id = Column(Integer, primary_key=True)
    clave = Column(String, unique=True, nullable=False)
    valor = Column(String, nullable=False)

# Crear tablas (se ejecuta una sola vez)
Base.metadata.create_all(bind=engine)