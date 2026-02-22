from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, JSON, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.engine import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    location = Column(String)
    start_date_time = Column(DateTime)
    end_date_time = Column(DateTime)
    max_seats = Column(Integer)
    status = Column(String, default="draft")
    limit_one_response = Column(Boolean, default=False)
    whatsapp_link = Column(String)
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    fields = relationship("EventField", back_populates="event", cascade="all, delete-orphan")

class EventField(Base):
    __tablename__ = "event_fields"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    order_index = Column(Integer)
    label = Column(String)
    type = Column(String)
    required = Column(Boolean)
    description = Column(Text)  # Help text
    min_value = Column(Integer)  # For scales/limits
    max_value = Column(Integer)  # For scales/limits
    file_types = Column(ARRAY(String))  # Allowed extensions
    max_file_size = Column(Integer)  # Max size in bytes
    options = Column(JSON)  # Options for choice questions
    image_url = Column(String)  # For organizer's question image/QR code
    logic = Column(JSON)  # For conditional logic (e.g., {"Option A": "section_id"})
    
    event = relationship("Event", back_populates="fields")

class Registration(Base):
    __tablename__ = "registrations"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    answers = Column(JSON)
    verified = Column(Boolean, default=False)
    payment_status = Column(String, default="pending")  # pending, paid, failed

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
