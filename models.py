from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    dream_entries = relationship('DreamEntry', back_populates='user', cascade="all, delete-orphan")

class DreamEntry(Base):
    __tablename__ = 'dream_entries'
    
    dream_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    dream_text = Column(Text, nullable=False)
    mood_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship('User', back_populates='dream_entries')

# Add this line to allow both Dream and DreamEntry to work
Dream = DreamEntry

# Database setup
engine = create_engine('sqlite:///dream_journal.db', echo=True)
Base.metadata.create_all(engine)

# Create a session factory
db_session = scoped_session(sessionmaker(bind=engine))