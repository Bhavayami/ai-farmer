import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from config import settings
from exceptions import DatabaseException
from logger import logger

Base = declarative_base()

# SQLAlchemy Models
class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    region = Column(String(100), default="Unknown")
    latitude = Column(Float, default=0.0)
    longitude = Column(Float, default=0.0)
    farm_size_acres = Column(Float, default=0.0)
    soil_ph = Column(Float, default=6.5)
    soil_nitrogen = Column(Float, default=45.0)  # mg/kg
    soil_phosphorus = Column(Float, default=18.0) # mg/kg
    soil_potassium = Column(Float, default=120.0) # mg/kg
    soil_moisture = Column(Float, default=30.0)   # percentage
    primary_crops = Column(String(200), default="Rice, Wheat")
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    session_id = Column(String(100), primary_key=True)
    farmer_id = Column(Integer, ForeignKey("farmer_profiles.id"), nullable=True)
    chat_history = Column(Text, default="[]")  # JSON encoded list of messages
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CacheEntry(Base):
    __tablename__ = "cache_entries"
    
    cache_key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)  # JSON encoded cached content
    expires_at = Column(DateTime, nullable=False)

class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False)
    farmer_id = Column(Integer, nullable=True)
    topic = Column(String(100), nullable=False)  # e.g., "crop_planning", "pest_control"
    input_query = Column(Text, nullable=False)
    consultation_log = Column(Text, nullable=False)  # JSON detailing sub-agent traces
    final_recommendation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database Connection Pool Setup
class DatabaseManager:
    def __init__(self, db_url: str = settings.sql_database_url):
        self.engine = create_engine(
            db_url, 
            connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.init_db()
        
    def init_db(self):
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database schemas initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseException("Database initialization error", {"error": str(e)})

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

db_manager = DatabaseManager()

# Repository Implementations
class FarmerProfileRepository:
    @staticmethod
    def get_profile(db: Session, profile_id: int) -> Optional[FarmerProfile]:
        return db.query(FarmerProfile).filter(FarmerProfile.id == profile_id).first()
        
    @staticmethod
    def get_latest_profile(db: Session) -> Optional[FarmerProfile]:
        return db.query(FarmerProfile).order_by(FarmerProfile.id.desc()).first()

    @staticmethod
    def save_profile(db: Session, profile_data: Dict[str, Any]) -> FarmerProfile:
        try:
            profile_id = profile_data.get("id")
            if profile_id:
                profile = db.query(FarmerProfile).filter(FarmerProfile.id == profile_id).first()
                if profile:
                    for key, val in profile_data.items():
                        setattr(profile, key, val)
                    db.commit()
                    db.refresh(profile)
                    return profile
            
            profile = FarmerProfile(**profile_data)
            db.add(profile)
            db.commit()
            db.refresh(profile)
            return profile
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving farmer profile: {e}")
            raise DatabaseException("Failed to save farmer profile", {"error": str(e)})

class ChatSessionRepository:
    @staticmethod
    def get_session(db: Session, session_id: str) -> Optional[ChatSession]:
        return db.query(ChatSession).filter(ChatSession.session_id == session_id).first()

    @staticmethod
    def save_session(db: Session, session_id: str, history: List[Dict[str, Any]], farmer_id: Optional[int] = None) -> ChatSession:
        try:
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            history_str = json.dumps(history)
            if session:
                session.chat_history = history_str
                if farmer_id:
                    session.farmer_id = farmer_id
            else:
                session = ChatSession(session_id=session_id, farmer_id=farmer_id, chat_history=history_str)
                db.add(session)
            db.commit()
            db.refresh(session)
            return session
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving chat session {session_id}: {e}")
            raise DatabaseException("Failed to save session", {"error": str(e)})

class CacheRepository:
    @staticmethod
    def get(db: Session, key: str) -> Optional[Dict[str, Any]]:
        entry = db.query(CacheEntry).filter(CacheEntry.cache_key == key).first()
        if entry:
            if entry.expires_at > datetime.utcnow():
                return json.loads(entry.value)
            else:
                db.delete(entry)
                db.commit()
        return None

    @staticmethod
    def set(db: Session, key: str, value: Dict[str, Any], ttl_seconds: int = 3600):
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            entry = db.query(CacheEntry).filter(CacheEntry.cache_key == key).first()
            val_str = json.dumps(value)
            if entry:
                entry.value = val_str
                entry.expires_at = expires_at
            else:
                entry = CacheEntry(cache_key=key, value=val_str, expires_at=expires_at)
                db.add(entry)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error setting cache entry {key}: {e}")
            raise DatabaseException("Failed to set cache entry", {"error": str(e)})

class RecommendationLogRepository:
    @staticmethod
    def log(db: Session, session_id: str, topic: str, query: str, trace: Dict[str, Any], recommendation: str, farmer_id: Optional[int] = None):
        try:
            log_str = json.dumps(trace)
            entry = RecommendationLog(
                session_id=session_id,
                farmer_id=farmer_id,
                topic=topic,
                input_query=query,
                consultation_log=log_str,
                final_recommendation=recommendation
            )
            db.add(entry)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error logging recommendation: {e}")
            raise DatabaseException("Failed to log recommendation", {"error": str(e)})
            
    @staticmethod
    def get_logs_by_farmer(db: Session, farmer_id: int) -> List[RecommendationLog]:
        return db.query(RecommendationLog).filter(RecommendationLog.farmer_id == farmer_id).order_by(RecommendationLog.created_at.desc()).all()
