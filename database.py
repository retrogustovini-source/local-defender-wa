from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Configurazione database PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class UserSession(Base):
    """Gestione sessioni utenti WhatsApp"""
    __tablename__ = 'user_sessions'
    
    phone_number = Column(String, primary_key=True)  # Formato: 420737895525 (senza prefisso whatsapp:)
    language = Column(String, default=None)  # it, en, cs
    last_interaction = Column(DateTime, default=datetime.utcnow)

class BotConfig(Base):
    """Configurazione globale del bot"""
    __tablename__ = 'bot_config'
    
    id = Column(String, primary_key=True)
    is_active = Column(Boolean, default=True)
    restaurant_admin = Column(String)  # Formato: 420123456789 (numero admin senza prefisso)

class RestaurantInfo(Base):
    """Informazioni ristorante (per multi-ristorante futuro)"""
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
            # Numero admin di default (modificabile poi)
            admin_phone = os.getenv('ADMIN_PHONE', '420737895525')  # Il tuo numero
            config = BotConfig(
                id='main',
                is_active=True,
                restaurant_admin=admin_phone
            )
            db.add(config)
            db.commit()
            print(f"✅ Database inizializzato. Admin phone: {admin_phone}")
    except Exception as e:
        print(f"⚠️ Errore init_db: {e}")
    finally:
        db.close()

def get_user_language(phone_number):
    """Ottieni la lingua dell'utente dal database"""
    db = SessionLocal()
    try:
        user = db.query(UserSession).filter_by(phone_number=phone_number).first()
        if user:
            # Aggiorna timestamp ultima interazione
            user.last_interaction = datetime.utcnow()
            db.commit()
            return user.language
        return None
    except Exception as e:
        print(f"⚠️ Errore get_user_language: {e}")
        return None
    finally:
        db.close()

def set_user_language(phone_number, language):
    """Salva la lingua scelta dall'utente"""
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
        print(f"✅ Lingua salvata per {phone_number}: {language}")
    except Exception as e:
        print(f"⚠️ Errore set_user_language: {e}")
    finally:
        db.close()

def reset_user_session(phone_number):
    """Reset sessione utente (per cambio lingua)"""
    db = SessionLocal()
    try:
        user = db.query(UserSession).filter_by(phone_number=phone_number).first()
        if user:
            user.language = None
            user.last_interaction = datetime.utcnow()
            db.commit()
            print(f"✅ Sessione reset per {phone_number}")
    except Exception as e:
        print(f"⚠️ Errore reset_user_session: {e}")
    finally:
        db.close()

def is_bot_active():
    """Controlla se il bot è attivo"""
    db = SessionLocal()
    try:
        config = db.query(BotConfig).filter_by(id='main').first()
        return config.is_active if config else True
    except Exception as e:
        print(f"⚠️ Errore is_bot_active: {e}")
        return True  # Default attivo in caso di errore
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
            status = "ACCESO ✅" if active else "SPENTO 🔴"
            print(f"✅ Bot status cambiato: {status}")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Errore set_bot_status: {e}")
        return False
    finally:
        db.close()

def get_admin_phone():
    """Ottieni il numero dell'admin"""
    db = SessionLocal()
    try:
        config = db.query(BotConfig).filter_by(id='main').first()
        return config.restaurant_admin if config else None
    except Exception as e:
        print(f"⚠️ Errore get_admin_phone: {e}")
        return None
    finally:
        db.close()

def set_admin_phone(phone_number):
    """Imposta numero admin (per cambiare admin)"""
    db = SessionLocal()
    try:
        config = db.query(BotConfig).filter_by(id='main').first()
        if config:
            config.restaurant_admin = phone_number
            db.commit()
            print(f"✅ Admin phone aggiornato: {phone_number}")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Errore set_admin_phone: {e}")
        return False
    finally:
        db.close()
