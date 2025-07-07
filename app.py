import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, stream_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import json
import threading
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "local-rag-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///rag.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# File upload configuration
UPLOAD_FOLDER = 'uploads'
EMBEDDINGS_FOLDER = 'embeddings'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EMBEDDINGS_FOLDER'] = EMBEDDINGS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EMBEDDINGS_FOLDER, exist_ok=True)

# Initialize the app with the extension
db.init_app(app)

# Import models and RAG engine
from models import Document, ChatSession, ChatMessage
from rag_engine import RAGEngine

# Initialize RAG engine
rag_engine = RAGEngine()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page showing uploaded documents and chat interface."""
    documents = Document.query.all()
    return render_template('index.html', documents=documents)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file upload and processing."""
    if 'files' not in request.files:
        flash('No files selected', 'error')
        return redirect(url_for('index'))
    
    files = request.files.getlist('files')
    if not files or all(file.filename == '' for file in files):
        flash('No files selected', 'error')
        return redirect(url_for('index'))
    
    uploaded_count = 0
    error_count = 0
    
    for file in files:
        if file.filename == '':
            continue
            
        if file and allowed_file(file.filename):
            try:
                # Generate unique filename
                filename = secure_filename(file.filename)
                unique_id = str(uuid.uuid4())
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
                
                # Save file
                file.save(file_path)
                
                # Create document record
                document = Document(
                    id=unique_id,
                    filename=filename,
                    original_filename=file.filename,
                    file_path=file_path,
                    upload_date=datetime.utcnow(),
                    status='uploaded'
                )
                db.session.add(document)
                db.session.commit()
                
                # Start processing in background
                threading.Thread(target=process_document_async, args=(unique_id,)).start()
                
                uploaded_count += 1
                
            except Exception as e:
                logger.error(f"Error uploading file {file.filename}: {str(e)}")
                error_count += 1
        else:
            logger.warning(f"Invalid file type: {file.filename}")
            error_count += 1
    
    if uploaded_count > 0:
        flash(f'{uploaded_count} file(s) uploaded successfully! Processing in background...', 'success')
    
    if error_count > 0:
        flash(f'{error_count} file(s) failed to upload. Please check file types and sizes.', 'warning')
    
    return redirect(url_for('index'))

def process_document_async(document_id):
    """Process document in background thread."""
    with app.app_context():
        try:
            document = Document.query.get(document_id)
            if not document:
                return
            
            # Update status
            document.status = 'processing'
            db.session.commit()
            
            # Process with RAG engine
            result = rag_engine.process_document(document.file_path, document_id)
            
            if result['success']:
                document.status = 'ready'
                document.page_count = result['page_count']
                document.chunk_count = result['chunk_count']
                document.embedding_path = result['embedding_path']
            else:
                document.status = 'error'
                document.error_message = result['error']
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            document = Document.query.get(document_id)
            if document:
                document.status = 'error'
                document.error_message = str(e)
                db.session.commit()

@app.route('/chat/<document_id>')
def chat_interface(document_id):
    """Chat interface for a specific document."""
    document = Document.query.get_or_404(document_id)
    if document.status != 'ready':
        flash('Document is not ready for chat yet.', 'warning')
        return redirect(url_for('index'))
    
    # Get or create chat session
    chat_session = ChatSession.query.filter_by(document_id=document_id).first()
    if not chat_session:
        chat_session = ChatSession(
            id=str(uuid.uuid4()),
            document_id=document_id,
            created_at=datetime.utcnow()
        )
        db.session.add(chat_session)
        db.session.commit()
    
    # Get chat messages
    messages = ChatMessage.query.filter_by(session_id=chat_session.id).order_by(ChatMessage.timestamp).all()
    
    return render_template('chat.html', document=document, chat_session=chat_session, messages=messages)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat messages."""
    data = request.get_json()
    question = data.get('question', '').strip()
    document_id = data.get('document_id')
    session_id = data.get('session_id')
    
    if not question or not document_id or not session_id:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Verify document and session exist
        document = Document.query.get(document_id)
        chat_session = ChatSession.query.get(session_id)
        
        if not document or not chat_session:
            return jsonify({'error': 'Document or session not found'}), 404
        
        if document.status != 'ready':
            return jsonify({'error': 'Document not ready for chat'}), 400
        
        # Save user message
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            message=question,
            is_user=True,
            timestamp=datetime.utcnow()
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Generate response using RAG
        response_data = rag_engine.generate_response(question, document_id)
        
        if response_data['success']:
            # Save assistant message
            assistant_message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                message=response_data['response'],
                is_user=False,
                timestamp=datetime.utcnow(),
                sources=json.dumps(response_data.get('sources', []))
            )
            db.session.add(assistant_message)
            db.session.commit()
            
            return jsonify({
                'response': response_data['response'],
                'sources': response_data.get('sources', []),
                'user_message_id': user_message.id,
                'assistant_message_id': assistant_message.id
            })
        else:
            return jsonify({'error': response_data['error']}), 500
            
    except Exception as e:
        logger.error(f"Error in chat API: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/document/<document_id>/status')
def api_document_status(document_id):
    """Get document processing status."""
    document = Document.query.get_or_404(document_id)
    return jsonify({
        'status': document.status,
        'page_count': document.page_count,
        'chunk_count': document.chunk_count,
        'error_message': document.error_message
    })

@app.route('/delete_document/<document_id>', methods=['POST'])
def delete_document(document_id):
    """Delete a document and its associated data."""
    try:
        document = Document.query.get_or_404(document_id)
        
        # Delete chat sessions and messages
        chat_sessions = ChatSession.query.filter_by(document_id=document_id).all()
        for session in chat_sessions:
            ChatMessage.query.filter_by(session_id=session.id).delete()
            db.session.delete(session)
        
        # Delete files
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        if document.embedding_path and os.path.exists(document.embedding_path):
            os.remove(document.embedding_path)
        
        # Delete document record
        db.session.delete(document)
        db.session.commit()
        
        flash('Document deleted successfully!', 'success')
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        flash(f'Error deleting document: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/api/models/status')
def api_models_status():
    """Get status of loaded models."""
    return jsonify(rag_engine.get_models_status())

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
