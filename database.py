from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    phone_number = Column(String, primary_key=True)
    language = Column(String, default=None)
    last_interaction = Column(DateTime, default=datetime.utcnow)

class BotConfig(Base):
    __tablename__ = 'bot_config'
    
    id = Column(String, primary_key=True)
    is_active = Column(Boolean, default=True)
    restaurant_admin = Column(String)

class RestaurantInfo(Base):
    __tablename__ = 'restaurant_info'
    
    restaurant_id = Column(String, primary_key=True, default='default')
    name = Column(String)
    phone = Column(String)
    address = Column(String)
    google_maps_link = Column(String)
    hours_it = Column(String)
    hours_en = Column(String)
    hours_cs = Column(String)
    menu_it = Column(String)
    menu_en = Column(String)
    menu_cs = Column(String)

def init_db():
    """Crea le tabelle nel database"""
    Base.metadata.create_all(bind=engine)
    
    # Inizializza configurazione bot se non esiste
    db = SessionLocal()
    try:
        config = db.query(BotConfig).filter_by(id='main').first()
        if not config:
            config = BotConfig(
                id='main',
                is_active=True,
                restaurant_admin=os.getenv('ADMIN_PHONE', 'whatsapp:+420123456789')
            )
            db.add(config)
            db.commit()
    finally:
        db.close()

def get_user_language(phone_number):
    """Ottieni la lingua dell'utente"""
    db = SessionLocal()
    try:
        user = db.query(UserSession).filter_by(phone_number=phone_number).first()
        if user:
            user.last_interaction = datetime.utcnow()
            db.commit()
            return user.language
        return None
    finally:
        db.close()

def set_user_language(phone_number, language):
    """Salva la lingua dell'utente"""
    db = SessionLocal()
    try:
        user = db.query(UserSession).filter_by(phone_number=phone_number).first()
        if user:
            user.language = language
            user.last_interaction = datetime.utcnow()
        else:
            user = UserSession(
                phone_number=phone_number,
                language=language,
                last_interaction=datetime.utcnow()
            )
            db.add(user)
        db.commit()
    finally:
        db.close()

def reset_user_session(phone_number):
    """Reset sessione utente (per cambio lingua)"""
    db = SessionLocal()
    try:
        user = db.query(UserSession).filter_by(phone_number=phone_number).first()
        if user:
            user.language = None
            db.commit()
    finally:
        db.close()

def is_bot_active():
    """Controlla se il bot è attivo"""
    db = SessionLocal()
    try:
        config = db.query(BotConfig).filter_by(id='main').first()
        return config.is_active if config else True
    finally:
        db.close()

def set_bot_status(active):
    """Imposta lo stato del bot (ON/OFF)"""
    db = SessionLocal()
    try:
        config = db.query(BotConfig).filter_by(id='main').first()
        if config:
            config.is_active = active
            db.commit()
            return True
        return False
    finally:
        db.close()

def get_admin_phone():
    """Ottieni il numero admin"""
    db = SessionLocal()
    try:
        config = db.query(BotConfig).filter_by(id='main').first()
        return config.restaurant_admin if config else None
    finally:
        db.close()