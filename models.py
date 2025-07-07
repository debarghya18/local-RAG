from app import db
from datetime import datetime
from sqlalchemy import Text

class Document(db.Model):
    """Model for uploaded PDF documents."""
    id = db.Column(db.String(36), primary_key=True)  # UUID
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='uploaded')  # uploaded, processing, ready, error
    page_count = db.Column(db.Integer)
    chunk_count = db.Column(db.Integer)
    embedding_path = db.Column(db.String(500))
    error_message = db.Column(Text)
    
    # Relationship with chat sessions
    chat_sessions = db.relationship('ChatSession', backref='document', lazy=True, cascade='all, delete-orphan')

class ChatSession(db.Model):
    """Model for chat sessions with documents."""
    id = db.Column(db.String(36), primary_key=True)  # UUID
    document_id = db.Column(db.String(36), db.ForeignKey('document.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with chat messages
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade='all, delete-orphan')

class ChatMessage(db.Model):
    """Model for individual chat messages."""
    id = db.Column(db.String(36), primary_key=True)  # UUID
    session_id = db.Column(db.String(36), db.ForeignKey('chat_session.id'), nullable=False)
    message = db.Column(Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)  # True for user messages, False for assistant
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sources = db.Column(Text)  # JSON string of source chunks
