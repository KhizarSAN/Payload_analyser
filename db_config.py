from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# Configuration de la connexion à la base MySQL (adapter les infos si besoin)
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'payload_analyser')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Définition des modèles ORM
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255))
    role = Column(String(50), default='user')
    created_at = Column(TIMESTAMP)
    # Relations
    patterns = relationship('Pattern', back_populates='creator')
    analyses = relationship('Analysis', back_populates='user')
    logs = relationship('Log', back_populates='user')

class Pattern(Base):
    __tablename__ = 'patterns'
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    resume = Column(String(255))
    description = Column(Text)
    categorie = Column(String(100))
    criticite = Column(String(50))
    regex = Column(Text)
    exemple_payload = Column(Text)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(TIMESTAMP)
    # Relations
    creator = relationship('User', back_populates='patterns')
    analyses = relationship('Analysis', back_populates='pattern')

class Analysis(Base):
    __tablename__ = 'analyses'
    id = Column(Integer, primary_key=True, index=True)
    payload = Column(Text, nullable=False)
    pattern_id = Column(Integer, ForeignKey('patterns.id'))
    pattern_nom = Column(String(100))
    resume_court = Column(String(255))
    description_faits = Column(Text)
    analyse_technique = Column(Text)
    resultat = Column(String(100))
    justification = Column(Text)
    rapport_complet = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    tags = Column(String(255))
    statut = Column(String(50), default='nouveau')
    # Relations
    user = relationship('User', back_populates='analyses')
    pattern = relationship('Pattern', back_populates='analyses')

class Log(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    created_at = Column(TIMESTAMP)
    # Relations
    user = relationship('User', back_populates='logs')

# Fonction utilitaire pour créer les tables (à utiliser une seule fois)
def init_db():
    Base.metadata.create_all(bind=engine) 