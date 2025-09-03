from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import chromadb
from chromadb.config import Settings as ChromaSettings
import os

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

chroma_client = chromadb.PersistentClient(
    path=settings.CHROMA_PERSIST_DIRECTORY,
    settings=ChromaSettings(anonymized_telemetry=False)
)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    try:
        collection = chroma_client.get_collection(name="recipes")
    except:
        collection = chroma_client.create_collection(
            name="recipes",
            metadata={"hnsw:space": "cosine"}
        )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_chroma_collection():
    return chroma_client.get_collection(name="recipes")